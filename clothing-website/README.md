# Théod — Clothing Website

A responsive, multi-page front-end for a modern clothing brand. Built with plain
HTML, CSS, and a small amount of vanilla JavaScript — no build step or
dependencies.

## Pages

| File | Description |
|------|-------------|
| `index.html` | Home page: hero, category grid, featured products, brand story, newsletter |
| `shop.html` | Product listing grid |
| `about.html` | Brand story and values |
| `contact.html` | Contact form and details |

## Shared assets

- `styles.css` — design system (colors, typography, layout) and all component styles
- `main.js` — mobile navigation toggle

## Running it

No server required. Open `index.html` in a browser, or serve the folder:

```bash
cd clothing-website
python3 -m http.server 8000
# then visit http://localhost:8000
```

## Notes

- Fully responsive (desktop, tablet, mobile) using CSS grid and flexbox.
- Product imagery is loaded from Unsplash via URL for demo purposes; swap in your
  own assets for production.
- Forms are front-end only and do not submit anywhere yet.
