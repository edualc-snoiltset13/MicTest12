# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository shape

This repo is a small grab-bag of **standard-library-only Python utilities**, organized around a primary CLI app (the Barber Booking Agent) plus several independent scripts. There is no `requirements.txt`, no virtualenv setup, and no package manager — every module must remain importable on a clean Python 3.7+ install.

Top-level scripts and what they are:

- `barber_booking_agent.py` — interactive CLI for managing barber appointments. The "main" app. Imports `email_template`.
- `email_template.py` — pure-function HTML/text email renderer used by the booking agent. No side effects, no I/O.
- `analyze_image.py` — one-shot CLI that calls the Anthropic Messages API directly over `urllib` (no SDK). Runs everything at import time.
- `calculator.py` — shunting-yard arithmetic evaluator + REPL.
- `simple_calculator.py` — class-based calculator with history (separate from `calculator.py`).
- `compression.py` — streaming gzip helpers (chunked, memory-bounded).
- `web_scraper.py` — stdlib HTML scraper that respects `robots.txt` by default.
- `index.html`, `about.html` — static brochure pages for the booking agent.
- `GAMING_MICROSERVICES_PLAN.md` — architecture planning doc, **unrelated to the code in this repo**. Don't treat it as a spec for anything here.

## Commands

The project has no build step. Everything runs directly with `python`.

**Run the booking agent CLI:**
```bash
python barber_booking_agent.py
```

**Run the full test suite (what CI runs):**
```bash
python -m unittest discover -s tests -v
```

**Run a single test module / class / method:**
```bash
python -m unittest tests.test_barber_booking_agent -v
python -m unittest tests.test_barber_booking_agent.SlotLogicTests
python -m unittest tests.test_barber_booking_agent.SlotLogicTests.test_taken_when_exact_match
```

**Root-level test files (`test_calculator.py`, `test_compression.py`) are NOT picked up by `discover -s tests`** and are not run in CI. Run them directly when touching those modules:
```bash
python -m unittest test_calculator test_compression -v
```

There is no linter or formatter configured; CI only runs unittest.

## Architecture notes

**Booking agent state model.** `barber_booking_agent.py` persists a single dict `{"barbers": {...}, "bookings": [...]}` to `bookings.json` in the current working directory (gitignored). The file is rewritten in full on every mutation via `save_bookings()`. Tests that exercise persistence `chdir` into a temp directory in `setUp` so they don't clobber a real `bookings.json` — follow the same pattern when adding tests that touch disk.

**Slot conflict logic** lives in the single helper `_is_slot_taken(data, barber, date, time_slot)`. Any new booking/reschedule path must go through it.

**Notification fan-out.** `notify()` always prints to the console; email is **opt-in** via SMTP env vars (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, optional `SMTP_FROM`). When any required var is missing or the recipient address is empty, `send_email_notification()` returns `False` silently — the CLI continues to work. Tests mock `smtplib.SMTP` and patch `os.environ` with `clear=True` to control this path.

**Email rendering is decoupled.** `email_template.render_booking_email(event, recipient_type, booking, previous=None)` returns `(subject, text_body, html_body)` and is pure. The event vocabulary is exactly `{"confirmed", "rescheduled", "cancelled"}` × `{"client", "barber"}` — these keys are used as tuple lookups in `HEADLINES` / `STATUS_STYLES` / `intro_map`, so adding an event type requires updating all three tables.

**`analyze_image.py` is intentionally a script, not a module.** It executes at import time and `sys.exit`s on bad args. The tests in `tests/test_analyze_image.py` invoke it via `subprocess` for exactly this reason — don't refactor it into importable functions without also rewriting those tests. The supported-format table (`MEDIA`) is asserted against by `MediaMapTests.test_readme_supported_formats_match_script`.

## Conventions to preserve

- **Stdlib only.** No third-party imports anywhere. Tests rely on `unittest`, `unittest.mock`, `subprocess`, `tempfile`. If a feature seems to need a library, prefer extending the existing stdlib approach (e.g. `urllib.request` over `requests`, `html.parser.HTMLParser` over `beautifulsoup4`).
- **Python 3.7+ compatibility.** CI matrix tests 3.9–3.12, but the README pins 3.7+ as the floor. Avoid 3.10+-only syntax (match statements, `X | Y` type unions in runtime code) unless guarded.
- **Tests `sys.path.insert` the project root** (see `tests/test_barber_booking_agent.py` line 17). New test files under `tests/` should do the same so they work regardless of where unittest is invoked from.
- `bookings.json`, `__pycache__/`, and `*.pyc` are gitignored — don't commit generated state.
