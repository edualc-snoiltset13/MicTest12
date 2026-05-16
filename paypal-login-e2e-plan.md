# PayPal Login Page — Automated E2E Test Plan (Playwright)

This document specifies the end-to-end test strategy for
`paypal-login.html` and the companion `paypal_demo_db.py` backend.
The implementation lives in `tests-e2e/paypal-login.spec.js` and is
driven by `playwright.config.js`.

## 1. Scope

In scope:

- The HTML page rendered both from the local HTTP server and from
  `file://` (static fallback).
- The two-step login form (email → password progressive disclosure).
- The `/api/register` and `/api/login` JSON endpoints exposed by the
  loopback HTTP server.
- Visual/structural sanity checks: branding, disclaimer, responsive
  breakpoints, focus styling.
- Accessibility basics: labels, autocomplete hints, keyboard
  reachability.

Out of scope:

- Cross-browser pixel-perfect visual diffing (use Playwright's
  built-in `toHaveScreenshot` later if needed).
- Real PayPal endpoints. We never hit the public internet.
- Load / performance testing.

## 2. Tooling

| Tool | Purpose |
| --- | --- |
| `@playwright/test` | Test runner, assertions, browser automation |
| `playwright.config.js` | Spawns `paypal_demo_db.py serve` as `webServer` |
| `paypal_demo_db.py` | Provides the live HTTP API under test |

A scratch SQLite DB (`.playwright-tmp.db`) is created per run and is
git-ignored. No shared state between developer machines.

## 3. Local setup

```bash
npm install
npx playwright install --with-deps
npm run test:e2e
```

`npm run test:e2e:ui` opens the Playwright UI runner.
`npm run test:e2e:headed` watches the browser drive the page.
`npm run test:e2e:report` opens the last HTML report.

## 4. Environments / projects

`playwright.config.js` runs every suite against five projects:

| Project | Device emulation |
| --- | --- |
| chromium | Desktop Chrome (1280×800) |
| firefox | Desktop Firefox |
| webkit | Desktop Safari |
| mobile-chrome | Pixel 5 |
| mobile-safari | iPhone 13 |

`workers: 1` keeps the SQLite-backed server happy under serial access.
On CI, retries are enabled and a HTML report is produced.

## 5. Test suites and what they cover

### 5.1 Page chrome and branding
| Test | Asserts |
| --- | --- |
| Title + heading | `<title>` and the H1 match the expected copy. |
| Disclaimer visible | Yellow banner is present and mentions "educational purposes", "not affiliated with PayPal", "does not submit credentials". |
| Two-color wordmark | SVG `<text>` fills are `#003087` and `#009cde`. |
| Viewport meta | `width=device-width, initial-scale=1` is present. |
| Affordances | Create Account button, "Forgot email?" link, and language row are visible. |

### 5.2 Form behavior — progressive disclosure
| Test | Asserts |
| --- | --- |
| Initial state | Password field hidden; submit reads "Next". |
| Blank email | Submitting with empty input does NOT advance. |
| Advance on valid email | Password field appears, button reads "Log In", focus moves to password input. |
| Floating label | Label `top` differs between resting and focused states. |
| Focus ring color | `border-color` on focused input is `rgb(0, 112, 186)` (PayPal blue). |

### 5.3 Loopback API flow through the UI
| Test | Asserts |
| --- | --- |
| Auto-register on unknown email | Submitting fresh credentials shows "Registered new demo account". |
| Login with existing account | After pre-registering via API, submitting the same creds shows "Logged in (demo account)". |
| Wrong password | Shows "Invalid credentials". |
| Submit lifecycle | Button disables during the request and re-enables afterwards. |

### 5.4 API contract (direct HTTP requests)
| Test | Asserts |
| --- | --- |
| Register success | `POST /api/register` → 201, `{ ok: true, id: number }`. |
| Short password | → 400, error mentions "8 characters". |
| Malformed email | → 400. |
| Duplicate email | → 400, error mentions "already exists". |
| Login success | → 200, `{ ok: true }`. |
| Wrong password | → 401, `{ ok: false }`. |
| Unknown account | → 401. |
| Case-insensitive email | Login works regardless of email casing. |
| Unknown route | → 404. |
| Path traversal | `GET /../paypal_demo_db.py` is refused (≥400). |

### 5.5 Static (`file://`) fallback
| Test | Asserts |
| --- | --- |
| No-API mode | Loading the HTML from disk and submitting shows "Demo only — nothing submitted" and disables the button. |

### 5.6 Responsive layout
| Test | Asserts |
| --- | --- |
| Mobile fit | At 390×844 the card width is ≤ viewport width and left-aligned ≥ 0. |
| Mobile radius | Below the 480px breakpoint, card `border-radius` is `16px`. |
| Desktop radius | At 1280px, card `border-radius` is `24px`. |

### 5.7 Accessibility basics
| Test | Asserts |
| --- | --- |
| Inputs have labels | Each input has a matching `<label for>`. |
| Keyboard reachable | Typing an email and pressing Enter advances the form. |
| Autocomplete hints | `email` is `username`; `password` is `current-password`. |

### 5.8 Smoke
| Test | Asserts |
| --- | --- |
| Clean console | No `pageerror` and no `console.error` after `networkidle`. |

## 6. Data strategy

- Each test that needs an account calls `uniqueEmail()` so emails never
  collide across runs.
- The scratch DB is destroyed implicitly by deleting
  `.playwright-tmp.db` — it lives outside the committed tree and is
  re-created by the server on boot.

## 7. CI integration

Recommended GitHub Actions step:

```yaml
- uses: actions/setup-node@v4
  with: { node-version: '22' }
- uses: actions/setup-python@v5
  with: { python-version: '3.12' }
- run: npm ci
- run: npx playwright install --with-deps
- run: npm run test:e2e
- uses: actions/upload-artifact@v4
  if: always()
  with:
    name: playwright-report
    path: playwright-report
```

Python unit tests (`python -m unittest discover`) continue to run in
their own job — Playwright is layered on top of, not in place of, the
existing 55-test Python suite.

## 8. Risks & mitigations

| Risk | Mitigation |
| --- | --- |
| Tests hit a real PayPal-look-alike server. | `playwright.config.js` only points at `127.0.0.1`; the Python server refuses non-loopback binds. |
| Persistent demo accounts pollute developer DBs. | Each run uses a dedicated `.playwright-tmp.db`; gitignored. |
| Flaky timing on the disable→enable transition. | Explicit `toBeEnabled({ timeout })` instead of fixed sleeps. |
| Cross-browser CSS drift. | Five-browser matrix already configured. |

## 9. Future work

- Add `toHaveScreenshot` baselines for the card at mobile + desktop.
- Add an axe-core accessibility pass (`@axe-core/playwright`).
- Add a "no third-party network calls" test that fails if any request
  goes outside `127.0.0.1`.
- Wire into `package.json` scripts: `test:py`, `test:e2e`, `test`.
