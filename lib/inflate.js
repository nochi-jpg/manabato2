// ===== 小さな inflate（raw DEFLATE を もとにもどす。同期）=====
// Canva版で 問題DB を 小さくして 入れるために つかう（tools/build_html.py）。外部ライブラリなし
window.MB_INFLATE = (function () {
  'use strict';
  const LBASE = [3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 15, 17, 19, 23, 27, 31, 35, 43, 51, 59, 67, 83, 99, 115, 131, 163, 195, 227, 258];
  const LEXT = [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 0];
  const DBASE = [1, 2, 3, 4, 5, 7, 9, 13, 17, 25, 33, 49, 65, 97, 129, 193, 257, 385, 513, 769, 1025, 1537, 2049, 3073, 4097, 6145, 8193, 12289, 16385, 24577];
  const DEXT = [0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12, 13, 13];
  const CLORD = [16, 17, 18, 0, 8, 7, 9, 6, 10, 5, 11, 4, 12, 3, 13, 2, 14, 1, 15];
  // ハフマン表：長さの 数（cnt）と 記号の じゅん（sym）
  function build(lens, n) {
    const cnt = new Uint16Array(16), sym = new Uint16Array(n), off = new Uint16Array(16);
    for (let i = 0; i < n; i++) cnt[lens[i]]++;
    cnt[0] = 0;
    for (let i = 1; i < 16; i++) off[i] = off[i - 1] + cnt[i - 1];
    for (let i = 0; i < n; i++) if (lens[i]) sym[off[lens[i]]++] = i;
    return { cnt, sym };
  }
  return function inflate(src) {
    let pos = 0, bit = 0, bits = 0, out = new Uint8Array(src.length * 4), len = 0;
    const need = k => { if (len + k > out.length) { const o = new Uint8Array(Math.max(out.length * 2, len + k)); o.set(out); out = o; } };
    const getb = k => { while (bits < k) { bit |= (src[pos++] || 0) << bits; bits += 8; } const v = bit & ((1 << k) - 1); bit >>>= k; bits -= k; return v; };
    const dec = t => { let code = 0, first = 0, idx = 0; for (let l = 1; l < 16; l++) { code |= getb(1); const c = t.cnt[l]; if (code - c < first) return t.sym[idx + code - first]; idx += c; first += c; first <<= 1; code <<= 1; } throw new Error('inflate'); };
    let fin;
    do {
      fin = getb(1); const type = getb(2);
      if (type === 0) {
        bit = 0; bits = 0; const n = src[pos] | (src[pos + 1] << 8); pos += 4;
        need(n); out.set(src.subarray(pos, pos + n), len); len += n; pos += n; continue;
      }
      let lt, dt;
      if (type === 1) {
        const l = new Uint8Array(288); l.fill(8, 0, 144); l.fill(9, 144, 256); l.fill(7, 256, 280); l.fill(8, 280, 288);
        lt = build(l, 288); const d = new Uint8Array(30).fill(5); dt = build(d, 30);
      } else if (type === 2) {
        const hl = getb(5) + 257, hd = getb(5) + 1, hc = getb(4) + 4;
        const cl = new Uint8Array(19); for (let i = 0; i < hc; i++) cl[CLORD[i]] = getb(3);
        const ct = build(cl, 19), L = new Uint8Array(hl + hd);
        for (let i = 0; i < hl + hd;) {
          const s = dec(ct);
          if (s < 16) L[i++] = s;
          else if (s === 16) { const p = L[i - 1], r = 3 + getb(2); L.fill(p, i, i + r); i += r; }
          else if (s === 17) i += 3 + getb(3);
          else i += 11 + getb(7);
        }
        lt = build(L.subarray(0, hl), hl); dt = build(L.subarray(hl), hd);
      } else throw new Error('inflate');
      for (;;) {
        const s = dec(lt);
        if (s < 256) { need(1); out[len++] = s; }
        else if (s === 256) break;
        else {
          const k = s - 257, n = LBASE[k] + getb(LEXT[k]), ds = dec(dt), dist = DBASE[ds] + getb(DEXT[ds]);
          need(n); for (let i = 0; i < n; i++, len++) out[len] = out[len - dist];
        }
      }
    } while (!fin);
    return out.subarray(0, len);
  };
})();
