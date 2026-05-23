# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository shape

This is **not** a single application — it is a collection of mostly-independent
Python scripts/tools that happen to share a repo. The only intra-repo import is
`barber_booking_agent.py` → `email_template.py`. Everything else
(`calculator.py`, `simple_calculator.py`, `compression.py`, `analyze_image.py`,
`web_scraper.py`) stands alone.

Hard constraint across the whole repo: **standard library only, no third-party
dependencies**. There is no `requirements.txt`, `pyproject.toml`, or
`setup.py`, and CI does not install anything. New code should preserve this.

## Running tests

```bash
# CI-equivalent run (this is what .github/workflows/tests.yml does)
python -m unittest discover -s tests -v

# Run a single test module / class / method
python -m unittest tests.test_barber_booking_agent
python -m unittest tests.test_barber_booking_agent.EmailNotificationTests
python -m unittest tests.test_barber_booking_agent.EmailNotificationTests.test_smtp_called_when_env_complete
```

**Gotcha — split test layout.** Tests live in two places:

- `tests/test_barber_booking_agent.py`, `tests/test_analyze_image.py` — discovered by CI.
- `test_calculator.py`, `test_compression.py` at the repo **root** — **not** picked up by `discover -s tests` and therefore not run in CI. Run them explicitly:
  ```bash
  python -m unittest test_calculator test_compression
  ```
  If you change `calculator.py` or `compression.py`, run the matching root-level test file manually; otherwise breakage will not show up in CI.

CI matrix: Python 3.9 / 3.10 / 3.11 / 3.12 (`.github/workflows/tests.yml`). Anything that requires a newer Python feature will break the 3.9 leg.

## Running the apps

```bash
python barber_booking_agent.py     # interactive CLI menu
python calculator.py               # REPL
python calculator.py "2 + 3 * 4"   # one-shot expression
python analyze_image.py path/to/image.jpg              # needs ANTHROPIC_API_KEY
python web_scraper.py https://example.com [--format json|csv] [--output FILE]
```

## Barber booking agent — things to know

`barber_booking_agent.py` is the largest module; `email_template.py` is its
HTML/text email renderer.

- **Persistence is implicit CWD state.** `load_bookings()` / `save_bookings()`
  read and write `bookings.json` in the **current working directory** — there
  is no path argument. Tests that touch persistence `chdir` to a temp dir in
  `setUp` and back in `tearDown` (see `PersistenceTests`, `RegisterBarberTests`
  in `tests/test_barber_booking_agent.py`). Do the same for any new
  persistence-touching test, or `bookings.json` will leak into the repo root.
  `bookings.json` is gitignored.

- **Data shape** (single source of truth — keep migrations in lockstep):
  ```python
  {
    "barbers": {
      "<name>": {"slots": ["HH:MM", ...], "services": {"<name>": price}, "email": "..."}
    },
    "bookings": [
      {"barber", "client", "client_email", "date" (YYYY-MM-DD),
       "time" (HH:MM), "service", "price", "booked_at" (ISO)}
    ]
  }
  ```

- **Notifications have two layers.** `notify()` always prints to the console;
  it sends email only when `send_email_notification()` finds all of
  `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS` in `os.environ` *and* a
  recipient address. With no SMTP env vars, the app works fine — emails are
  silently skipped. Tests mock `smtplib.SMTP` rather than hitting a server.
  Optional `SMTP_FROM` overrides the sender; otherwise `SMTP_USER` is used.

- **Rich emails vs. plain text.** When `notify()` is called with both `event`
  (`"confirmed"` | `"rescheduled"` | `"cancelled"`) and `booking`, it routes
  through `email_template.render_booking_email()` which returns
  `(subject, text_body, html_body)` and is sent as `multipart/alternative`.
  Without those kwargs it falls back to a plain-text message. New booking
  lifecycle events need entries in `STATUS_STYLES`, `HEADLINES`, and
  `intro_map` in `email_template.py` to render correctly.

- **Slot conflict logic** is centralized in `_is_slot_taken()`. Booking and
  rescheduling both go through `_select_free_slot()` which filters the
  barber's slots through this predicate — don't reimplement the check
  ad hoc.

## analyze_image.py — testing constraint

`analyze_image.py` is intentionally script-shaped: **all logic runs at import
time** (top-level `if`/`sys.exit` chain, no `main()` function). That means it
**cannot be unit-tested by importing it** — `tests/test_analyze_image.py`
exercises it via `subprocess.run([sys.executable, SCRIPT, ...])` with a
controlled `env`. Preserve that pattern if you add tests; don't refactor the
script into functions just to make it importable unless that's the goal of
the change.

The supported-format table (`MEDIA` dict) is asserted against by
`MediaMapTests.test_readme_supported_formats_match_script` — if you add or
remove an extension, update both the dict and the README "Supported formats"
line.

## Unrelated documents

`GAMING_MICROSERVICES_PLAN.md` is a standalone architecture design doc — it
does not correspond to any code in this repo. Treat it as a reference
document, not a roadmap for the current codebase. `index.html` / `about.html`
are static marketing pages for the booking agent; they have no build step.
