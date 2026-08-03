"""Hybrid retrieval: BM25 (từ vựng) + dense (ngữ nghĩa), hợp nhất bằng RRF.

Lý do cần: thí nghiệm cosine ở REPORT_CANHAN cho thấy embedding đo *cách viết*
chứ không đo *giá trị số hay chiều so sánh* — "dưới 10km" vs "xa hơn 10km" đạt
cosine 0.8622. Hệ quả là dense retrieval không phân biệt được điều kiện ngược
nhau, và benchmark Q3 trả về đúng tài liệu nhưng sai mệnh đề.

BM25 sửa đúng chỗ đó: nó chấm điểm theo token hiếm, nên "50.000.000", "1800.2097"
hay "10km" trở thành tín hiệu mạnh thay vì bị hòa tan vào vector 1024 chiều.

Hai thang điểm không cộng trực tiếp được (BM25 không chặn trên, cosine trong
[-1,1]), nên hợp nhất bằng **Reciprocal Rank Fusion** — chỉ dùng THỨ HẠNG:

    RRF(d) = Σ 1 / (k + rank_i(d))

Toàn bộ bằng thư viện chuẩn, không thêm dependency nào cho lab.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any

from .chunking import _dot
from .models import Document
from .store import EmbeddingStore

# Giữ nguyên cụm số có dấu phân cách ("50.000.000", "1800.2097") và hậu tố đơn vị
# dính liền ("10km") — đó chính là các token mà dense retrieval bỏ lỡ.
TOKEN = re.compile(r"[0-9]+(?:[.,][0-9]+)*[a-zà-ỹ]*|[a-zà-ỹ]+", re.IGNORECASE)

BM25_K1 = 1.5
BM25_B = 0.75
RRF_K = 60
# Chỉ dùng BM25 khi truy vấn có token xuất hiện ở <= 5% số chunk (sàn 1 chunk).
DISCRIMINATIVE_DF_RATIO = 0.05
BM25_WEIGHT = 1.0


def tokenize(text: str) -> list[str]:
    """Tách text thành token thường hóa, giữ nguyên cụm số."""
    return TOKEN.findall(text.lower())


class BM25Index:
    """BM25 Okapi trên một tập tài liệu nhỏ (đủ cho quy mô lab)."""

    def __init__(self, documents: list[tuple[str, str]], k1: float = BM25_K1, b: float = BM25_B) -> None:
        self.k1 = k1
        self.b = b
        self.doc_ids = [doc_id for doc_id, _ in documents]
        self.term_counts = [Counter(tokenize(text)) for _, text in documents]
        self.lengths = [sum(counts.values()) for counts in self.term_counts]
        self.average_length = (sum(self.lengths) / len(self.lengths)) if self.lengths else 0.0

        document_frequency: Counter = Counter()
        for counts in self.term_counts:
            document_frequency.update(counts.keys())

        self.document_frequency = document_frequency
        total = len(documents)
        self.idf = {
            term: math.log(1 + (total - frequency + 0.5) / (frequency + 0.5))
            for term, frequency in document_frequency.items()
        }

    def search(self, query: str, top_k: int = 10) -> list[tuple[str, float]]:
        """Trả về [(doc_id, score)] giảm dần; bỏ các tài liệu không khớp token nào."""
        terms = tokenize(query)
        if not terms or not self.doc_ids:
            return []

        scored: list[tuple[str, float]] = []
        for index, counts in enumerate(self.term_counts):
            length = self.lengths[index] or 1
            score = 0.0
            for term in terms:
                frequency = counts.get(term, 0)
                if not frequency:
                    continue
                denominator = frequency + self.k1 * (1 - self.b + self.b * length / (self.average_length or 1))
                score += self.idf.get(term, 0.0) * frequency * (self.k1 + 1) / denominator
            if score > 0:
                scored.append((self.doc_ids[index], score))

        scored.sort(key=lambda pair: pair[1], reverse=True)
        return scored[:top_k]

    def max_query_idf(self, query: str) -> float:
        """IDF cao nhất trong các token của truy vấn — thước đo 'truy vấn này có
        chứa từ hiếm nào không'. Bằng 0 nếu không token nào có trong index."""
        return max((self.idf.get(term, 0.0) for term in tokenize(query)), default=0.0)

    def has_discriminative_term(self, query: str, ratio: float = 0.05) -> bool:
        """Truy vấn có chứa token định danh/số vừa hiếm không?

        Hai điều kiện, cả hai đều rút ra từ đo đạc chứ không phải phỏng đoán:

        1. **Hiếm trong corpus** — dùng tần suất tài liệu thay vì ngưỡng IDF
           tuyệt đối, vì IDF phụ thuộc kích thước corpus (3 tài liệu: IDF tối đa
           ~0.98; 279 chunk: token xuất hiện 1 lần đạt ~5.2), nên ngưỡng IDF cố
           định sẽ chặn nhầm ở corpus nhỏ. Tỉ lệ thì bất biến quy mô.

        2. **Có chứa chữ số** — tiếng Việt tách theo âm tiết nên hư từ dễ trông
           như từ hiếm: trong corpus 279 chunk, "sang" (ở "đổi *sang* máy khác")
           chỉ có df=5, lọt mọi ngưỡng hiếm, rồi kéo BM25 chấm điểm theo một âm
           tiết vô nghĩa và làm Hit@3 tụt 1.00 -> 0.80. Ngược lại các token dense
           thật sự mù đều là số: "10km", "50.000.000", "15%", "1800.2097".
           Muốn khớp từ vựng cho danh từ riêng tiếng Việt thì phải tách từ
           (underthesea/VnCoreNLP) — ngoài phạm vi lab này.
        """
        if not self.doc_ids:
            return False
        limit = max(1, int(ratio * len(self.doc_ids)))
        return any(
            any(character.isdigit() for character in term)
            and 0 < self.document_frequency.get(term, 0) <= limit
            for term in tokenize(query)
        )


