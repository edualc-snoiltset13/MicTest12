# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository nature

This repo is a collection of small, **independent standard-library-only Python scripts** rather than a single application. There is no package, no `requirements.txt`, no build step, and no shared framework — each top-level `.py` is its own program. Treat each module as standalone unless it explicitly imports from another (currently only `barber_booking_agent.py` → `email_template.py`).

The constraint that **everything must run on a stock Python ≥3.7 / 3.9 install with no `pip install`** is load-bearing. Any new dependency would break the README's "no external dependencies" promise and the CI matrix below. Reach for `urllib`, `unittest`, `unittest.mock`, `html.parser`, `gzip`, `smtplib`, `argparse`, etc. before suggesting a third-party package.

## Commands

Run the main app:
```bash
python barber_booking_agent.py
```

Run the full test suite (matches what CI runs):
```bash
python -m unittest discover -s tests -v
```

Run a single test module / class / method:
```bash
python -m unittest tests.test_barber_booking_agent
python -m unittest tests.test_barber_booking_agent.PersistenceTests
python -m unittest tests.test_barber_booking_agent.PersistenceTests.test_round_trip_preserves_all_fields
```

The root-level `test_calculator.py` and `test_compression.py` are **not** picked up by `discover -s tests` and **not** run in CI. Run them explicitly when touching `calculator.py` or `compression.py`:
```bash
python -m unittest test_calculator test_compression
```

CI (`.github/workflows/tests.yml`) runs the `tests/` discover on Python 3.9, 3.10, 3.11, and 3.12 — keep code compatible with 3.9 syntax.

## Architecture notes

### Barber booking agent (the main artifact)

`barber_booking_agent.py` is an interactive CLI with a single in-memory dict shape that is also the on-disk format:
```python
{"barbers": {name: {"slots": [...], "services": {name: price}, "email": ""}},
 "bookings": [{"barber", "client", "client_email", "date", "time",
               "service", "price", "booked_at"}, ...]}
```
- Persistence is a plain `bookings.json` written via `save_bookings` after every mutation. The file is gitignored.
- `notify()` is the single funnel for both console output and email. When called with `event` + `booking`, it delegates to `email_template.render_booking_email()` for HTML; otherwise it falls back to plain text. New flows that produce notifications should pass `event` (`"confirmed"` | `"rescheduled"` | `"cancelled"`) and the booking dict so they get the styled email automatically.
- SMTP is opt-in via `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM` env vars. If any required var is missing, `send_email_notification` returns `False` silently — the app must remain fully functional without SMTP, and tests rely on this.
- Slot conflicts are detected only by `_is_slot_taken` (exact `(barber, date, time)` match). There is no duration model — services don't have a length.

### Other scripts (independent)

- `calculator.py` — shunting-yard infix→RPN expression evaluator with a REPL. Tokens, precedence, and right-associativity are declared as module-level dicts/sets; extend those rather than the parser when adding operators or functions.
- `simple_calculator.py` — unrelated class-based calculator with memory + history. Do not consolidate with `calculator.py`; they're intentionally different exercises.
- `compression.py` — streaming gzip helpers. The 1 MiB `CHUNK_SIZE` and `shutil.copyfileobj(..., length=chunk_size)` pattern exist so multi-GB files don't blow memory; preserve streaming when editing.
- `web_scraper.py` — stdlib-only HTML scraper using `html.parser.HTMLParser`, with built-in `robots.txt` checking and rate limiting. Don't swap in `requests` or `beautifulsoup4`.
- `analyze_image.py` — minimal Claude vision CLI hitting `https://api.anthropic.com/v1/messages` via `urllib`. Default model is `claude-sonnet-4-6`. Documented exit codes (`0/2/3/4/5`) are part of the contract; tests in `tests/test_analyze_image.py` assert them.
- `email_template.py` — pure renderer for `(subject, text_body, html_body)`. Adding a new event type means extending **both** `STATUS_STYLES` and `HEADLINES` (and the `intro_map` inside `render_booking_email`) — they're keyed on `(event, recipient_type)`.
- `index.html` / `about.html` — static marketing pages. Not served by any Python here.
- `GAMING_MICROSERVICES_PLAN.md` — design doc unrelated to the running code; do not treat it as a spec for anything in this repo.

## Conventions

- **Stdlib only.** Don't add `requirements.txt` or import non-stdlib packages.
- **Persistence files live at CWD**, not next to the module — `barber_booking_agent`'s tests `chdir` into a temp dir to isolate `bookings.json`. New persisted files should follow the same pattern so tests can sandbox them.
- Tests use `unittest` + `unittest.mock` only. SMTP is mocked via `mock.patch("smtplib.SMTP")`; follow that pattern for any new network I/O rather than introducing `responses`/`requests-mock`.
- When editing notification flows, run `tests/test_barber_booking_agent.py` — it asserts both the console output (captured via `redirect_stdout`) and the SMTP call shape.
