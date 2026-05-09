# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A grab-bag of **independent, stdlib-only Python scripts** — not a package or application. Each top-level `.py` is its own program. The only intra-repo import today is `barber_booking_agent.py` → `email_template.py`.

The "no `pip install` ever" rule is load-bearing: the README promises it, and CI installs nothing. Reach for `urllib`, `unittest`, `unittest.mock`, `html.parser`, `gzip`, `smtplib`, `argparse` before introducing any third-party dependency. Do not add a `requirements.txt`, `pyproject.toml`, or `setup.py`.

## Commands

```bash
# Run the main app
python barber_booking_agent.py

# Full test suite (exactly what CI runs)
python -m unittest discover -s tests -v

# A single module / class / method
python -m unittest tests.test_barber_booking_agent
python -m unittest tests.test_barber_booking_agent.PersistenceTests
python -m unittest tests.test_barber_booking_agent.PersistenceTests.test_round_trip_preserves_all_fields
```

The root-level `test_calculator.py` and `test_compression.py` live **outside** `tests/`, so `discover -s tests` does not pick them up and CI does not run them. Invoke them explicitly when touching `calculator.py` or `compression.py`:

```bash
python -m unittest test_calculator test_compression
```

CI (`.github/workflows/tests.yml`) runs the suite on Python 3.9, 3.10, 3.11, 3.12 — keep code 3.9-syntax-compatible (no `match`, no `X | Y` annotations at runtime, etc.).

## Architecture

### Barber booking agent (the main artifact)

`barber_booking_agent.py` drives an interactive menu CLI. The in-memory state and on-disk JSON share one shape:

```python
{
  "barbers":  {name: {"slots": [...], "services": {name: price}, "email": ""}},
  "bookings": [{"barber", "client", "client_email", "date", "time",
                "service", "price", "booked_at"}, ...],
}
```

Key invariants:

- `bookings.json` is rewritten by `save_bookings` after every mutation. It lives at CWD (gitignored). Tests `chdir` into a temp dir to isolate it — any new persisted file should do the same.
- `notify()` is the **single funnel** for both console output and email. Pass `event` (`"confirmed"` | `"rescheduled"` | `"cancelled"`) and the booking dict and you get the styled HTML email automatically; omit them and you get a plain-text fallback.
- SMTP is opt-in via `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM`. If any required var is missing, `send_email_notification` returns `False` silently — the app must keep working without SMTP, and tests rely on this.
- Slot conflicts are detected only by `_is_slot_taken` on an exact `(barber, date, time)` triple. There is no service-duration model.

### Email template (`email_template.py`)

Pure renderer that returns `(subject, text_body, html_body)`. Adding a new event type requires updating **all** of `STATUS_STYLES`, `HEADLINES`, and the `intro_map` inside `render_booking_email` — they're keyed on `(event, recipient_type)` and a missing key will `KeyError`.

### Other standalone scripts

- `calculator.py` — shunting-yard infix→RPN evaluator + REPL. Operators, precedence, right-associativity, and functions are module-level dicts/sets; extend those rather than the parser when adding ops.
- `simple_calculator.py` — class-based calculator with memory + history. Intentionally separate from `calculator.py`; do not consolidate.
- `compression.py` — streaming gzip helpers. The 1 MiB `CHUNK_SIZE` + `shutil.copyfileobj(..., length=chunk_size)` pattern exists so multi-GB files don't blow memory; keep edits streaming.
- `web_scraper.py` — stdlib HTML scraper via `html.parser.HTMLParser`, with `robots.txt` checks and rate limiting. Do not swap in `requests`/`beautifulsoup4`.
- `analyze_image.py` — minimal Claude vision CLI hitting `https://api.anthropic.com/v1/messages` via `urllib`. Default model: `claude-sonnet-4-6`. The exit codes (`0` ok, `2` bad args / missing key, `3` image error, `4` API error, `5` network error) are part of the contract — `tests/test_analyze_image.py` asserts them.
- `index.html`, `about.html` — static marketing pages, not served by anything here.
- `GAMING_MICROSERVICES_PLAN.md` — standalone design doc; **not** a spec for anything in this repo.

## Conventions

- Tests use `unittest` + `unittest.mock` only. Mock SMTP with `mock.patch("smtplib.SMTP")`; follow that pattern for any new outbound I/O rather than reaching for `responses` / `requests-mock`.
- When editing notification flows, run `tests/test_barber_booking_agent.py` — it asserts both the captured stdout (`redirect_stdout`) and the SMTP call shape.
- Persisted state belongs at CWD, not next to the module, so tests can sandbox it via `chdir`.
