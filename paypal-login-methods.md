# PayPal Login Page — Methods

This document explains the techniques used to build `paypal-login.html`,
a static, educational recreation of the PayPal login screen.

## 1. Single-file delivery

Everything ships in one HTML file: structure, styles, and behavior. No
build step, no external CSS or JS, no fonts or images fetched from a
CDN. The page works when opened directly from disk (`file://`) and has
no third-party network calls.

- HTML for structure
- A `<style>` block in `<head>` for all CSS
- A small `<script>` block at the end of `<body>` for the two-step
  form behavior

## 2. Layout — Flexbox column with a centered card

The page body is a vertical flex container that pins the disclaimer
banner to the top and the footer to the bottom, while `<main>` grows
to fill the space and centers the card horizontally.

```css
body { display: flex; flex-direction: column; min-height: 100vh; }
main { flex: 1; display: flex; justify-content: center; }
```

The card itself uses `max-width: 460px` so it scales down to fit
small viewports without media queries doing the heavy lifting.

## 3. Brand wordmark via inline SVG

Instead of loading a logo image, the "PayPal" wordmark is rendered as
two `<text>` elements inside an inline SVG, each colored with one of
PayPal's two brand blues:

| Token | Hex |
| --- | --- |
| Dark blue ("Pay") | `#003087` |
| Light blue ("Pal") | `#009cde` |

Inline SVG keeps the logo crisp at any zoom level and removes a
network request.

## 4. Floating-label inputs (pure CSS)

The familiar "label sits inside the field, then floats up when the
field is focused or filled" effect is done with no JavaScript. The
trick is the `:placeholder-shown` pseudo-class plus a placeholder
that's a single space:

```html
<input id="email" placeholder=" " required>
<label for="email">Email or mobile number</label>
```

```css
.field input:focus + label,
.field input:not(:placeholder-shown) + label {
    top: 0.95rem;
    font-size: 0.75rem;
    transform: translateY(-50%) scale(0.95);
}
```

Because the placeholder is `" "`, `:placeholder-shown` is true only
when the user hasn't typed anything, so the label sits in the middle
until something is entered.

## 5. Focus ring matching PayPal's input style

PayPal's inputs show a doubled blue border on focus. That's
reproduced with a 1px border plus a `box-shadow` of the same color,
which acts like a second border without changing layout:

```css
.field input:focus {
    border-color: #0070ba;
    box-shadow: 0 0 0 1px #0070ba;
}
```

## 6. Two-step form via progressive disclosure

PayPal asks for the email first, then reveals the password field.
That's implemented with a hidden second field and a tiny state
machine in JavaScript:

```js
form.addEventListener('submit', function (e) {
    e.preventDefault();
    if (step === 'email') {
        passwordField.hidden = false;
        submitBtn.textContent = 'Log In';
        step = 'password';
    } else {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Demo only — nothing submitted';
    }
});
```

`e.preventDefault()` is unconditional, so the form **never** posts
anywhere. The `hidden` attribute is used instead of a `display: none`
class to keep semantics correct for screen readers.

## 7. Divider with text via flexbox + pseudo-elements

The "or" divider is two `::before` / `::after` lines that share space
with the text, using `flex: 1` to stretch:

```css
.divider { display: flex; align-items: center; }
.divider::before, .divider::after {
    content: ""; flex: 1; border-bottom: 1px solid #d1d4d6;
}
```

## 8. Button hierarchy

Two button styles encode visual hierarchy:

- **Primary** (`Next` / `Log In`): solid PayPal blue, white text,
  hover darkens to `#003087`.
- **Secondary** (`Create Account`): white fill with a blue border
  and blue text — the same shape, less visual weight.

Both share `border-radius: 24px` and `height: 48px` so they line up
as a pill-shaped pair.

## 9. Responsive tuning

Only one breakpoint is needed because the card already shrinks to fit:

```css
@media (max-width: 480px) {
    .card { padding: 2rem 1.5rem; border-radius: 16px; }
}
```

Below 480px the card uses tighter padding and a smaller corner radius
so it doesn't feel oversized on phones.

