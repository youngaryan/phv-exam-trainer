'use strict';

const assert = require('node:assert/strict');
const { pathToFileURL } = require('node:url');
const path = require('node:path');
const { chromium, webkit, devices } = require('playwright');

const url = process.argv[2] || pathToFileURL(path.resolve(__dirname, '../../app/index.html')).href;
const engine = process.argv[3] || 'chromium';
const action = (page, name, filter = '') => page.locator(`[data-action="${name}"]${filter}`).first().tap();
const points = page => page.evaluate(() => PHV.state.attempt.answers[PHV_UI.question.id]?.points || []);
const zoom = page => page.evaluate(() => PHV_UI.map.getZoom());

async function checkWidth(page) {
  const sizes = await page.evaluate(() => [document.documentElement.scrollWidth, document.documentElement.clientWidth]);
  assert.ok(sizes[0] <= sizes[1] + 1, `Page overflows horizontally: ${sizes}`);
}

async function mapBox(page) {
  const map = page.locator('#route-map');
  await map.evaluate(el => el.scrollIntoView({ block: 'center' }));
  const box = await map.boundingBox();
  assert.ok(box.width >= page.viewportSize().width * 0.9, `Map is only ${box.width}px wide`);
  assert.ok(box.height >= 215, `Map is only ${box.height}px tall`);
  return box;
}

async function checkGestures(page) {
  const client = await page.context().newCDPSession(page);
  const box = await mapBox(page);
  const x = Math.round(box.x + box.width / 2), y = Math.round(box.y + box.height / 2);
  const touch = (type, touchPoints) => client.send('Input.dispatchTouchEvent', { type, touchPoints });
  // Give Leaflet a painted frame between finger positions, as with a physical gesture.
  const frame = () => page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
  const before = await page.evaluate(() => PHV_UI.map.getCenter());
  await touch('touchStart', [{ x, y }]);
  for (let i = 1; i <= 8; i++) {
    await touch('touchMove', [{ x: x + i * 7, y: y + i * 3 }]);
    await frame();
  }
  await touch('touchEnd', []);
  await page.waitForFunction(before => PHV_UI.map.getCenter().distanceTo(before) > 5, before);
  const previousZoom = await zoom(page);
  const fingers = gap => [{ id: 1, x: x - gap, y }, { id: 2, x: x + gap, y }];
  await touch('touchStart', fingers(20));
  for (let gap = 24; gap <= 60; gap += 4) {
    await touch('touchMove', fingers(gap));
    await frame();
  }
  await touch('touchEnd', []);
  await page.waitForFunction(previous => PHV_UI.map.getZoom() > previous, previousZoom);
  await client.detach();
}

async function runPhone(browser, profile, width, height, section) {
  const context = await browser.newContext({ ...devices[profile], viewport: { width, height } });
  try {
    const page = await context.newPage();
    page.setDefaultTimeout(15000);
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('response', response => { if (response.status() >= 400) errors.push(response.url()); });
    await page.goto(url, { timeout: 120000 });
    await checkWidth(page);
    await action(page, 'practice-picker', '[data-exam="topo"]');
    await checkWidth(page);
    await action(page, 'start-practice', `[data-section="route:${section}"]`);
    await checkWidth(page);
    const portrait = await mapBox(page);
    await page.waitForFunction(() => Array.from(document.querySelectorAll('.leaflet-tile')).some(img => img.complete && img.naturalWidth === 256 && !img.src.endsWith('empty.webp')));
    await page.locator('.route-instructions summary').tap();
    assert.equal(await page.locator('.route-instructions details').getAttribute('open'), '');
    await page.locator('.route-instructions summary').tap();

    await action(page, 'centre-start');
    await page.waitForFunction(() => PHV_UI.map.getZoom() >= 16);
    const initialZoom = await zoom(page);
    await page.locator('.leaflet-control-zoom-out').tap();
    await page.waitForFunction(z => PHV_UI.map.getZoom() === z - 1, initialZoom);
    // Begin a new gesture after the zoom transition and double-tap window finish.
    await page.waitForTimeout(500);
    if (engine === 'chromium') await checkGestures(page);
    assert.equal((await points(page)).length, 0);
    await action(page, 'centre-start');
    await page.locator('.route-marker.start').tap();
    assert.equal((await points(page)).length, 1);
    const box = await mapBox(page);
    await page.touchscreen.tap(box.x + box.width * 0.65, box.y + box.height * 0.6);
    const drawn = await points(page);
    assert.equal(drawn.length, 2);
    await action(page, 'legend');
    await page.waitForFunction(() => document.querySelector('dialog img')?.naturalWidth > 0);
    await action(page, 'close-dialog');
    await page.setViewportSize({ width: height, height: width });
    const landscape = await mapBox(page);
    await checkWidth(page);
    assert.deepEqual(await points(page), drawn);
    await page.reload({ timeout: 120000 });
    assert.deepEqual(await points(page), drawn);
    const resetZoom = await zoom(page);
    await page.locator('.leaflet-control-zoom-in').tap();
    await page.waitForFunction(z => PHV_UI.map.getZoom() > z, resetZoom);
    await action(page, 'check');
    await page.locator('#route-feedback h2').waitFor();
    await action(page, 'undo-route');
    assert.equal((await points(page)).length, 1);
    assert.equal(await page.locator('#route-feedback').isVisible(), false);
    await action(page, 'clear-route');
    assert.equal((await points(page)).length, 0);

    await page.setViewportSize({ width, height });
    await action(page, 'exit');
    await action(page, 'practice-picker', '[data-exam="seru"]');
    await checkWidth(page);
    await action(page, 'start-practice', '[data-section="1"]');
    await action(page, 'begin-practice');
    if (await page.locator('.word-bank').count()) {
      const question = await page.evaluate(() => PHV_UI.question);
      for (const [blank, word] of Object.entries(question.blanks)) {
        await page.locator('.word-bank').getByRole('button', { name: word, exact: true }).tap();
        await action(page, 'place-word', `[data-blank="${blank}"]`);
      }
      while (await page.locator('.word-bank button').count()) {
        await page.locator('.word-bank button').first().tap();
        await page.locator('.discard-title').tap();
      }
      await action(page, 'check');
    } else {
      await page.locator('.option').first().tap();
    }
    await page.locator('.feedback-panel').waitFor();
    await checkWidth(page);
    await action(page, 'review');
    await action(page, 'finish-confirm');
    await action(page, 'finish');
    await page.locator('.result-hero').waitFor();
    await checkWidth(page);
    assert.deepEqual(errors, []);
    console.log(`${engine} ${width}×${height} ${section}: portrait map ${portrait.width}×${Math.round(portrait.height)}, landscape ${landscape.width}×${Math.round(landscape.height)}, route and SERU passed`);
  } finally {
    await context.close();
  }
}

(async () => {
  assert.ok(['chromium', 'webkit'].includes(engine));
  const browser = engine === 'webkit' ? await webkit.launch() : await chromium.launch({ channel: process.env.CHROMIUM_CHANNEL || 'msedge' });
  try {
    if (engine === 'webkit') await runPhone(browser, 'iPhone 13', 390, 844, 'short');
    else {
      await runPhone(browser, 'Pixel 7', 412, 915, 'long');
      await runPhone(browser, 'iPhone SE', 320, 568, 'closure');
    }
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
