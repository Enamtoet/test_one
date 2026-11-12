// Usage: node render_frames.js video.html <out_dir> [timeline.json] [--preview t1,t2,...]
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
(async () => {
  const args = process.argv.slice(2);
  const [html, outDir] = args;
  const tlFile = args[2] && !args[2].startsWith('--') ? args[2] : null;
  const pv = args.indexOf('--preview');
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  await page.goto('file://' + path.resolve(html));
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(800);
  if (tlFile) await page.evaluate(tl => setTimeline(tl), JSON.parse(fs.readFileSync(tlFile, 'utf8')));
  const total = await page.evaluate(() => window.TOTAL);
  const fps = 30;
  const times = pv >= 0 ? args[pv + 1].split(',').map(Number)
                        : Array.from({ length: Math.round(total * fps) }, (_, i) => i / fps);
  for (let i = 0; i < times.length; i++) {
    await page.evaluate(t => render(t), times[i]);
    await page.screenshot({ path: `${outDir}/f${String(i).padStart(5, '0')}.jpg`, type: 'jpeg', quality: 92 });
  }
  console.log('frames', times.length, 'total', total);
  await browser.close();
})();
