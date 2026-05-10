# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Orientation

MicTest12 is a **collection of unrelated, single-file Python programs** that happen to share a repo. There is no package, no entry point, no shared framework. Treat each `.py` as standalone unless it explicitly imports another module — today the only intra-repo edge is `barber_booking_agent.py` → `email_template.py`.

The hard rule across everything here: **stdlib only**. The README advertises "no external dependencies", CI installs nothing, and there is deliberately no `requirements.txt` / `pyproject.toml` / `setup.py`. Use `urllib` instead of `requests`, `html.parser` instead of `beautifulsoup4`, `unittest`+`unittest.mock` instead of `pytest`+`responses`, and so on. If a task seems to need a third-party package, prefer expanding the stdlib approach over adding one.

## Commands

```bash
# Run the main app (interactive menu CLI)
python barber_booking_agent.py

# What CI runs — full suite under tests/
python -m unittest discover -s tests -v

# Narrow down to a module / class / single test
python -m unittest tests.test_barber_booking_agent
python -m unittest tests.test_barber_booking_agent.PersistenceTests
python -m unittest tests.test_barber_booking_agent.PersistenceTests.test_round_trip_preserves_all_fields
```

`test_calculator.py` and `test_compression.py` sit at the **repo root, not in `tests/`**, so `discover -s tests` skips them and CI never runs them. Run them by hand whenever you touch `calculator.py` or `compression.py`:

```bash
python -m unittest test_calculator test_compression
```

CI matrix (`.github/workflows/tests.yml`): Python 3.9 / 3.10 / 3.11 / 3.12. Stay 3.9-compatible — no `match` statements, no PEP 604 `X | Y` unions evaluated at runtime, no `dict[str, int]` generics outside `from __future__ import annotations`.

## Architecture

### `barber_booking_agent.py` — the main artifact

An interactive menu CLI. The in-memory state is the same dict written to `bookings.json`:

```python
{
  "barbers":  {name: {"slots": [...], "services": {name: price}, "email": ""}},
  "bookings": [{"barber", "client", "client_email", "date", "time",
                "service", "price", "booked_at"}, ...],
}
```

Things to know before editing it:

- **Persistence path is CWD-relative.** `save_bookings` rewrites `bookings.json` in the current directory after every mutation. The file is gitignored. Tests `chdir` into a temp dir to sandbox it; any new persisted file should follow the same convention or the test isolation breaks.
- **`notify()` is the only path to the user.** Both console output and email go through it. Pass `event` (`"confirmed"` | `"rescheduled"` | `"cancelled"`) plus the `booking` dict and you get the styled HTML email via `email_template.render_booking_email`. Omit them and you get a plain-text fallback. Don't add a parallel print-or-send path — extend `notify()` instead.
- **SMTP is opt-in and silent on failure.** Required env vars: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`; optional `SMTP_FROM` (defaults to `SMTP_USER`). If any required var is missing, `send_email_notification` returns `False` without raising — the app must remain fully usable without SMTP, and tests rely on that behavior.
- **Slot conflicts are exact-triple matches.** `_is_slot_taken` compares `(barber, date, time)` literally; there is no service duration, no overlap detection, no calendar arithmetic. Don't introduce one casually — it would invalidate the existing tests.

### `email_template.py`

Pure renderer that returns `(subject, text_body, html_body)`. Keyed off `(event, recipient_type)`. Adding a new event type means updating **all three** of `STATUS_STYLES`, `HEADLINES`, and the `intro_map` inside `render_booking_email` — a missing key will raise `KeyError` at send time, not at import.

### Other standalone scripts

| File | What it is | Watch out for |
|---|---|---|
| `calculator.py` | Shunting-yard infix→RPN evaluator + REPL | Operators, precedence, associativity, and functions are module-level dicts/sets — extend those rather than the parser. |
| `simple_calculator.py` | Class-based calculator with memory + history | Intentionally a separate exercise from `calculator.py`. Do not consolidate. |
| `compression.py` | Streaming gzip helpers | 1 MiB `CHUNK_SIZE` + `shutil.copyfileobj(..., length=chunk_size)` is what keeps multi-GB files from blowing memory. Keep edits streaming. |
| `web_scraper.py` | Stdlib HTML scraper (`html.parser.HTMLParser`) with `robots.txt` checks + rate limiting | Don't swap in `requests` / `beautifulsoup4`. |
| `analyze_image.py` | Minimal Claude vision CLI hitting `api.anthropic.com/v1/messages` via `urllib` | Default model `claude-sonnet-4-6`. Exit codes (`0` ok, `2` bad args / missing key, `3` image error, `4` API error, `5` network error) are part of the contract — `tests/test_analyze_image.py` asserts them. |
| `index.html`, `about.html` | Static marketing pages | Not served by any Python here. |
| `GAMING_MICROSERVICES_PLAN.md` | Standalone design doc | **Not** a spec for anything in this repo — don't try to implement it. |

## Conventions

- Tests are `unittest` + `unittest.mock` only. Mock outbound I/O at the stdlib boundary — e.g. `mock.patch("smtplib.SMTP")` for the booking agent, `mock.patch("urllib.request.urlopen")` for HTTP. Don't introduce `responses` / `requests-mock` / `pytest-mock`.
- When you change anything in the notification flow, run `tests/test_barber_booking_agent.py`. It asserts both the captured stdout (`redirect_stdout`) **and** the exact SMTP call shape — both will fail loudly if you skew either side.
- Persisted state belongs at CWD, not next to the module that writes it. This is what lets tests sandbox via `chdir`.
- Keep new scripts self-contained: a single file with a `main()` and a `if __name__ == "__main__":` guard, no shared utilities module.