def reciprocal_rank_fusion(
    rankings: list[list[str]], k: int = RRF_K, weights: list[float] | None = None
) -> list[tuple[str, float]]:
    """Hợp nhất nhiều danh sách đã xếp hạng thành một, chỉ dựa trên thứ hạng.

    Dùng RRF thay vì cộng điểm vì BM25 không chặn trên còn cosine nằm trong
    [-1, 1] — cộng thẳng sẽ để BM25 lấn át hoàn toàn.

    `weights` cho phép hạ ảnh hưởng của một nhánh; mặc định các nhánh ngang nhau.
    """
    if weights is None:
        weights = [1.0] * len(rankings)

    fused: dict[str, float] = {}
    for ranking, weight in zip(rankings, weights):
        if not weight:
            continue
        for rank, key in enumerate(ranking, start=1):
            fused[key] = fused.get(key, 0.0) + weight / (k + rank)
    return sorted(fused.items(), key=lambda pair: pair[1], reverse=True)


class HybridStore:
    """Bọc `EmbeddingStore`, thêm nhánh BM25 song song và hợp nhất bằng RRF.

    Giữ nguyên API của EmbeddingStore (`add_documents`, `search`,
    `search_with_filter`, `get_collection_size`, `delete_document`) nên thay
    được vào mọi chỗ đang dùng store, kể cả `KnowledgeBaseAgent`.
    """

    def __init__(
        self,
        dense_store: EmbeddingStore,
        candidates: int = 20,
        bm25_weight: float = BM25_WEIGHT,
        discriminative_ratio: float = DISCRIMINATIVE_DF_RATIO,
    ) -> None:
        self.dense = dense_store
        self.candidates = candidates
        self.bm25_weight = bm25_weight
        self.discriminative_ratio = discriminative_ratio
        self._records: list[dict[str, Any]] = []
        self._bm25: BM25Index | None = None

    def add_documents(self, docs: list[Document]) -> None:
        self.dense.add_documents(docs)
        self._records = self.dense._store
        self._rebuild_index()

    def _rebuild_index(self) -> None:
        self._bm25 = BM25Index([(str(r["index"]), r["content"]) for r in self._records])

    def get_collection_size(self) -> int:
        return self.dense.get_collection_size()

    def delete_document(self, doc_id: str) -> bool:
        removed = self.dense.delete_document(doc_id)
        self._records = self.dense._store
        self._rebuild_index()
        return removed

    def _fuse(self, query: str, candidates: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        if not candidates:
            return []

        allowed = {str(record["index"]) for record in candidates}
        by_key = {str(record["index"]): record for record in candidates}

        # Tự chấm điểm dense thay vì gọi _search_records: hàm đó bỏ khóa `index`
        # nên muốn ghép ngược lại record phải dò theo nội dung — sai ngay khi có
        # hai chunk trùng nội dung (corpus này có, vì các trang lặp điều khoản).
        query_embedding = self.dense._embedding_fn(query)
        dense_scored = sorted(
            ((str(record["index"]), _dot(query_embedding, record["embedding"])) for record in candidates),
            key=lambda pair: pair[1],
            reverse=True,
        )
        dense_ranking = [key for key, _ in dense_scored[: self.candidates]]

        # Cổng chặn: chỉ cho BM25 tham gia khi truy vấn có ít nhất một token đủ
        # hiếm. Tiếng Việt tách theo âm tiết nên câu hỏi toàn từ phổ thông
        # ("điện thoại mua mới ... bao nhiêu ngày") cho BM25 gần như ngẫu nhiên;
        # để nó vào RRF ngang quyền với dense là hạ chất lượng, đo được ở
        # benchmark Q1 (Hit@3 1.00 -> 0.80).
        bm25_ranking: list[str] = []
        if self._bm25 and self._bm25.has_discriminative_term(query, self.discriminative_ratio):
            bm25_all = self._bm25.search(query, top_k=len(self._records))
            bm25_ranking = [key for key, _ in bm25_all if key in allowed][: self.candidates]

        results: list[dict[str, Any]] = []
        fused = reciprocal_rank_fusion(
            [dense_ranking, bm25_ranking], weights=[1.0, self.bm25_weight]
        )
        for key, score in fused[:top_k]:
            record = by_key[key]
            results.append(
                {
                    "id": record["id"],
                    "content": record["content"],
                    "metadata": record["metadata"],
                    "score": score,
                }
            )
        return results

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        return self._fuse(query, self._records, top_k)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        if not metadata_filter:
            candidates = self._records
        else:
            candidates = [
                record
                for record in self._records
                if all(record["metadata"].get(key) == value for key, value in metadata_filter.items())
            ]
        return self._fuse(query, candidates, top_k)
