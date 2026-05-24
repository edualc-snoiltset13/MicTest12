# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a small Python "playground" repo containing several **independent, standard-library-only** scripts. There is no package, no `requirements.txt`, no build step — every file is run directly with `python <script>.py`. Python 3.7+ is required; CI tests against 3.9, 3.10, 3.11, and 3.12.

The headline app (and the subject of `README.md` / `index.html` / `about.html`) is the **Barber Booking Agent**. The other scripts (`calculator.py`, `simple_calculator.py`, `compression.py`, `web_scraper.py`, `analyze_image.py`) are unrelated standalone utilities that happen to live in the same repo. `GAMING_MICROSERVICES_PLAN.md` is a design document with no associated code.

## Common Commands

```bash
# Run the barber booking CLI (interactive menu)
python barber_booking_agent.py

# Run the CI test suite (only tests under tests/ — this is what GitHub Actions runs)
python -m unittest discover -s tests -v

# Root-level tests are NOT picked up by `discover -s tests` — run them directly:
python -m unittest test_calculator test_compression

# Run a single test class or method
python -m unittest tests.test_barber_booking_agent.PersistenceTests
python -m unittest tests.test_barber_booking_agent.PersistenceTests.test_load_creates_default

# Other entry points
python calculator.py "2 + 3 * 4"                # one-shot expression
python calculator.py                             # REPL
python web_scraper.py https://example.com --format json
python analyze_image.py photo.png                # needs ANTHROPIC_API_KEY
```

There is no linter or formatter configured for this repo — don't add one unless asked.

## Test Layout Gotcha

Tests live in **two places** and the split matters:

- `tests/` — discovered by CI (`.github/workflows/tests.yml` runs only `unittest discover -s tests`). Contains tests for `barber_booking_agent.py` and `analyze_image.py`. These use `sys.path.insert(0, ...)` to import from the project root.
- `test_calculator.py` and `test_compression.py` at the repo root — **not run by CI**. They are invoked manually with `python -m unittest test_calculator test_compression`.

When adding tests for a new top-level module, put them in `tests/` so CI picks them up.

## Barber Booking Agent Architecture

The booking app is a single-process CLI with three collaborating modules:

- **`barber_booking_agent.py`** — interactive menu, all booking/barber state mutations, and the `notify()` dispatcher. State lives entirely in one dict `{"barbers": {...}, "bookings": [...]}` that is loaded from and re-saved to `DATA_FILE = "bookings.json"` on every mutation. The file is gitignored.
- **`email_template.py`** — pure rendering of `(subject, text_body, html_body)` triples for the three lifecycle events (`confirmed`, `rescheduled`, `cancelled`) × two recipient types (`client`, `barber`). No I/O. `barber_booking_agent.notify()` calls `render_booking_email()` when it has an `event` + `booking`, falls back to plain text otherwise.
- **SMTP delivery** — `send_email_notification()` reads `SMTP_HOST/PORT/USER/PASS` (and optional `SMTP_FROM`) from the environment. If any is missing it silently returns `False` and the console notification path still works. Tests mock `smtplib.SMTP` to verify the email path without a real server.

When adding a new lifecycle event, you must update three things in lockstep: the `notify()` call site in `barber_booking_agent.py`, the `STATUS_STYLES` and `HEADLINES` maps in `email_template.py`, and the `intro_map` in `render_booking_email()`.

## Conventions

- **Standard library only.** Don't add third-party dependencies — the README, the about page, and the test suites all explicitly advertise this. If you need something non-trivial, implement it (see `calculator.py`'s shunting-yard parser, `web_scraper.py`'s `HTMLParser` subclass).
- **Single-file scripts.** Each utility is meant to be runnable as `python <file>.py` with `if __name__ == "__main__": main()`. Don't split them into packages.
- **Persistence is just JSON on disk.** `bookings.json` is the source of truth for the booking app. Tests `chdir` into a temp directory and rebind `bba.DATA_FILE` to isolate state.
- The `analyze_image.py` script targets `claude-sonnet-4-6` by default and uses `urllib.request` directly against `https://api.anthropic.com/v1/messages` — keep it dependency-free.
