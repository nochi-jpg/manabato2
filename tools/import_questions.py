"""manabi-resource（となりのフォルダ）の 問題DB から questions.js を 作る。

- 番号（1〜）は tools/qids.json の じゅん。新しい問題は うしろに 足すだけなので、番号は かわらない
  （リソースで 問題が 消えたら、その番号は 空き番号のまま のこす）
- せいかつA → 社会、せいかつB → 理科
- 漢字モード（その学年までに 習う 漢字だけ）を つかう
使い方：python3 tools/import_questions.py
"""
import json, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
RES = ROOT.parent / 'manabi-resource' / 'dist' / 'questions.json'
IDS = ROOT / 'tools' / 'qids.json'
SUBJ = {'国語': '国語', '算数': '算数', '理科': '理科', '社会': '社会', '英語': '英語', 'せいかつA': '社会', 'せいかつB': '理科'}
db = json.loads(RES.read_text(encoding='utf8'))
qs = {q['id']: q for q in db['questions']}
ids = json.loads(IDS.read_text(encoding='utf8')) if IDS.exists() else []
known = set(ids)
ids += [q['id'] for q in db['questions'] if q['id'] not in known]
IDS.write_text(json.dumps(ids, ensure_ascii=False, indent=0) + '\n', encoding='utf8')
rows = []
for n, rid in enumerate(ids, 1):
    q = qs.get(rid)
    if not q: continue
    rows.append([n, SUBJ[q['subject']], q['grade'], q['q'], q['choices'], q['exp']])
out = ['// ===== 問題DB（まなびバトル2）：tools/import_questions.py で manabi-resource から作る。手で直さない =====',
       '// 形式： [番号, 教科, 学年, 問題文, [正解, ハズレ1, ハズレ2, ハズレ3], 解説]　番号は tools/qids.json の じゅん（かわらない）',
       f'window.QDB_VERSION = 1;', f'window.QDB_MAXID = {len(ids)};', f'window.QDB_SRC = {json.dumps(db.get("version", ""), ensure_ascii=False)};',
       'window.QUESTION_DB = [']
out += [json.dumps(r, ensure_ascii=False, separators=(',', ':')) + ',' for r in rows]
out.append('];')
(ROOT / 'questions.js').write_text('\n'.join(out) + '\n', encoding='utf8')
from collections import Counter
print(len(rows), '問', sorted(Counter((r[1], r[2]) for r in rows).items()))
