# まなびバトル2 の 新しい アイテム（102〜131）：エラーなく 動くか・勝率が かわるか（simVs。同じ ステータス どうし）
import pathlib, json
from playwright.sync_api import sync_playwright
ROOT = pathlib.Path(__file__).resolve().parent.parent
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1280, 'height': 720})
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto((ROOT / 'index.html').as_uri() + '?test'); pg.wait_for_timeout(600)
    pg.fill('#pn', 'てすと'); pg.fill('#cn', 'もん'); pg.click('#go'); pg.wait_for_timeout(300)
    r = pg.evaluate("""(() => { const st = { 国語: 400, 算数: 300, 理科: 250, 社会: 350, 英語: 300 }, stB = { 国語: 350, 算数: 300, 理科: 300, 社会: 300, 英語: 350 };
      const base = MB.simVs({ stA: st, stB, n: 3000 }).win, out = { base };
      MB.D.ITEMS.slice(101).forEach(it => { try { out[it.n] = MB.simVs({ stA: st, stB, itemsA: [it.n], n: 3000 }).win; } catch (e) { out[it.n] = 'ERR ' + e.message; } });
      ['ねらいのメガネ', '木の盾', 'たこ焼き', 'にじの紋章', '背水の書', '特化の王冠', 'メテオ'].forEach(n => (out['(旧)' + n] = MB.simVs({ stA: st, stB, itemsA: [n], n: 3000 }).win));
      out.both = MB.simVs({ stA: st, stB, itemsA: MB.D.ITEMS.slice(101, 116).map(i => i.n), itemsB: MB.D.ITEMS.slice(116).map(i => i.n), n: 500 }).win;
      return out; })()""")
    for k, v in r.items(): print(k, v)
    print('errors:', errs or 'なし'); b.close()
