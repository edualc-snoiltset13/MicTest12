// @ts-check
/**
 * End-to-end tests for the PayPal login UI recreation.
 *
 * These tests drive the live page served by paypal_demo_db.py and cover:
 *   - Layout, branding, and the educational disclaimer
 *   - Floating-label and focus styling
 *   - Two-step progressive disclosure (email -> password)
 *   - Loopback-only API: register, login, validation, idempotency
 *   - Accessibility basics (labels, focus order, viewport meta)
 *   - Static mode fallback when opened via file://
 *   - Responsive layout at desktop and mobile viewports
 */

const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

const SUCCESS_TEXTS = [
  /Registered new demo account/i,
  /Logged in \(demo account\)/i,
];

function uniqueEmail(prefix = 'pw') {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}@example.com`;
}

async function fillEmailStep(page, email) {
  await page.locator('#email').fill(email);
  await page.locator('#submit-btn').click();
  await expect(page.locator('#password-field')).toBeVisible();
  await expect(page.locator('#submit-btn')).toHaveText('Log In');
}

async function submitPassword(page, password) {
  await page.locator('#password').fill(password);
  await page.locator('#submit-btn').click();
}

test.describe('Page chrome and branding', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('has the expected title and main heading', async ({ page }) => {
    await expect(page).toHaveTitle(/Log in to your PayPal account/i);
    await expect(page.getByRole('heading', { name: /Log in to your account/i })).toBeVisible();
  });

  test('shows the educational disclaimer prominently', async ({ page }) => {
    const banner = page.locator('.demo-banner');
    await expect(banner).toBeVisible();
    await expect(banner).toContainText(/educational purposes/i);
    await expect(banner).toContainText(/not affiliated with PayPal/i);
    await expect(banner).toContainText(/does not submit credentials/i);
  });

  test('renders the PayPal-style two-color wordmark', async ({ page }) => {
    const logo = page.locator('.logo svg');
    await expect(logo).toBeVisible();
    await expect(logo.locator('text', { hasText: 'Pay' })).toHaveAttribute('fill', '#003087');
    await expect(logo.locator('text', { hasText: 'Pal' })).toHaveAttribute('fill', '#009cde');
  });

  test('exposes a viewport meta tag for responsive rendering', async ({ page }) => {
    const meta = await page.locator('meta[name="viewport"]').getAttribute('content');
    expect(meta).toMatch(/width=device-width/);
    expect(meta).toMatch(/initial-scale=1/);
  });

  test('has Create Account, Forgot email, and language links', async ({ page }) => {
    await expect(page.getByRole('button', { name: /Create Account/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /Forgot email\?/i })).toBeVisible();
    await expect(page.locator('.legal')).toContainText('English');
    await expect(page.locator('.legal')).toContainText('Fran');
  });
});

test.describe('Form behavior - progressive disclosure', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('password field is hidden until email step is submitted', async ({ page }) => {
    await expect(page.locator('#password-field')).toBeHidden();
    await expect(page.locator('#submit-btn')).toHaveText('Next');
  });

  test('blank email keeps the user on step 1', async ({ page }) => {
    await page.locator('#email').fill('   ');
    await page.locator('#submit-btn').click();
    await expect(page.locator('#password-field')).toBeHidden();
    await expect(page.locator('#submit-btn')).toHaveText('Next');
  });

  test('valid email reveals password and refocuses', async ({ page }) => {
    await fillEmailStep(page, uniqueEmail());
    await expect(page.locator('#password')).toBeFocused();
  });

  test('floating label animates up on focus', async ({ page }) => {
    const email = page.locator('#email');
    const label = page.locator('label[for="email"]');
    const restingTop = await label.evaluate((el) => getComputedStyle(el).top);
    await email.focus();
    const focusedTop = await label.evaluate((el) => getComputedStyle(el).top);
    expect(focusedTop).not.toEqual(restingTop);
  });

  test('focus ring uses PayPal blue', async ({ page }) => {
    const email = page.locator('#email');
    await email.focus();
    const borderColor = await email.evaluate((el) => getComputedStyle(el).borderColor);
    // #0070ba == rgb(0, 112, 186)
    expect(borderColor).toBe('rgb(0, 112, 186)');
  });
});

test.describe('Loopback API flow (served by paypal_demo_db.py)', () => {
  test('unknown email auto-registers as a new demo account', async ({ page }) => {
    await page.goto('/');
    await fillEmailStep(page, uniqueEmail('newacct'));
    await submitPassword(page, 'password1-demo');
    await expect(page.locator('#submit-btn')).toHaveText(SUCCESS_TEXTS[0], { timeout: 5_000 });
  });

  test('correct password for an existing account logs in', async ({ page, request }) => {
    const email = uniqueEmail('existing');
    const password = 'password1-demo';
    const res = await request.post('/api/register', { data: { email, password } });
    expect(res.status()).toBe(201);

    await page.goto('/');
    await fillEmailStep(page, email);
    await submitPassword(page, password);
    await expect(page.locator('#submit-btn')).toHaveText(SUCCESS_TEXTS[1], { timeout: 5_000 });
  });

  test('wrong password for an existing account does not log in', async ({ page, request }) => {
    const email = uniqueEmail('wrongpw');
    await request.post('/api/register', { data: { email, password: 'password1-demo' } });

    await page.goto('/');
    await fillEmailStep(page, email);
    await submitPassword(page, 'totally-wrong');
    await expect(page.locator('#submit-btn')).toHaveText(/Invalid credentials/i);
  });

  test('button is disabled while in-flight then re-enabled', async ({ page }) => {
    await page.goto('/');
    await fillEmailStep(page, uniqueEmail('disable'));
    await submitPassword(page, 'password1-demo');
    await expect(page.locator('#submit-btn')).toBeDisabled();
    await expect(page.locator('#submit-btn')).toBeEnabled({ timeout: 5_000 });
  });
});

test.describe('API contract (direct HTTP)', () => {
  test('POST /api/register returns 201 and { ok: true, id }', async ({ request }) => {
    const email = uniqueEmail('api-reg');
    const res = await request.post('/api/register', { data: { email, password: 'password1-demo' } });
    expect(res.status()).toBe(201);
    const body = await res.json();
    expect(body.ok).toBe(true);
    expect(typeof body.id).toBe('number');
  });

  test('POST /api/register rejects short password with 400', async ({ request }) => {
    const res = await request.post('/api/register', {
      data: { email: uniqueEmail('short'), password: 'x' },
    });
    expect(res.status()).toBe(400);
    const body = await res.json();
    expect(body.ok).toBe(false);
    expect(body.error).toMatch(/8 characters/i);
  });

  test('POST /api/register rejects malformed email with 400', async ({ request }) => {
    const res = await request.post('/api/register', {
      data: { email: 'not-an-email', password: 'password1-demo' },
    });
    expect(res.status()).toBe(400);
  });

  test('POST /api/register rejects duplicate email with 400', async ({ request }) => {
    const email = uniqueEmail('dup');
    const first = await request.post('/api/register', { data: { email, password: 'password1-demo' } });
    expect(first.status()).toBe(201);
    const second = await request.post('/api/register', { data: { email, password: 'password1-demo' } });
    expect(second.status()).toBe(400);
    const body = await second.json();
    expect(body.error).toMatch(/already exists/i);
  });

  test('POST /api/login returns 200 for correct credentials', async ({ request }) => {
    const email = uniqueEmail('api-login');
    const password = 'password1-demo';
    await request.post('/api/register', { data: { email, password } });
    const res = await request.post('/api/login', { data: { email, password } });
    expect(res.status()).toBe(200);
    expect((await res.json()).ok).toBe(true);
  });

  test('POST /api/login returns 401 for wrong password', async ({ request }) => {
    const email = uniqueEmail('api-bad');
    await request.post('/api/register', { data: { email, password: 'password1-demo' } });
    const res = await request.post('/api/login', { data: { email, password: 'nope' } });
    expect(res.status()).toBe(401);
    expect((await res.json()).ok).toBe(false);
  });

  test('POST /api/login returns 401 for unknown account', async ({ request }) => {
    const res = await request.post('/api/login', {
      data: { email: uniqueEmail('ghost'), password: 'password1-demo' },
    });
    expect(res.status()).toBe(401);
  });

  test('email lookup is case-insensitive', async ({ request }) => {
    const email = uniqueEmail('Case');
    const password = 'password1-demo';
    await request.post('/api/register', { data: { email, password } });
    const res = await request.post('/api/login', {
      data: { email: email.toUpperCase(), password },
    });
    expect(res.status()).toBe(200);
  });

  test('unknown route returns 404', async ({ request }) => {
    const res = await request.post('/api/nope', { data: {} });
    expect(res.status()).toBe(404);
  });

  test('path-traversal in static fetch is refused', async ({ request }) => {
    const res = await request.get('/../paypal_demo_db.py');
    expect(res.status()).toBeGreaterThanOrEqual(400);
  });
});

test.describe('Static (file://) fallback', () => {
  test('opening the HTML from disk shows "Demo only" on submit', async ({ page }) => {
    const fileUrl = 'file://' + path.resolve(__dirname, '..', 'paypal-login.html');
    await page.goto(fileUrl);
    await page.locator('#email').fill('local@example.com');
    await page.locator('#submit-btn').click();
    await page.locator('#password').fill('password1-demo');
    await page.locator('#submit-btn').click();
    await expect(page.locator('#submit-btn')).toHaveText(/Demo only/i);
    await expect(page.locator('#submit-btn')).toBeDisabled();
  });
});

test.describe('Responsive layout', () => {
  test('card is centered and fits within mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('/');
    const card = page.locator('.card');
    const box = await card.boundingBox();
    expect(box).not.toBeNull();
    if (box) {
      expect(box.width).toBeLessThanOrEqual(390);
      expect(box.x).toBeGreaterThanOrEqual(0);
    }
  });

  test('card uses a smaller radius below 480px breakpoint', async ({ page }) => {
    await page.setViewportSize({ width: 400, height: 800 });
    await page.goto('/');
    const radius = await page.locator('.card').evaluate((el) => getComputedStyle(el).borderRadius);
    expect(radius).toBe('16px');
  });

  test('card uses 24px radius on desktop', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto('/');
    const radius = await page.locator('.card').evaluate((el) => getComputedStyle(el).borderRadius);
    expect(radius).toBe('24px');
  });
});

test.describe('Accessibility basics', () => {
  test('every input has an associated <label>', async ({ page }) => {
    await page.goto('/');
    for (const id of ['email', 'password']) {
      const label = page.locator(`label[for="${id}"]`);
      await expect(label).toHaveCount(1);
    }
  });

  test('submit button is reachable by keyboard from the email field', async ({ page }) => {
    await page.goto('/');
    await page.locator('#email').focus();
    await page.keyboard.type(uniqueEmail('a11y'));
    await page.keyboard.press('Enter');
    await expect(page.locator('#password-field')).toBeVisible();
  });

  test('form has autocomplete hints', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('#email')).toHaveAttribute('autocomplete', 'username');
    await expect(page.locator('#password')).toHaveAttribute('autocomplete', 'current-password');
  });
});

test.describe('Visual snapshot (smoke)', () => {
  test('renders without console errors', async ({ page }) => {
    const errors = [];
    page.on('pageerror', (e) => errors.push(e.message));
    page.on('console', (msg) => {
      if (msg.type() === 'error') errors.push(msg.text());
    });
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    expect(errors).toEqual([]);
  });
});
