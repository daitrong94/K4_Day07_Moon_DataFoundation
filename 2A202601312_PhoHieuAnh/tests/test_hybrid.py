"""Tests cho hybrid retrieval (BM25 + dense, hợp nhất bằng RRF).

File riêng của sinh viên — KHÔNG đụng tests/test_solution.py của lab.
"""
import unittest

from src import Document, EmbeddingStore, _mock_embed
from src.hybrid import BM25Index, HybridStore, reciprocal_rank_fusion, tokenize


class TestTokenize(unittest.TestCase):
    def test_lowercases_and_splits_on_punctuation(self):
        self.assertEqual(tokenize("Chính sách, đổi trả!"), ["chính", "sách", "đổi", "trả"])

    def test_keeps_grouped_numbers_intact(self):
        # "50.000.000" phải là MỘT token — đây chính là tín hiệu mà dense embedding bỏ lỡ.
        self.assertIn("50.000.000", tokenize("Đơn hàng vượt quá 50.000.000 VNĐ"))

    def test_keeps_hotline_intact(self):
        self.assertIn("1800.2097", tokenize("gọi tổng đài 1800.2097 để hủy"))

    def test_keeps_unit_suffix_attached(self):
        self.assertIn("10km", tokenize("bán kính 10km"))


class TestBM25Index(unittest.TestCase):
    DOCS = [
        ("a", "Đơn hàng có giá trị vượt quá 50.000.000 VNĐ không được hỗ trợ vận chuyển"),
        ("b", "Chính sách đổi trả áp dụng trong vòng 30 ngày kể từ ngày mua"),
        ("c", "Người bán phải đóng gói đúng quy cách trước khi giao cho đơn vị vận chuyển"),
    ]

    def _index(self) -> BM25Index:
        return BM25Index([(doc_id, text) for doc_id, text in self.DOCS])

    def test_ranks_document_with_rare_query_term_first(self):
        ranked = self._index().search("50.000.000", top_k=3)
        self.assertEqual(ranked[0][0], "a")

    def test_returns_at_most_top_k(self):
        self.assertLessEqual(len(self._index().search("vận chuyển", top_k=2)), 2)

    def test_scores_are_sorted_descending(self):
        scores = [score for _, score in self._index().search("vận chuyển đơn hàng", top_k=3)]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_unknown_term_returns_no_positive_match(self):
        self.assertEqual(self._index().search("xyzzy", top_k=3), [])

    def test_common_term_scores_lower_than_rare_term(self):
        index = self._index()
        rare = dict(index.search("50.000.000", top_k=3))["a"]
        common = dict(index.search("vận chuyển", top_k=3))["a"]
        self.assertGreater(rare, common)


class TestReciprocalRankFusion(unittest.TestCase):
    def test_document_ranked_first_in_both_lists_wins(self):
        fused = reciprocal_rank_fusion([["x", "y"], ["x", "z"]])
        self.assertEqual(fused[0][0], "x")

    def test_document_present_in_one_list_only_still_appears(self):
        self.assertIn("z", dict(reciprocal_rank_fusion([["x", "y"], ["x", "z"]])))

    def test_agreement_beats_a_single_top_rank(self):
        # "b" đứng hạng 2 ở CẢ HAI danh sách phải thắng "a" chỉ đứng hạng 1 ở một danh sách.
        fused = dict(reciprocal_rank_fusion([["a", "b"], ["c", "b"]]))
        self.assertGreater(fused["b"], fused["a"])

    def test_empty_input_returns_empty(self):
        self.assertEqual(reciprocal_rank_fusion([]), [])


class TestWeightedFusion(unittest.TestCase):
    def test_weights_can_override_a_higher_rank(self):
        # "b" chỉ đứng hạng 2 ở danh sách thứ nhất, nhưng danh sách đó nặng gấp 4 lần.
        fused = dict(reciprocal_rank_fusion([["a", "b"], ["c", "d"]], weights=[4.0, 1.0]))
        self.assertGreater(fused["b"], fused["c"])

    def test_zero_weight_removes_a_list_entirely(self):
        fused = dict(reciprocal_rank_fusion([["a"], ["b"]], weights=[1.0, 0.0]))
        self.assertEqual(fused.get("b", 0.0), 0.0)

    def test_default_weights_are_equal(self):
        fused = dict(reciprocal_rank_fusion([["a"], ["b"]]))
        self.assertAlmostEqual(fused["a"], fused["b"])


