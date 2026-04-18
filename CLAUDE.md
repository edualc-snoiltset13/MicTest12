# CLAUDE.md

Guidance for AI assistants working in this repository.

## Repository overview

A single-file Python CLI that manages barber appointment bookings with console and optional SMTP email notifications. No external dependencies — standard library only, Python 3.7+.

## Layout

```
.
├── README.md                  User-facing docs (install, usage, env vars)
├── barber_booking_agent.py    Entire application (CLI, persistence, notifications)
└── bookings.json              Runtime data file (created on first save; git-ignored in practice, not tracked)
```

There is no `src/`, package layout, test suite, build system, or dependency manifest. Do not introduce one unless the task requires it.

## Running

```bash
python barber_booking_agent.py
```

The script is interactive (`input()`-driven menu). It cannot be exercised non-interactively without refactoring.

## Code structure (`barber_booking_agent.py`)

Organized by comment-banner sections — keep this structure when editing:

1. **Persistence** — `load_bookings`, `save_bookings`. JSON file at `DATA_FILE = "bookings.json"`.
2. **Notifications** — `send_email_notification` (SMTP via env vars), `notify` (console + optional email).
3. **Barber email helper** — `_barber_email`.
4. **Barber management** — `register_barber`, `list_barbers`.
5. **Booking logic** — private prompt helpers (`_select_barber`, `_select_date`, `_select_free_slot`, `_select_service`, `_select_booking`, `_is_slot_taken`) and public commands (`book_appointment`, `view_bookings`, `cancel_booking`, `reschedule_booking`, `search_bookings`).
6. **Main menu** — `MENU` string and `main()` dispatcher.

### Data shape

`load_bookings()` returns `{"barbers": {...}, "bookings": [...]}`.

- `barbers[name]` → `{"slots": ["HH:MM", ...], "services": {name: price}, "email": str}`
- Each booking → `{"barber", "client", "client_email", "date" (YYYY-MM-DD), "time" (HH:MM), "service", "price", "booked_at" (ISO)}`

Any new field must be read defensively (`.get(...)` with a default) so older `bookings.json` files still load.

### Formats

- Date: `YYYY-MM-DD`, validated with `datetime.strptime(..., "%Y-%m-%d")`.
- Time slot: `HH:MM` (24-hour), validated with `datetime.strptime(..., "%H:%M")`.
- Price: `round(float(x), 2)`, displayed as `${price:.2f}`.

### Notifications

`notify(recipient_type, name, message, email=None)` prints to console and attempts email if SMTP env vars are set (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, optional `SMTP_FROM`). Email failures are caught and printed — they must never block the flow. When adding a new user-facing action (booking change, cancellation, etc.), notify **both** the barber and the client.

## Conventions

- Module-level docstring at the top; short docstrings on each public function.
- Section banners use `# ── Title ──────...` — keep them when adding related functions.
- Private helpers are prefixed with `_`.
- User input is always `.strip()`-ed; empty/invalid input prints a message and returns early (no exceptions raised to `main`).
- After any mutation to `data`, call `save_bookings(data)` before notifying.
- Menu choices are string-compared (`"1"`, `"2"`, ...). Adding a new command means: write the function, add a `MENU` line, add an `elif` in `main()`, and renumber Exit if inserted above it.

## What not to do

- Don't add dependencies (`requirements.txt`, `pyproject.toml`, third-party libs) — stdlib only is a deliberate constraint.
- Don't split the file into modules unless explicitly requested.
- Don't replace the `input()` loop with a framework (argparse, click, curses) unless asked.
- Don't add comments explaining what code does; the existing style is minimal docstrings only.
- Don't commit a `bookings.json` with real data.

## Git workflow

- Default working branch for Claude-authored changes: `claude/add-claude-documentation-0U48G` (per session instructions; may differ per task).
- Commit messages follow a short imperative summary (see `git log`): e.g. `Add reschedule, services/pricing, search, and email notifications`.
- Push with `git push -u origin <branch>`. Do not open PRs unless the user asks.
