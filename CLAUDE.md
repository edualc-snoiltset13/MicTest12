# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository nature

This is a collection of small, independent Python scripts — not a single packaged project. There is no `requirements.txt`, `setup.py`, `pyproject.toml`, or virtual-env config: every script uses only the standard library and targets Python 3.7+ (CI matrix runs 3.9 / 3.10 / 3.11 / 3.12). Do not add third-party dependencies without a clear reason — "stdlib-only" is a stated property of this repo (see README and `about.html`).

The flagship script is the **Barber Booking Agent** (`barber_booking_agent.py`); the other modules (`calculator.py`, `simple_calculator.py`, `compression.py`, `web_scraper.py`, `analyze_image.py`) are unrelated standalone tools that happen to live in the same repo.

`GAMING_MICROSERVICES_PLAN.md` is a design document only — no code in this repo implements it.

## Common commands

Run the booking agent (interactive REPL):
```bash
python barber_booking_agent.py
```

Run individual scripts:
```bash
python calculator.py                 # arithmetic REPL
python calculator.py "2 + 3 * 4"     # one-shot eval
python web_scraper.py <url> [--format json|csv] [--output FILE]
ANTHROPIC_API_KEY=sk-ant-... python analyze_image.py path/to/image.jpg
```

### Tests

**Important:** test files live in two places and CI only picks up one of them.

```bash
# What CI runs (.github/workflows/tests.yml) — only discovers tests/ subdir:
python -m unittest discover -s tests -v

# Root-level tests (test_calculator.py, test_compression.py) are NOT in tests/
# and must be run explicitly:
python -m unittest test_calculator test_compression -v

# All tests in one go:
python -m unittest discover -s . -p 'test_*.py' -v

# Single test class or method:
python -m unittest tests.test_barber_booking_agent.SlotLogicTests
python -m unittest tests.test_barber_booking_agent.SlotLogicTests.test_taken_when_exact_match
```

If you add a new test for a root-level module, either put it under `tests/` (where CI will find it) or update `.github/workflows/tests.yml`.

## Architecture — Barber Booking Agent

The agent is split across two files plus a JSON data file:

- `barber_booking_agent.py` — all CLI flow, persistence, slot/booking logic, and SMTP sending.
- `email_template.py` — pure rendering layer; `render_booking_email(event, recipient_type, booking, previous=None)` returns `(subject, text_body, html_body)` for the three lifecycle events `confirmed` / `rescheduled` / `cancelled` and two recipient types `client` / `barber`. No I/O here.
- `bookings.json` — single source of truth, created on first save, gitignored. Shape: `{"barbers": {<name>: {slots, services, email}}, "bookings": [...]}`. The whole file is rewritten on every mutation via `save_bookings`.

Key contracts to preserve when editing:

- **`notify(...)`** is the single seam between business logic and side effects (console print + optional email). All booking flows funnel through it. When `event` and `booking` are passed, the email uses the HTML template; otherwise a plain-text fallback is sent. Don't bypass `notify` by calling `send_email_notification` directly from booking flows.
- **`send_email_notification`** is a no-op (returns `False`) unless **all** of `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, and a recipient address are set. `SMTP_FROM` is optional and defaults to `SMTP_USER`. Tests rely on this graceful degradation — keep the "missing env returns False, no exception" behavior.
- **Slot conflicts** are checked by `_is_slot_taken(data, barber, date, time_slot)` — a linear scan over `data["bookings"]`. Rescheduling mutates the booking dict in place (rather than delete + re-add), so any new field added to a booking will silently carry across reschedules.
- **Booking lifecycle events** (`confirmed`, `rescheduled`, `cancelled`) are referenced as string literals in both `barber_booking_agent.py` and `email_template.py` (`STATUS_STYLES`, `HEADLINES`, `intro_map`). Adding a new event means updating all three dicts in `email_template.py`.
- **Date/time formats**: dates are `YYYY-MM-DD`, slots are `HH:MM` (24-hr). `view_bookings` partitions upcoming vs. past with a string comparison against `datetime.now().strftime("%Y-%m-%d")` — this works only because of the lexicographic-friendly format.

The interactive flows (`register_barber`, `book_appointment`, `reschedule_booking`, …) read from `input()` directly, which is why tests mock `builtins.input` and `redirect_stdout` rather than calling smaller pure helpers. Prefer adding new logic to the existing helpers (`_select_barber`, `_select_date`, `_select_free_slot`, `_select_service`, `_select_booking`) so the same testing pattern keeps working.

## Other scripts — quick notes

- **`calculator.py`** — full shunting-yard expression evaluator (tokenize → RPN → eval). Supports `+ - * / // % **`, unary minus, `sqrt`/`abs`, parentheses. `evaluate(expr)` is the public entry. Operator metadata (`PRECEDENCE`, `RIGHT_ASSOC`, `BINARY_OPS`, `UNARY_OPS`, `FUNCTIONS`) lives at the top of the module; extending the calculator means updating those tables plus `TOKEN_RE`.
- **`simple_calculator.py`** — unrelated to `calculator.py`. A class-based `Calculator` with a memory register and history list, parsing a fixed `<a> <op> <b>` form. Don't unify the two without a reason; they're independent toys with different APIs.
- **`compression.py`** — `compress_file` / `decompress_file` stream through `shutil.copyfileobj` in 1 MiB chunks; `test_compression.py` asserts both the chunk size and that exactly two copy calls happen per round-trip. If you change the streaming approach, the streaming-memory test will need updating.
- **`web_scraper.py`** — stdlib-only scraper with a custom `HTMLParser`. Respects `robots.txt` by default (`--ignore-robots` to override) and rate-limits with `--delay`. Exit code is `1` only when **every** URL failed.
- **`analyze_image.py`** — minimal Anthropic Messages API client; runs entirely at import time (no `main()`), uses `claude-sonnet-4-6` and `anthropic-version: 2023-06-01`. Tests invoke it as a subprocess because of the import-time execution.

## CI

`.github/workflows/tests.yml` runs `python -m unittest discover -s tests -v` on Python 3.9–3.12. There is no lint/format step configured; don't claim "CI passes" based only on a local run that excludes root-level tests.