class TestQueryIdfGate(unittest.TestCase):
    """BM25 chỉ nên tham gia khi truy vấn có token đủ hiếm để mang thông tin."""

    DOCS = [(f"d{i}", "chính sách đổi trả áp dụng cho khách hàng") for i in range(20)]

    def test_common_only_query_has_low_idf(self):
        index = BM25Index(self.DOCS)
        self.assertLess(index.max_query_idf("chính sách đổi trả"), 1.0)

    def test_rare_token_query_has_high_idf(self):
        docs = self.DOCS + [("rare", "phí nhập lại 50.000.000 đồng")]
        self.assertGreater(BM25Index(docs).max_query_idf("50.000.000"), 2.0)

    def test_unknown_token_gives_zero(self):
        self.assertEqual(BM25Index(self.DOCS).max_query_idf("xyzzy"), 0.0)

    def test_rare_number_opens_the_gate(self):
        docs = self.DOCS + [("rare", "đơn hàng vượt quá 50.000.000 đồng")]
        self.assertTrue(BM25Index(docs).has_discriminative_term("giới hạn 50.000.000 là bao nhiêu"))

    def test_rare_function_word_does_not_open_the_gate(self):
        """'sang' trong 'đổi sang máy khác' hiếm trong corpus nhưng vô nghĩa khi
        truy xuất — tách âm tiết tiếng Việt khiến hư từ trông như từ hiếm."""
        docs = self.DOCS + [("odd", "khách đổi sang mẫu khác")]
        self.assertFalse(BM25Index(docs).has_discriminative_term("đổi sang máy khác"))

    def test_query_with_no_terms_at_all_does_not_open_the_gate(self):
        self.assertFalse(BM25Index(self.DOCS).has_discriminative_term("!!!"))


class TestHybridStore(unittest.TestCase):
    def _store(self) -> HybridStore:
        dense = EmbeddingStore(collection_name="hybrid_test", embedding_fn=_mock_embed)
        store = HybridStore(dense)
        store.add_documents([
            Document("d1", "Đơn hàng vượt quá 50.000.000 VNĐ không được hỗ trợ vận chuyển", {}),
            Document("d2", "Chính sách đổi trả trong vòng 30 ngày", {}),
            Document("d3", "Quy định đóng gói hàng dễ vỡ", {}),
        ])
        return store

    def test_results_have_same_shape_as_embedding_store(self):
        for result in self._store().search("50.000.000", top_k=3):
            self.assertIn("content", result)
            self.assertIn("score", result)
            self.assertIn("metadata", result)

    def test_results_sorted_by_score_descending(self):
        scores = [r["score"] for r in self._store().search("vận chuyển", top_k=3)]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_exact_number_match_ranks_first(self):
        # Mock embedding sinh vector gần như ngẫu nhiên nên dense KHÔNG thể tìm ra d1;
        # nhánh BM25 mới là thứ phải kéo nó lên hạng 1.
        self.assertEqual(self._store().search("50.000.000", top_k=3)[0]["id"], "d1")

    def test_respects_top_k(self):
        self.assertLessEqual(len(self._store().search("hàng", top_k=2)), 2)

    def test_query_without_rare_token_falls_back_to_pure_dense(self):
        """Truy vấn toàn âm tiết phổ thông: BM25 chỉ là nhiễu nên phải bị tắt."""
        store = self._store()
        dense_only = store.dense.search("chính sách hàng", top_k=3)
        hybrid = store.search("chính sách hàng", top_k=3)
        self.assertEqual([r["id"] for r in hybrid], [r["id"] for r in dense_only])

    def test_metadata_filter_is_applied(self):
        dense = EmbeddingStore(collection_name="hybrid_filter", embedding_fn=_mock_embed)
        store = HybridStore(dense)
        store.add_documents([
            Document("s1", "Quy định dành cho người bán", {"customer_role": "seller"}),
            Document("b1", "Hướng dẫn dành cho người mua", {"customer_role": "buyer"}),
        ])
        results = store.search_with_filter("quy định", top_k=5, metadata_filter={"customer_role": "seller"})
        self.assertTrue(all(r["metadata"]["customer_role"] == "seller" for r in results))


if __name__ == "__main__":
    unittest.main()
