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

## File map

| File | Role |
| --- | --- |
| `paypal-login.html` | The page itself (HTML + CSS + JS) |
| `plan.txt` | Planning document with design tokens and structure |
| `paypal-login-methods.md` | This file |
| `index.html` | Updated to link to the demo page |
