// Captures dfurrer.com/tools for the README. Needs playwright available:
//   npx playwright@1.62.1 install chromium && node tools/shoot.mjs
// so it needs a moment to settle before the shot.
//   node tools/shoot.mjs
import { chromium } from 'playwright';
import { execSync } from 'node:child_process';

const OUT = new URL('../assets/tools.webp', import.meta.url).pathname;
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1500, height: 860 }, deviceScaleFactor: 2 });
await p.goto('https://dfurrer.com/tools', { waitUntil: 'load', timeout: 60000 });
await p.waitForTimeout(6000);                 // tiles load, canvas settles
await p.evaluate(() => {                      // hide the drag hint and the cursor
  document.querySelector('#hint')?.remove();
  document.querySelectorAll('.cur,.cur-r').forEach(e => e.remove());
});
await p.waitForTimeout(800);
await p.screenshot({ path: OUT });
await b.close();
execSync(`sips -Z 1500 "${OUT}" >/dev/null; execSync(`cwebp -quiet -q 82 "${OUT}" -o "${OUT.replace(/png$/, 'webp')}"`)`);
console.log('wrote', OUT);
