# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository shape

This is a **collection of mostly-independent Python scripts**, not one cohesive application. The headline project is the barber booking agent; the other scripts (`calculator.py`, `simple_calculator.py`, `compression.py`, `web_scraper.py`, `analyze_image.py`) share the repo but do not import each other and have their own tests. `GAMING_MICROSERVICES_PLAN.md` is a standalone design doc — there is no code behind it.

**Everything is stdlib-only.** There is no `requirements.txt`, `pyproject.toml`, `setup.py`, or virtualenv. Do not add a dependency without an explicit reason — the README and CI both rely on "no pip install needed."

## Commands

```bash
# Run the discovered test suite (this is what CI runs)
python -m unittest discover -s tests -v

# Run a single test module / class / method
python -m unittest tests.test_barber_booking_agent
python -m unittest tests.test_barber_booking_agent.PersistenceTests
python -m unittest tests.test_barber_booking_agent.PersistenceTests.test_round_trip_preserves_all_fields

# Root-level tests are NOT discovered by `discover -s tests` — run them explicitly:
python -m unittest test_calculator
python -m unittest test_compression

# Run the apps
python barber_booking_agent.py           # interactive menu
python calculator.py "2 + 3 * 4"         # one-shot, or no args for REPL
python web_scraper.py https://example.com --format json
python analyze_image.py path/to/image.jpg   # requires ANTHROPIC_API_KEY
```

There is no linter or formatter configured. CI (`.github/workflows/tests.yml`) only runs `unittest discover -s tests -v` on Python 3.9–3.12.

## Test layout gotcha

Tests live in **two locations** and they are not equivalent:

- `tests/` — discovered by CI: `test_barber_booking_agent.py`, `test_analyze_image.py`
- Repo root — **not run by CI**: `test_calculator.py`, `test_compression.py`

If you change `calculator.py` or `compression.py`, run their tests by hand — green CI does not prove they pass. If you add a new test file, put it under `tests/` so CI picks it up.

The booking-agent tests insert the repo root into `sys.path` (`tests/test_barber_booking_agent.py:17`) so they can import the top-level modules; do the same in any new `tests/`-level test that imports from the repo root.

## Barber booking agent — architecture

The agent is a single-process interactive CLI with a dict-shaped in-memory state, persisted to `bookings.json` after every mutation. Knowing the shape unlocks most of the code:

```python
data = {
    "barbers": {
        "<name>": {"slots": ["09:00", ...], "services": {"Haircut": 25.0}, "email": "..."},
    },
    "bookings": [
        {"barber", "client", "client_email", "date", "time", "service", "price", "booked_at"},
    ],
}
```

- `barber_booking_agent.py` owns the menu loop and all mutations. Each top-level action (`register_barber`, `book_appointment`, `cancel_booking`, `reschedule_booking`, …) takes `data`, mutates it in place, calls `save_bookings(data)`, then calls `notify(...)` for both barber and client. Adding a new flow means following that same pattern — mutate, persist, notify both sides — and wiring it into `MENU` + the `main()` if/elif chain.
- `_select_barber`, `_select_date`, `_select_free_slot`, `_select_service`, `_select_booking` are the prompt helpers; each returns `None` on bad input and prints its own error, so callers just early-return when they get `None`. Reuse these instead of writing new input loops.
- `_is_slot_taken(data, barber, date, time)` is the only conflict check — slot freeness is computed on the fly from `data["bookings"]`, not stored.
- `notify(...)` does **both** console output and (optional) email. When `event` and `booking` are passed, it delegates to `email_template.render_booking_email` for a real HTML email; otherwise it sends a plain-text fallback. SMTP is fully optional and gated by env vars — `send_email_notification` returns `False` (not raises) when SMTP is not configured, and the agent keeps working.
- `email_template.py` is a pure renderer: `render_booking_email(event, recipient_type, booking, previous=None) -> (subject, text_body, html_body)`. It has no I/O. `event` is one of `confirmed | rescheduled | cancelled`; `recipient_type` is `client | barber`; `previous` is only used for reschedules. Keep it dependency-free.

## `analyze_image.py` — heads up

The script is a deliberately minimal ~30 lines (see commit history: "Shrink analyze_image.py to a minimal script"). The README advertises richer flags (`--model`, `--max-tokens`, `--json`, exit codes 2/3/4/5) that **are not implemented in the current script** — only `<image> [prompt]` and `-h/--help` work. If a task asks you to touch this file, either implement those flags or update the README; do not assume they exist.

Tests for it (`tests/test_analyze_image.py`) run the script via `subprocess` because everything happens at import time. They never hit the network — they only exercise arg parsing, the API-key check, and the format-extension table. Keep that contract: if you refactor `analyze_image.py`, the supported-extension map and the "ANTHROPIC_API_KEY"/"unsupported format"/"Usage" error strings are load-bearing for the tests.

## Reading timeline (start here if you're new to the repo)

Read in this order — each step builds on the previous and skips files that aren't load-bearing for understanding the code.

1. **`README.md`** — user-facing pitch and CLI surface for the booking agent and `analyze_image.py`. Sets expectations; note the gap between what it promises for `analyze_image.py` and what's implemented (see "heads up" above).
2. **`barber_booking_agent.py`** — top to bottom. The section banners (`── Persistence ──`, `── Notifications ──`, `── Barber management ──`, `── Booking logic ──`, `── Main menu ──`) are the file's natural reading order. By the end you understand the data shape, the mutate→save→notify pattern, and the menu loop.
3. **`email_template.py`** — short, pure renderer. Read after the agent so you know what `notify(..., event=, booking=)` is feeding it.
4. **`tests/test_barber_booking_agent.py`** — the executable spec. The `_sample_data()` fixture at the top is the canonical example of the `data` dict; the test classes mirror the agent's sections (Persistence, SlotLogic, EmailNotification, Notify, ViewBookings, Search, RegisterBarber).
5. **`.github/workflows/tests.yml`** — confirms CI only runs `unittest discover -s tests -v`. This is why the root-level `test_calculator.py` / `test_compression.py` gotcha matters.
6. **`analyze_image.py`** + **`tests/test_analyze_image.py`** — ~30-line script and its subprocess-based tests. Read together; the tests document the script's contract better than the script does.
7. **The standalone scripts**, only as needed:
   - `calculator.py` — shunting-yard infix evaluator with a REPL. Self-contained.
   - `simple_calculator.py` — class-based `Calculator` with history; unrelated to `calculator.py`.
   - `compression.py` — gzip streaming helpers (`compress_file` / `decompress_file`).
   - `web_scraper.py` — stdlib HTML scraper with robots.txt handling and JSON/CSV output.
8. **`index.html`, `about.html`** — static marketing pages. Not wired to the Python code; safe to skim or ignore unless your task touches them.
9. **`GAMING_MICROSERVICES_PLAN.md`** — design doc for a hypothetical gaming platform. No code behind it. Read only if a task references it.

## Conventions worth preserving

- **Standard library only.** Don't introduce third-party packages.
- **Persist after every mutation.** The booking agent never batches writes; tests rely on `bookings.json` being current.
- **Notify both sides.** Any booking-state change emits two `notify(...)` calls (barber + client) with matching `event=` values. Tests for new flows should assert both.
- **Email is optional, never required.** Guard SMTP behind env-var presence and return `False` on failure instead of raising — see `send_email_notification` in `barber_booking_agent.py`.
- `.gitignore` excludes `bookings.json` and `__pycache__/`. Don't commit the data file; treat it as user state.
