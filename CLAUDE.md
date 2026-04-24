# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository

A single-file Python CLI that manages barber appointment bookings. The entire implementation lives in `barber_booking_agent.py`; there is no package layout, no build step, and no test suite.

## Running

```bash
python barber_booking_agent.py
```

Requires Python 3.7+ and uses only the standard library — do **not** add third-party dependencies without a strong reason; the "no external deps" property is called out in the README as a feature.

Optional email notifications activate only when all of `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS` are set (plus optional `SMTP_FROM`). When any is missing, `send_email_notification` silently returns `False` and the agent continues with console-only output — preserve this "email is optional, never fatal" behavior.

## Architecture

The program is a menu-driven REPL with a single in-memory dict (`data`) that mirrors `bookings.json` on disk. Every mutation calls `save_bookings(data)` before returning, so the JSON file is the source of truth between sessions.

Data shape persisted to `bookings.json`:

```
{
  "barbers": { "<name>": { "slots": [...], "services": {name: price}, "email": "" } },
  "bookings": [ { "barber", "client", "client_email", "date", "time",
                  "service", "price", "booked_at" }, ... ]
}
```

Conventions that matter when editing:

- **Barber name is the primary key.** `data["barbers"]` is keyed by name, and bookings reference barbers by name string. Renaming a barber would orphan bookings — there's no migration path, so don't add a rename feature casually.
- **Slot availability is computed, not stored.** `_is_slot_taken` scans `data["bookings"]` each time; there is no reserved/free flag on slots. New booking flows (e.g. reschedule) must use `_select_free_slot` to avoid double-booking.
- **Notifications are a two-call pattern.** Every booking/cancel/reschedule calls `notify(...)` twice — once for the barber (email via `_barber_email(data, name)`) and once for the client (email from the booking record). Keep both calls when adding new mutation flows.
- **Input helpers return `None` on invalid input** (`_select_barber`, `_select_date`, `_select_free_slot`, `_select_booking`). Callers are expected to early-return on `None` rather than raise.
- **Dates are `YYYY-MM-DD` strings, times are `HH:MM` strings.** Sorting and "upcoming vs past" comparisons rely on lexicographic ordering of these formats — don't switch to other formats without updating the comparisons in `view_bookings`.
- **Menu dispatch is a chain of `if/elif` on string digits in `main()`.** When adding a menu option, update both the `MENU` constant and the dispatch chain, and renumber "Exit" accordingly (it's currently the highest number, not a fixed value).

## Branch workflow

Feature work happens on `claude/...` branches (see existing `claude/barber-booking-agent-iFcT7`, `claude/add-claude-documentation-Iyq6a`). `main` is not used as the working branch in this repo.
