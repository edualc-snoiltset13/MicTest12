# Project To-Do Plan

A prioritized plan for MicTest12. The repo currently holds several independent pieces: the
Barber Booking Agent (the main app, with email templates and compression helpers), two
calculators, a web scraper, an image-analysis CLI, static HTML pages, and a gaming-platform
microservices plan document. The plan below is ordered so that correctness and CI gaps are
closed first, then the codebase is organized, then features are extended.

## Phase 1 — Fix CI and test gaps (highest priority)

- [ ] **Run all tests in CI.** `.github/workflows/tests.yml` runs
      `python -m unittest discover -s tests`, which misses the root-level
      `test_calculator.py` (5 tests) and `test_compression.py` (2 tests). Either move both
      files into `tests/` (preferred, one convention) or change the workflow to also
      discover from the repo root.
- [ ] **Add missing test coverage.** `web_scraper.py`, `email_template.py`, and
      `calculator.py`'s expression parser/REPL have no tests. Start with pure functions
      (HTML parsing, template rendering, tokenizer) — they need no network or SMTP.
- [ ] **Add a linter to CI.** A `ruff check` (or `flake8`) step catches drift cheaply across
      Python versions already in the matrix.

## Phase 2 — Organize the repository

- [ ] **Decide the repo's identity.** The README describes only the booking agent and the
      image analyzer, but half the files are unrelated demos. Either scope the repo to the
      booking agent and move demos to an `examples/` folder, or restructure into per-tool
      directories (`booking/`, `calculator/`, `scraper/`, `web/`).
- [ ] **Consolidate the two calculators.** `calculator.py` (expression REPL) and
      `simple_calculator.py` (class-based with memory/history) overlap; merge into one
      module with both interfaces, or document why both exist.
- [ ] **Update the README** to cover everything that ships: calculators, compression
      helpers, web scraper, email templates, the HTML pages, and a pointer to
      `GAMING_MICROSERVICES_PLAN.md`.
- [ ] **Clean up `page.html`** (an 11-line stub) — either grow it into a real page linked
      from `index.html`/`about.html` or delete it.

## Phase 3 — Booking agent improvements (the core app)

- [ ] **Wire compression into the agent.** `compression.py` says it exists "for the Barber
      Booking Agent," but `barber_booking_agent.py` never imports it. Use it to archive old
      `bookings.json` data, or move it to a generic utilities area.
- [ ] **Use the HTML email templates end-to-end.** Verify `email_template.py` renders are
      actually sent as multipart (text + HTML) by the agent's SMTP path, with a test using
      mocked SMTP.
- [ ] **Harden persistence.** Guard `bookings.json` reads against corruption (bad JSON →
      backup + fresh start rather than crash), and write atomically (temp file + rename).
- [ ] **Add non-interactive CLI flags** (e.g. `--list`, `--book ...`) so the agent is
      scriptable and testable beyond the interactive menu.

## Phase 4 — Stretch / product direction

- [ ] **Decide the fate of the gaming microservices plan.** It's a design doc unrelated to
      the code. Answer its own "Open Questions" section and start Phase 0 in a separate
      repo, or park it under `docs/`.
- [ ] **Web front-end for bookings.** `index.html`/`about.html` are static; a small
      stdlib `http.server`-based UI over the booking agent would tie the HTML and Python
      halves of the repo together.
- [ ] **Scraper output → analysis.** Add an example notebook or script that consumes the
      scraper's JSON/CSV output, since the scraper advertises "analysis-ready" records.

## Suggested order of attack

1. Phase 1 items — small, mechanical, immediately raise confidence in every later change.
2. The repo-identity decision in Phase 2 — it determines where everything else lands.
3. Phase 3 top-to-bottom — each item is independently shippable.
4. Phase 4 only after the above, and only the items that match where the project is headed.
