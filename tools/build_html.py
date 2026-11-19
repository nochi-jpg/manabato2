# 1つのHTMLにまとめた版を作る（子どもが「解凍 → index.html」をしなくていいように）
# 使い方: python3 tools/build_html.py [BGMのビットレート kbps（ふつう32）]
#         python3 tools/build_html.py --canva  → manabi-battle-canva.html（Canva の ホームページ用・10MB以内）
#           BGM 20kbps・22kHz・モノラル／フォントは ゲームで使う字だけ／背景は WebP
#   素材リポジトリは となりのフォルダ（../manabi-battle-assets）。ffmpeg が必要（BGMを軽くする）
#   画像・音・フォントは data: URI にして中に入れる。同じ画像は1回だけ入れて、読みこんだあとに パスを置きかえる
import base64, json, mimetypes, pathlib, re, subprocess, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT.parent / 'manabi-battle-assets'
CANVA = '--canva' in sys.argv
args = [a for a in sys.argv[1:] if not a.startswith('--')]
KBPS = 16 if CANVA else int(args[0]) if args else 32
OUT = ROOT / ('manabato2-canva.html' if CANVA else 'manabato2.html')
TMP = pathlib.Path(tempfile.mkdtemp())
MIME = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.gif': 'image/gif', '.webp': 'image/webp', '.svg': 'image/svg+xml', '.mp3': 'audio/mpeg', '.woff': 'font/woff', '.woff2': 'font/woff2'}

def src(rel):  # 公開リポジトリ → なければ素材リポジトリ
    for b in (ROOT, ASSETS):
        if (b / rel).exists(): return b / rel
    raise FileNotFoundError(rel)
CHARS = TMP / 'chars.txt'
if CANVA:  # フォントに入れる字：ゲームの文と問題で使う字（めずらしい漢字の名前は パソコンの字で出る）
    ch = set()
    for f in ['game.js', 'data.js', 'questions.js', 'index.html', 'savecode.js', 'assets.js']: ch |= set((ROOT / f).read_text())
    ch |= set((ASSETS / 'assets.local.css').read_text())
    ch |= {chr(c) for c in list(range(0x20, 0x7f)) + list(range(0x3040, 0x3100)) + list(range(0x30A0, 0x3100)) + list(range(0xFF01, 0xFF5F))}
    CHARS.write_text(''.join(sorted(c for c in ch if ord(c) >= 0x20 and not 0xD800 <= ord(c) < 0xE000)))
def data_uri(rel):
    p = src(rel)
    if rel.startswith('sounds/bgm/'):  # BGM は モノラル・低いビットレートに（Canva版は 16kbps。10/12：10MB に おさめるため）
        q = TMP / f'{KBPS}_{p.name}'
        if not q.exists():
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(p), '-ac', '1'] + (['-ar', '22050'] if CANVA else []) + ['-b:a', f'{KBPS}k', str(q)], check=True)
        p = q
    elif CANVA and rel.startswith('fonts/'):
        q = TMP / (p.stem + '.woff2')  # まなびバトル2：woff2（brotli。pip install brotli）で 小さく（問題が ふえて 字が ふえたため）
        if not q.exists():
            subprocess.run(['pyftsubset', str(p), f'--text-file={CHARS}', '--flavor=woff2', '--layout-features=*', f'--output-file={q}'], check=True, capture_output=True)
        p = q
    elif CANVA and p.suffix.lower() in ('.jpg', '.jpeg'):  # 背景は WebP に（同じくらいの見た目で 半分）
        from PIL import Image
        q = TMP / (p.stem + '_' + str(abs(hash(rel))) + '.webp')
        if not q.exists(): Image.open(p).convert('RGB').save(q, quality=62, method=6)  # 10/13：75→62（Canva版 10MB）
        p = q
    elif CANVA and p.suffix.lower() == '.png':  # PNG も WebP に（10/12。小さくなるときだけ）。手描きの 大きな絵は 見た目が かわらない程度に 圧縮、ドット絵などは ロスレス
        from PIL import Image
        q = TMP / (p.stem + '_' + str(abs(hash(rel))) + '.webp')
        if not q.exists():
            im = Image.open(p).convert('RGBA')
            if re.match(r'images/(boss2|zako2|player|npc/kokuusa|ui/magic|item2)', rel): im.save(q, quality=82, alpha_quality=85, method=6)
            else: im.save(q, lossless=True, method=6)
        if q.stat().st_size < p.stat().st_size: p = q
    return f'data:{MIME[p.suffix.lower()]};base64,' + base64.b64encode(p.read_bytes()).decode()
PATH = re.compile(r'(?:images|sounds|fonts)/[\w./%-]+\.(?:png|jpg|jpeg|gif|webp|svg|mp3|woff2?)')
def js(text): return text.replace('</script', '<\\/script')

html = (ROOT / 'index.html').read_text()
css_local = (ASSETS / 'assets.local.css').read_text()
local_js = (ASSETS / 'assets.local.js').read_text()
# まなびバトル2：旧作の アイテム画像（images/item/iNN.png）は 新しい 絵（images/item2/iNNN.png）に 置きかえて、assets2.js を うしろに つなぐ
local_js = re.sub(r'images/item/i(\d+)\.png', lambda m: f'images/item2/i{int(m.group(1)) + 1:03d}.png', local_js) + '\n' + (ROOT / 'assets2.js').read_text()