## 10. Safety / non-phishing guardrails

Because the page looks like a real login screen, the build deliberately
includes guardrails so it can't be repurposed for credential capture:

1. A persistent yellow banner at the top of the viewport states that
   the page is a UI recreation, not affiliated with PayPal, and does
   not submit credentials.
2. The `<form>` has no `action` attribute and the submit handler
   always calls `preventDefault()`.
3. No `fetch`, no `XMLHttpRequest`, no `localStorage`/`sessionStorage`,
   no analytics, no third-party scripts.
4. Footer copyright reads "Recreation. Not affiliated with PayPal."

## 11. Optional backend (`paypal_demo_db.py`)

For a slightly more realistic demo, `paypal_demo_db.py` adds a tiny
backend. It is stdlib-only (`sqlite3` + `http.server` + `hashlib`) and
binds only to the loopback interface.

### Schema

```sql
CREATE TABLE users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    email       TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    salt        BLOB    NOT NULL,
    pw_hash     BLOB    NOT NULL,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
```

`COLLATE NOCASE` makes email uniqueness and lookup case-insensitive,
matching how real services usually behave.

### Password storage

Passwords are hashed with `hashlib.scrypt` using a fresh 16-byte salt
per user. Verification uses `hmac.compare_digest` for constant-time
comparison, and authentication runs `scrypt` even for unknown emails
so timing doesn't leak which accounts exist.

```python
SCRYPT_N = 2 ** 14   # CPU/memory cost
SCRYPT_R = 8         # block size
SCRYPT_P = 1         # parallelism
```

### Parameterized SQL

Every query passes user input as a parameter, never as string
interpolation, so the SQLite driver handles escaping:

```python
conn.execute("SELECT salt, pw_hash FROM users WHERE email = ?", (email,))
```

### Local-only HTTP server

`serve()` runs a `http.server.HTTPServer` and refuses any host other
than `127.0.0.1`, `localhost`, or `::1`:

```python
if host not in ("127.0.0.1", "localhost", "::1"):
    raise ValueError("refusing to bind to non-loopback host for safety")
```

The handler exposes:

| Route | Method | Purpose |
| --- | --- | --- |
| `/` | GET | Serves `paypal-login.html` |
| `/api/register` | POST | Create a demo account |
| `/api/login` | POST | Verify demo credentials |

Static-file serving canonicalizes the path with `Path.resolve()` and
checks the result is still under the project root, so a request like
`/../../etc/passwd` cannot escape the directory.

### Front-end wiring

The form's submit handler only calls the API when the page is loaded
over HTTP from loopback:

```js
var apiEnabled = location.protocol === 'http:' &&
    (location.hostname === '127.0.0.1' || location.hostname === 'localhost');
```

Opened directly from disk (`file://`), the page falls back to the
original "Demo only — nothing submitted" behavior. When the API is
available, an unknown email auto-registers as a fresh demo account.

### CLI

```
python paypal_demo_db.py init
python paypal_demo_db.py register alice@example.com hunter22-demo
python paypal_demo_db.py login    alice@example.com hunter22-demo
python paypal_demo_db.py list
python paypal_demo_db.py serve --port 8000
```

### Tests

`tests/test_paypal_demo_db.py` covers:

- Salt uniqueness and password round-trips
- Insert/lookup with case-insensitive email
- Validation errors (short password, malformed email, duplicate email)
- CLI exit codes
- An end-to-end test that boots the server on an ephemeral port and
  hits `/api/register` and `/api/login` over HTTP
- A guard test that `serve(host="0.0.0.0")` is rejected

## File map

| File | Role |
| --- | --- |
| `paypal-login.html` | The page itself (HTML + CSS + JS) |
| `paypal_demo_db.py` | SQLite demo store + loopback HTTP server |
| `tests/test_paypal_demo_db.py` | Unit + integration tests |
| `plan.txt` | Planning document with design tokens and structure |
| `paypal-login-methods.md` | This file |
| `index.html` | Updated to link to the demo page |
