# Portfolio Webpage — Project Overview

A simple, self-contained portfolio site built as a single HTML file with no
external dependencies. This document describes what the page contains, how it
is structured, and how to work with it.

## Project Summary

`portfolio.html` is a single-page personal portfolio for a fictional developer
("Jane Doe"). It demonstrates the core building blocks of a static webpage:
semantic headings, a sticky navigation bar, embedded images, a responsive
project grid, and a contact form with built-in HTML5 validation. All styling
lives in an inline `<style>` block and all images are inline SVG data URIs, so
the page renders correctly offline — just open the file in a browser.

## Features

- **Navigation**
  - Sticky top bar that stays visible while scrolling
  - Anchor links to each section:
    - Home
    - About
    - Projects
    - Contact
- **Content sections**
  - Hero with an `h1` heading and subtitle
  - About section with a circular profile image
  - Projects grid with three cards, each containing:
    - A thumbnail image
    - A title and short description
- **Contact form**
  - Labeled fields:
    - Name (required)
    - Email (required, validated as an email address)
    - Subject (optional)
    - Message (required)
  - Submit button with hover styling

## Page Structure

| Section  | Anchor      | Key elements                                  |
| -------- | ----------- | --------------------------------------------- |
| Home     | `#home`     | `h1` heading, subtitle                        |
| About    | `#about`    | Profile image, bio paragraph                  |
| Projects | `#projects` | CSS grid of three project cards               |
| Contact  | `#contact`  | Form with name, email, subject, message       |
| Footer   | —           | Copyright notice                              |

## Usage

No build step or server is required. Open the file directly:

```bash
# From the repository root
open portfolio.html        # macOS
xdg-open portfolio.html    # Linux

# Or serve it locally if you prefer
python3 -m http.server 8000
# then visit http://localhost:8000/portfolio.html
```

## Customization Notes

Replace the "Jane Doe" placeholder name, bio text, and project descriptions
with real content. The SVG data-URI images can be swapped for real photos by
pointing each `src` at an image file, and the accent color can be changed by
searching the stylesheet for `#c9b458`.
