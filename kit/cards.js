const { chromium } = require('playwright');
const fs = require('fs');
const nar = JSON.parse(fs.readFileSync('/home/claude/vid/nar/nar.json'));
const F = 'file:///home/claude/limina-videos/kit/fonts/';
const css = `
@font-face{font-family:R;font-weight:400;src:url(${F}rubik-latin-400-normal.woff2)}
@font-face{font-family:R;font-weight:500;src:url(${F}rubik-latin-500-normal.woff2)}
@font-face{font-family:R;font-weight:700;src:url(${F}rubik-latin-700-normal.woff2)}
@font-face{font-family:R;font-weight:900;src:url(${F}rubik-latin-900-normal.woff2)}
@font-face{font-family:M;font-weight:700;src:url(${F}jetbrains-mono-700.woff2)}
*{box-sizing:border-box;margin:0} html,body{width:1080px;height:1920px;background:transparent;font-family:R}
.card{width:1080px;height:1920px;background:#8a3fc4;color:#fff;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;position:relative}
.logo{display:flex;align-items:center;gap:34px}
.word{font:900 150px R;letter-spacing:.16em;margin-right:-.16em}
.chips{display:flex;flex-direction:column;gap:10px}
.chip{font:700 30px M;color:#fff;padding:6px 14px;border-radius:12px;letter-spacing:.04em}
.g{background:#1f8f55;box-shadow:0 5px 0 #146b3e}.o{background:#ee7419;box-shadow:0 5px 0 #b85510}.p{background:#64289a;box-shadow:0 5px 0 #4a1d73;outline:3px solid rgba(255,255,255,.35)}
.tag{font:400 44px R;opacity:.9;margin-top:36px}
.pill{display:inline-block;margin-top:110px;background:#ffb547;color:#1d2433;font:700 40px R;padding:16px 34px;border-radius:40px;box-shadow:0 6px 0 #c47a12}
.big{font:900 96px R;margin-top:40px;line-height:1.05}
.date{font:500 50px R;margin-top:22px;opacity:.95}
.spoil{position:absolute;bottom:430px;font:500 36px R;opacity:.8}
.url{font:900 74px R;background:#fff;color:#8a3fc4;padding:22px 44px;border-radius:28px;margin-top:30px;box-shadow:0 8px 0 #64289a}
.cap{position:absolute;left:0;right:0;bottom:105px;display:flex;justify-content:center}
.cap div{max-width:960px;background:rgba(29,36,51,.9);color:#fff;font:500 50px/1.28 R;padding:20px 32px;border-radius:24px;text-align:center}
.cap b{font-weight:700}.cap .og{color:#ff9a4a}.cap .gn{color:#3fd98a}
.later{position:absolute;left:0;right:0;top:330px;display:flex;justify-content:center}
.later div{background:#ffb547;color:#1d2433;font:700 54px R;padding:18px 40px;border-radius:40px;box-shadow:0 6px 0 #c47a12}
`;
const logo = `<div class="logo"><div class="word">LIMINA</div><div class="chips"><span class="chip g">M·N</span><span class="chip o">A·L</span><span class="chip p">I·M</span></div></div>`;
function esc(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;')}
function fmt(s){ return esc(s).replace(/\b([A-Z]{4,})\b/g,'<b>$1</b>').replace(/\borange\b/g,'<span class="og">orange</span>').replace(/\bgreen\b/g,'<span class="gn">green</span>'); }
(async()=>{
  const b = await chromium.launch(); const p = await b.newPage({viewport:{width:1080,height:1920}});
  async function shot(html, path, transparent){ fs.writeFileSync("/tmp/card.html", `<!doctype html><meta charset=utf-8><style>${css}</style>${html}`); await p.goto("file:///tmp/card.html"); await p.evaluate(()=>document.fonts.ready); await p.waitForTimeout(150); await p.screenshot({path, omitBackground:!!transparent}); }
  await shot(`<div class="card">${logo}<div class="tag">Find the order. Find the word.</div>
    <div class="pill">Founder's solve</div><div class="big">Daily puzzle #29</div><div class="date">Monday 23 November</div>
    <div class="spoil">Spoiler: the answer is at the end</div></div>`, '/home/claude/vid/png/open.png');
  await shot(`<div class="card">${logo}<div class="tag">Find the order. Find the word.</div>
    <div class="big" style="margin-top:120px">Free. New puzzle<br>every day.</div><div class="date" style="margin-top:60px">Play at</div>
    <div class="url">liminawordgame.com</div></div>`, '/home/claude/vid/png/close.png');
  await shot(`<div class="later"><div>⏱ 4½ minutes later…</div></div>`, '/home/claude/vid/png/later.png', true);
  for (const [k,v] of Object.entries(nar)) for (let i=0;i<v.caps.length;i++)
    await shot(`<div class="cap"><div>${fmt(v.caps[i][2])}</div></div>`, `/home/claude/vid/png/cap_${k}_${i}.png`, true);
  await b.close();
})();
