#!/usr/bin/env node
/**
 * Assertion verifier.
 *
 * The Cypress suite in `cypress/e2e` is the deliverable. This script exists
 * because a test suite that has never been executed is a claim, not a check -
 * and in this environment the Cypress binary cannot be downloaded (the archive
 * arrives truncated through the egress proxy).
 *
 * So this reproduces the *load-bearing assertions* of the suite against the
 * same running stack, using Playwright as the driver. It is not a replacement
 * for the Cypress run in CI; it is evidence that the assertions the suite makes
 * are ones the application actually satisfies.
 *
 * Usage:
 *   node verify-assertions.mjs [baseUrl]
 */

import { chromium } from 'playwright';

const BASE = process.argv[2] ?? 'http://localhost:4173';
const EXECUTABLE = process.env.CHROMIUM_PATH ?? '/opt/pw-browsers/chromium';

const LOCALES = ['en', 'de', 'es', 'nl', 'ru'];
const COMMA_DECIMAL = ['de', 'es', 'nl', 'ru'];
const VIEWPORTS = {
  narrow: [320, 640],
  galaxyA: [360, 740],
  iphoneSe: [375, 667],
  galaxyS: [412, 915],
  tablet: [768, 1024],
  laptop: [1024, 768],
  desktop: [1440, 900],
};

const results = [];

function record(id, name, passed, detail = '') {
  results.push({ id, name, passed, detail });
  const mark = passed ? 'PASS' : 'FAIL';
  console.log(`  ${mark}  ${id}  ${name}${detail ? ` - ${detail}` : ''}`);
}

async function overflow(page) {
  return page.evaluate(() => {
    const el = document.documentElement;
    return el.scrollWidth - el.clientWidth;
  });
}

const browser = await chromium.launch({ executablePath: EXECUTABLE, channel: 'chromium' });

