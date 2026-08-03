import csv
import re
from pathlib import Path

# Thư mục dữ liệu cho K4
D = Path('data/k4_ecommerce')
REQ = ['doc_id', 'title', 'source_url', 'retrieved_at', 'document_version']
mds = sorted(D.glob('*.md'))
rows = list(csv.DictReader(open(D / 'sources.csv', encoding='utf-8')))
ids, roles = [], {}
KEY = 'customer_role'

print("--- KIỂM TRA METADATA ---")
for p in mds:
    parts = p.read_text(encoding='utf-8').split('---')
    if len(parts) < 3:
        print(f'{p.name:40} THIEU FRONTMATTER')
        continue
    fm = dict(re.findall(r'^(\w+):\s*(.+)$', parts[1], re.M))
    ids.append(fm.get('doc_id'))
    
    role = fm.get(KEY)
    roles[role] = roles.get(role, 0) + 1
    
    ok = all(k in fm for k in REQ) and KEY in fm and fm.get('doc_id') == p.stem
    print(f'{p.name:40} {"OK" if ok else "THIEU METADATA / SAI DOC_ID"}')

print('\n--- KẾT QUẢ ---')
print('so file :', len(mds), '(can 5-10)')
print('csv     :', 'khop' if sorted(r['doc_id'] for r in rows) == sorted(ids) else 'LECH')
print(KEY, ':', roles)