# CSS（index.html の中と assets.local.css）：パスを その場で data: に（フォント・UI画像。少ない）
inline = lambda t: PATH.sub(lambda m: data_uri(m.group(0)), t)
if CANVA: html = html.replace('format("woff")', 'format("woff2")')
style_parts = re.split(r'(<style>.*?</style>)', html, flags=re.S)
html = ''.join(inline(s) if s.startswith('<style>') else s for s in style_parts)
html = html.replace('<link rel="stylesheet" href="assets.local.css">', '<style>\n' + inline(css_local) + '\n</style>')
ico = data_uri('images/player/all_cute_1.png')
html = re.sub(r'(<link rel="(?:icon|apple-touch-icon)"[^>]*href=")images/player/all_cute_1\.png', lambda m: m.group(1) + ico, html)

# JS：assets.local.js の パスは 表（__EMB）にまとめて 1回だけ入れる → 読みこんだあと ASSETS の中の文字を置きかえ
def exists(p):
    try: src(p); return True
    except FileNotFoundError: return False
paths = sorted(set(PATH.findall(local_js)) | {p for p in PATH.findall((ROOT / 'assets.js').read_text()) if exists(p)})
emb = {p: data_uri(p) for p in paths}
fix = '<script>(function(){/* data: を blob: に（innerHTML に 長い文字が 入らないように＝画面の切りかえが かるくなる）。画像は 先に デコードしておく */const E=window.__EMB,K=window.__KEEP=[];for(const k in E){const v=E[k],c=v.indexOf(\',\'),t=v.slice(5,v.indexOf(\';\')),b=atob(v.slice(c+1)),u=new Uint8Array(b.length);for(let j=0;j<b.length;j++)u[j]=b.charCodeAt(j);E[k]=URL.createObjectURL(new Blob([u],{type:t}));if(t.startsWith(\'image/\')){const im=new Image();im.src=E[k];if(im.decode)im.decode().catch(()=>{});K.push(im);}}const w=o=>{for(const k in o){const v=o[k];if(typeof v==="string"&&E[v])o[k]=E[v];else if(v&&typeof v==="object")w(v);}};w(window.ASSETS||{});})();</script>'
# 問題DB（約1.1MB）は raw DEFLATE ＋ base64 で 小さくして 入れ、ひらいたときに lib/inflate.js で もとにもどす（まなびバトル2）
def qdb_script():
    import zlib
    t = (ROOT / 'questions.js').read_text(encoding='utf8')
    num = lambda k: re.search(r'window\.' + k + r' = ([^;]+);', t).group(1)
    rows = [json.loads(l.rstrip(',')) for l in t.split('\n') if l.startswith('[') and l.rstrip().endswith('],')]
    pay = json.dumps({'v': json.loads(num('QDB_VERSION')), 'max': json.loads(num('QDB_MAXID')), 'src': json.loads(num('QDB_SRC')), 'db': rows}, ensure_ascii=False, separators=(',', ':')).encode()
    c = zlib.compressobj(9, zlib.DEFLATED, -15); z = c.compress(pay) + c.flush()
    dec = ('(function(){const b=atob(window.__QZ),u=new Uint8Array(b.length);for(let i=0;i<b.length;i++)u[i]=b.charCodeAt(i);'
           'const j=JSON.parse(new TextDecoder().decode(window.MB_INFLATE(u)));window.QDB_VERSION=j.v;window.QDB_MAXID=j.max;window.QDB_SRC=j.src;window.QUESTION_DB=j.db;delete window.__QZ;})();')
    return ('<script>window.__QZ="' + base64.b64encode(z).decode() + '";</script>\n<script>' + js((ROOT / 'lib' / 'inflate.js').read_text()) + '</script>\n<script>' + dec + '</script>')
def script(m):
    name = m.group(1)
    if name == 'assets.local.js':
        return '<script>window.__EMB=' + js(json.dumps(emb, ensure_ascii=False)) + ';</script>\n<script>' + js(local_js) + '</script>\n' + fix
    if name == 'assets2.js': return ''  # assets.local.js に つないだ
    if name == 'questions.js': return qdb_script()
    return '<script>' + js(src(name).read_text()) + '</script>'
html = re.sub(r'<script src="([^"]+)"></script>', script, html)
# いつ作った版かを タイトルに出す（Canva で 差しかえが 反映されたか ひと目でわかるように）
import datetime
ver = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%-m/%-d %H:%M')
# 冬眠版（4.0.0）：Canva版だけ 育成ダンジョン・無限の塔を 灰色・ログボなし。5.0.0 で None に もどす（GitHub版・1ファイル版・ZIPは 3.0.0 のまま）
HIB_VER = None  # まなびバトル2 は 冬眠版なし
html = html.replace('<script>', f'<script>window.__VER={json.dumps(ver + (" Canva" if CANVA else ""))};{("window.__HIB=" + json.dumps(HIB_VER) + ";") if CANVA and HIB_VER else ""}</script>\n<script>', 1)
left = [p for p in PATH.findall(re.sub(r'data:[^"\')]+', '', html)) if p not in emb and exists(p)]
OUT.write_text(html)
print(f'{OUT}（{OUT.stat().st_size / 1e6:.1f} MB・BGM {KBPS}kbps モノラル・埋めこみ {len(emb)} ファイル）')
if left: print('のこっているパス:', sorted(set(left))[:10])
