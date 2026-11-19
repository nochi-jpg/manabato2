"""assets2.js（まなびバトル2 の 画像の 差しかえ表）を 作る。
- 旧作の アイテム画像 images/item/iNN.png（0から）は、まなびバトル2 の item2 フォルダ・1からに 置きかえる
  （アイテムの 表 だけでなく、UIの 絵文字に つかっている ところも）
- 新しい アイテム（102〜131）は、素材リポジトリに 画像が あるものだけ 書く（ないものは 絵文字のまま）
使い方：python3 tools/make_assets2.py（素材リポジトリは となりのフォルダ ../manabi-battle-assets）
"""
import json, pathlib, subprocess
ROOT = pathlib.Path(__file__).resolve().parent.parent
IMG = ROOT.parent / 'manabi-battle-assets' / 'images' / 'item2'
names = json.loads(subprocess.run(['node', '-e', "global.window={};require('./data.js');console.log(JSON.stringify(window.DATA.ITEMS.map(i=>i.n)))"], cwd=ROOT, capture_output=True, text=True, check=True).stdout)
have = {i: f'images/item2/i{i:03d}.png' for i in range(1, len(names) + 1) if (IMG / f'i{i:03d}.png').exists()}
items = {names[i - 1]: p for i, p in have.items()}
miss = [f'{i} {names[i - 1]}' for i in range(1, len(names) + 1) if i not in have]
js = f"""// ===== まなびバトル2：画像の 差しかえ表（tools/make_assets2.py で 作る。手で直さない）=====
// assets.local.js（旧作の 素材）の あとに 読む。画像が なければ 絵文字に もどる
// 画像が まだ ない アイテム：{'、'.join(miss) or 'なし'}
(function (A) {{
  // 旧作の アイテム画像（item フォルダ・0から）→ item2 フォルダ・1から。UIの 絵文字に つかっている ところも
  const re = /^images\\/item\\/i(\\d+)\\.png$/;
  const w = o => {{ for (const k in o) {{ const v = o[k]; if (typeof v === 'string') {{ const m = v.match(re); if (m) o[k] = 'images/item2/i' + String(+m[1] + 1).padStart(3, '0') + '.png'; }} else if (v && typeof v === 'object') w(v); }} }};
  w(A);
  A.item = Object.assign(A.item || {{}}, {json.dumps(items, ensure_ascii=False, indent=2)});
}})(window.ASSETS);
"""
(ROOT / 'assets2.js').write_text(js, encoding='utf8')
print(len(have), '枚', '画像なし:', miss)