try {
  // --- EC-26 / EC-27: no horizontal overflow, 5 locales x 7 viewports x 2 pages
  console.log('\nEC-26/EC-27  horizontal containment across the locale x viewport matrix');
  {
    const failures = [];
    let checked = 0;
    for (const [vpName, [width, height]] of Object.entries(VIEWPORTS)) {
      const ctx = await browser.newContext({ viewport: { width, height } });
      const page = await ctx.newPage();
      for (const locale of LOCALES) {
        for (const path of ['/', '/cases/HEM-001']) {
          await page.goto(`${BASE}${path}?lang=${locale}`, { waitUntil: 'networkidle' });
          await page.waitForTimeout(250);
          const over = await overflow(page);
          checked += 1;
          if (over > 1) failures.push(`${path} ${locale}@${vpName}(${width}px)=+${over}px`);
        }
      }
      await ctx.close();
    }
    record(
      'EC-26/27',
      `${checked} layout combinations contain themselves`,
      failures.length === 0,
      failures.length ? failures.slice(0, 4).join(', ') : `${checked} checked`,
    );
  }

  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await ctx.newPage();

  // --- EC-31: decimal separator follows the locale
  console.log('\nEC-31  decimal separators follow the locale');
  {
    await page.goto(`${BASE}/cases/THY-001?lang=en`, { waitUntil: 'networkidle' });
    const englishRow = await page.locator('[data-testid="lab-result-row"][data-analyte="TSH"]').first().innerText();
    record('EC-31a', 'English renders 0.005 with a point', englishRow.includes('0.005'), englishRow.split('\n')[0]);

    for (const locale of COMMA_DECIMAL) {
      await page.goto(`${BASE}/cases/THY-001?lang=${locale}`, { waitUntil: 'networkidle' });
      const row = await page.locator('[data-testid="lab-result-row"][data-analyte="TSH"]').first().innerText();
      const hasComma = /0,005/.test(row);
      const hasPoint = /0\.005/.test(row);
      record(
        `EC-31-${locale}`,
        `${locale} renders 0,005 with a comma and not a point`,
        hasComma && !hasPoint,
        `comma=${hasComma} point=${hasPoint}`,
      );
    }
  }

  // --- EC-32: chart axis labels use the same convention
  console.log('\nEC-32  chart labels follow the same convention as the table');
  {
    await page.goto(`${BASE}/cases/THY-003?lang=de`, { waitUntil: 'networkidle' });
    const label = await page
      .locator('[data-testid="lab-trend-chart"][data-analyte="TSH"] .chart-endpoint-label')
      .first()
      .textContent();
    record('EC-32', 'German chart endpoint label uses a comma decimal', /\d+,\d+/.test(label), label);
  }

  // --- EC-33: Russian CLDR plural categories
  console.log('\nEC-33  Russian plural categories');
  {
    await page.goto(`${BASE}/?lang=ru`, { waitUntil: 'networkidle' });
    await page.waitForSelector('[data-testid="case-card"]');
    const many = await page.locator('[data-testid="result-count"]').innerText();
    record('EC-33a', '25 selects the "many" form (случаев)', /случаев/.test(many), many);

    // The filter counter is the control whose number genuinely varies, so it
    // is where one/few are actually exercised. (In the "N of M" result string
    // the noun agrees with the TOTAL, which is always 25 here.)
    await page.selectOption('[data-testid="discipline-filter"]', 'microbiology');
    await page.waitForTimeout(700);
    const one = await page.locator('[data-testid="active-filter-count"]').innerText();
    record('EC-33b', '1 filter selects the "one" form (фильтр)', /Активен 1 фильтр/.test(one), one);

    await page.fill('[data-testid="search-input"]', 'lep');
    await page.waitForTimeout(900);
    const few = await page.locator('[data-testid="active-filter-count"]').innerText();
    record('EC-33c', '2 filters select the "few" form (фильтра)', /Активны 2 фильтра/.test(few), few);

    // And the filtered result string agrees with the total, not the count:
    // "N из 25 случаев" is correct Russian; "N из 25 случая" is not.
    const filtered = await page.locator('[data-testid="result-count"]').innerText();
    record('EC-33d', 'filtered count agrees with the total', /из 25 случаев/.test(filtered), filtered);
  }

  // --- EC-34: Cyrillic renders without tofu
  console.log('\nEC-34  Cyrillic rendering');
  {
    await page.goto(`${BASE}/cases/HEM-002?lang=ru`, { waitUntil: 'networkidle' });
    const heading = await page.locator('h1').first().innerText();
    record(
      'EC-34',
      'Russian heading is Cyrillic with no replacement glyphs',
      /[Ѐ-ӿ]/.test(heading) && !/[�□]/.test(heading),
      heading.slice(0, 50),
    );
  }

  // --- EC-14: flag badges carry three redundant channels
  console.log('\nEC-14  critical flags do not rely on colour');
  {
    await page.goto(`${BASE}/cases/THY-002?lang=en`, { waitUntil: 'networkidle' });
    const badge = await page.locator('[data-testid="flag-HH"]').first().innerText();
    record(
      'EC-14',
      'critical badge has glyph + code + accessible name',
      /[▲▼]/.test(badge) && badge.includes('HH') && /Critically high/i.test(badge),
      JSON.stringify(badge),
    );
  }

  // --- EC-18: reference band has real height
  console.log('\nEC-18  reference band');
  {
    await page.goto(`${BASE}/cases/THY-003?lang=en`, { waitUntil: 'networkidle' });
    const height = await page
      .locator('[data-testid="lab-trend-chart"][data-analyte="TSH"] [data-testid="reference-band"]')
      .first()
      .getAttribute('height');
    record('EC-18', 'reference band is drawn with non-zero height', Number(height) > 0, `height=${height}`);
  }

  // --- EC-20: table view equivalence
  console.log('\nEC-20  every chart has an equivalent data table');
  {
    const chart = page.locator('[data-testid="lab-trend-chart"][data-analyte="TSH"]').first();
    await chart.locator('[data-testid="table-view-toggle"]').click();
    await page.waitForTimeout(200);
    const rows = await chart.locator('tbody tr').count();
    record('EC-20', 'table view lists every measurement', rows >= 6, `${rows} rows`);
    await chart.locator('[data-testid="chart-view-toggle"]').click();
  }

  // --- EC-19: qualitative results excluded from charts, present in the table
  console.log('\nEC-19  qualitative results are not plotted');
  {
    await page.goto(`${BASE}/cases/HEM-001?lang=en`, { waitUntil: 'networkidle' });
    const charted = await page.locator('[data-testid="lab-trend-chart"][data-analyte="DAT_POLY"]').count();
    const tabled = await page.locator('[data-testid="lab-result-row"][data-analyte="DAT_POLY"]').first().innerText();
    record(
      'EC-19',
      'DAT is absent from the charts but present in the table',
      charted === 0 && /Positive/i.test(tabled),
      `charts=${charted}`,
    );
  }

  // --- EC-24: diagnosis gated behind a deliberate reveal
  console.log('\nEC-24  diagnosis reveal');
  {
    await page.goto(`${BASE}/cases/HEM-005?lang=en`, { waitUntil: 'networkidle' });
    const before = await page.locator('[data-testid="primary-diagnosis"]').count();
    await page.locator('[data-testid="reveal-diagnosis"]').click();
    await page.waitForTimeout(200);
    const after = await page.locator('[data-testid="primary-diagnosis"]').count();
    record('EC-24', 'diagnosis hidden until revealed', before === 0 && after === 1);
  }

  // --- EC-41 / EC-43: malformed and non-JSON bodies
  console.log('\nEC-41/EC-43  rewritten response bodies');
  {
    await page.route('**/api/v1/cases?*', (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: '{"meta":{"total":25},"items":[{"id":1,,' }),
    );
    await page.goto(`${BASE}/?lang=en`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(400);
    const kind = await page.locator('[data-testid="error-state"]').first().getAttribute('data-error-kind');
    record('EC-41', 'malformed JSON produces a parse error state', kind === 'parse', `kind=${kind}`);
    await page.unroute('**/api/v1/cases?*');

    await page.route('**/api/v1/cases?*', (route) =>
      route.fulfill({ status: 200, contentType: 'text/html', body: '<html><body>Sign in</body></html>' }),
    );
    await page.goto(`${BASE}/?lang=en`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(400);
    const kind2 = await page.locator('[data-testid="error-state"]').first().getAttribute('data-error-kind');
    record('EC-43', 'a captive-portal HTML body produces a parse error state', kind2 === 'parse', `kind=${kind2}`);
    await page.unroute('**/api/v1/cases?*');
  }

  // --- EC-39: status error with request id
  console.log('\nEC-39  server error surfaces the request id');
  {
    await page.route('**/api/v1/cases?*', (route) =>
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          type: '', title: 'Internal server error', status: 500,
          detail: 'Injected by the QA verifier.', instance: '/api/v1/cases',
          errors: [], request_id: 'qa-injected-500',
        }),
      }),
    );
    await page.goto(`${BASE}/?lang=en`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(400);
    const text = await page.locator('[data-testid="error-state"]').first().innerText();
    record('EC-39', 'error state quotes the request id', text.includes('qa-injected-500'));
    await page.unroute('**/api/v1/cases?*');
  }

  // --- EC-45: dropped connection
  console.log('\nEC-45  dropped connection');
  {
    await page.route('**/api/v1/cases?*', (route) => route.abort('connectionreset'));
    await page.goto(`${BASE}/?lang=en`, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1200);
    const kind = await page.locator('[data-testid="error-state"]').first().getAttribute('data-error-kind');
    record('EC-45', 'a reset connection produces a network error state', kind === 'network', `kind=${kind}`);
    await page.unroute('**/api/v1/cases?*');
  }

  // --- EC-49: stale response cannot overwrite newer results
  console.log('\nEC-49  stale in-flight response is discarded');
  {
    await page.route('**/api/v1/cases?*', async (route) => {
      if (!route.request().url().includes('discipline=')) {
        await new Promise((resolve) => setTimeout(resolve, 2500));
      }
      await route.continue();
    });
    await page.goto(`${BASE}/?lang=en`, { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('[data-testid="discipline-filter"]');
    await page.selectOption('[data-testid="discipline-filter"]', 'pharmacology');
    await page.waitForTimeout(1200);
    const during = await page.locator('[data-testid="case-card"]').count();
    await page.waitForTimeout(3000);
    const after = await page.locator('[data-testid="case-card"]').count();
    record('EC-49', 'filtered result survives the late unfiltered response', after === 3 && during === 3, `during=${during} after=${after}`);
    await page.unroute('**/api/v1/cases?*');
  }

  // --- EC-36: touch targets
  console.log('\nEC-36  touch targets on a phone viewport');
  {
    const mobileCtx = await browser.newContext({ viewport: { width: 360, height: 740 }, hasTouch: true, isMobile: true });
    const mobilePage = await mobileCtx.newPage();
    await mobilePage.goto(`${BASE}/?lang=de`, { waitUntil: 'networkidle' });
    const small = await mobilePage.evaluate(() => {
      const out = [];
      for (const el of document.querySelectorAll('button.btn-primary, button.btn-secondary, .segmented-option, select')) {
        const r = el.getBoundingClientRect();
        if (r.width > 0 && Math.min(r.width, r.height) < 39) {
          out.push(`${el.tagName}.${String(el.className).split(' ')[0]}=${Math.round(Math.min(r.width, r.height))}px`);
        }
      }
      return out;
    });
    record('EC-36', 'interactive controls meet the touch-target floor', small.length === 0, small.slice(0, 3).join(', '));
    await mobileCtx.close();
  }

  await ctx.close();
} finally {
  await browser.close();
}

const failed = results.filter((entry) => !entry.passed);
console.log(`\n${'='.repeat(70)}`);
console.log(`${results.length - failed.length}/${results.length} assertions passed`);
if (failed.length > 0) {
  console.log('\nFailures:');
  for (const entry of failed) console.log(`  ${entry.id}  ${entry.name}  ${entry.detail}`);
  process.exit(1);
}
console.log('All verified assertions hold against the running stack.');
