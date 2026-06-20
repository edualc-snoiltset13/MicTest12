# MicTest12 — Development Roadmap

_Last updated: 2026-06-06_

This document is a **development roadmap**: where the project is today, where it
should go, and the phased, prioritized work to get there. It is meant to be a
living document — update it as milestones land.

---

## 1. Where We Are Today

MicTest12 is a sandbox repository (`"Tester test"`) that has accumulated several
independent, **standard-library-only Python** tools, a couple of static HTML
pages, and a large backlog of experimental pull requests. The de-facto flagship
is the **Barber Booking Agent**.

### Current assets

| Area | Files | State |
|---|---|---|
| **Barber Booking Agent (flagship)** | `barber_booking_agent.py`, `email_template.py` | Working CLI; JSON persistence; optional SMTP email; HTML email templates |
| Calculators | `calculator.py`, `simple_calculator.py` | Two overlapping implementations |
| Utilities | `web_scraper.py`, `compression.py` | Standalone stdlib scripts |
| AI helper | `analyze_image.py` | Claude vision API CLI wrapper |
| Static web | `index.html`, `about.html` | Static landing/about pages |
| Tests | `tests/test_barber_booking_agent.py`, `tests/test_analyze_image.py`, `test_calculator.py`, `test_compression.py` | Mixed — see gap below |
| CI | `.github/workflows/tests.yml` | unittest matrix on Python 3.9–3.12 |
| Planning | `GAMING_MICROSERVICES_PLAN.md` | Aspirational architecture doc (unrelated to current code) |

### Known gaps & tech debt

1. **CI does not run all tests.** The workflow runs `unittest discover -s tests`,
   so `test_calculator.py` and `test_compression.py` (at the repo root) are
   **never executed in CI**. Either move them under `tests/` or broaden discovery.
2. **Duplicate calculators.** `calculator.py` and `simple_calculator.py` overlap.
   Pick one canonical module and deprecate/delete the other.
3. **Untested modules.** `web_scraper.py` and `email_template.py` have no tests.
4. **PR backlog (~20 open).** Many experimental PRs (HTML pages, shopping cart,
   CSV cleaner, Maven config, etc.) targeting feature branches rather than a
   trunk. They need triage: merge, close, or convert to roadmap items.
5. **No single product focus.** Issues [#1] and [#2] request a real **Barber
   Slot Booking API/backend**, but the current agent is a CLI. The repo needs a
   decision on whether to evolve toward that service.

---

## 2. Strategic Direction

The roadmap proposes converging on **one coherent product — the Barber Booking
platform** — while keeping the smaller utilities as a clearly separated
`tools/` collection. This gives the repo a narrative instead of being a pile of
unrelated scripts.

**Guiding principles**
- Keep the **standard-library-only** convention for core code where practical;
  introduce dependencies deliberately and document them.
- Every new feature ships with tests that **run in CI**.
- Reduce the open-PR backlog before adding net-new surface area.

---

## 3. Phased Roadmap

### Phase 0 — Stabilize & Tidy (foundations)  ⏱ ~1 week
_Goal: green, trustworthy CI and a clean baseline._

- [ ] **Fix CI test discovery** so root-level tests run (move `test_calculator.py`
      and `test_compression.py` into `tests/`, or add them to the discovery path).
- [ ] **Add `CLAUDE.md` / contributor notes** documenting the stdlib-only
      convention and the tests layout (see open PR [#26]).
- [ ] **Resolve calculator duplication** — choose `calculator.py` as canonical,
      fold in anything unique from `simple_calculator.py`, deprecate the other.
- [ ] **Backlog triage** — review all open PRs ([#3]–[#27]); merge what's ready,
      close stale experiments, file the rest as roadmap issues.
- [ ] **Add a linter/formatter** (e.g. `ruff` + `ruff format`) as a CI check.

**Exit criteria:** CI runs every test in the repo and is green; no duplicate
modules; PR backlog under control.

---

### Phase 1 — Harden the Barber Booking Agent (CLI)  ⏱ ~1–2 weeks
_Goal: make the flagship robust and well-tested._

- [ ] **Add tests for `email_template.py`** (rendering for confirmed /
      rescheduled / cancelled × client / barber).
- [ ] **Input validation & error handling** for dates, slots, and email addresses.
- [ ] **Concurrency / data-integrity** review of `bookings.json` writes
      (atomic write-and-rename to avoid corruption).
- [ ] **Token-based booking lookup** (see open PR [#3]) — finalize and merge.
- [ ] **Configurable data path** and a documented backup/export command.

**Exit criteria:** Booking agent has >90% line coverage on core logic and a
documented, validated CLI.

---

### Phase 2 — Booking Service / API  ⏱ ~3–4 weeks
_Goal: deliver the API/backend requested in issues [#1] and [#2]._

Decision point: the issues sketch a **Node.js + Express + SQLite** service. The
existing code is Python. Recommendation: **build the API in Python**
(`http.server` or a thin framework) to reuse the existing domain logic and keep
the stack consistent — unless there's a reason to standardize on Node.

- [ ] **Define the data model** (slots, bookings) with a real datastore
      (SQLite via stdlib `sqlite3`).
- [ ] **Endpoints:** list slots by date, create slots (admin), book a slot
      (client), list bookings (admin/customer).
- [ ] **Atomic booking** — enforce a unique constraint to prevent double-booking;
      return `409` on conflict.
- [ ] **Reuse** the existing email/notification layer (`email_template.py` + SMTP).
- [ ] **API tests** (happy path + conflict + validation) wired into CI.
- [ ] **Docs:** setup, run, and sample `curl` requests in the README.

**Exit criteria:** A running booking API with atomic bookings, notifications, and
CI-tested endpoints; the CLI becomes a client of (or shares a core with) the API.

---

### Phase 3 — Interfaces & Integrations  ⏱ ~4+ weeks
_Goal: make the service usable by real users._

- [ ] **Web admin UI** — calendar view of slots and bookings (build on the
      existing static HTML pages).
- [ ] **Public booking page** for clients.
- [ ] **Calendar sync** (iCal export; optional Google Calendar).
- [ ] **Notifications** beyond email (optional SMS/webhook).
- [ ] **Auth** for admin/booking management.

---

### Phase 4 — Tooling Collection (parallel track)  ⏱ ongoing
_Goal: keep the standalone utilities maintained but separated._

- [ ] Move `web_scraper.py`, `compression.py`, `calculator.py`, `analyze_image.py`
      under a `tools/` directory with their own README.
- [ ] Backfill tests for `web_scraper.py`.
- [ ] Decide the fate of `GAMING_MICROSERVICES_PLAN.md` — keep as a reference
      design exercise or remove if out of scope.

---

## 4. Milestones at a Glance

| Milestone | Phase | Outcome |
|---|---|---|
| **M0 — Green Baseline** | 0 | All tests run in CI; backlog triaged; lint enforced |
| **M1 — Solid CLI** | 1 | Hardened, well-tested Barber Booking Agent |
| **M2 — Booking API** | 2 | Atomic booking service with notifications + API tests |
| **M3 — Usable Product** | 3 | Admin/booking UIs, calendar sync, auth |
| **M4 — Clean Tooling** | 4 | Utilities isolated and tested |

---

## 5. Immediate Next Steps (top 5)

1. Fix CI so `test_calculator.py` and `test_compression.py` actually run.
2. Triage the open PR backlog (merge/close/convert to issues).
3. Resolve the `calculator.py` / `simple_calculator.py` duplication.
4. Add tests for `email_template.py`.
5. Make the Phase 2 stack decision (Python vs Node) for the booking API.

---

## 6. Risks & Open Questions

- **Stack split (Python vs Node):** issues request Node; code is Python. Resolve
  before Phase 2 to avoid duplicate implementations.
- **Stdlib-only vs. frameworks:** a web API/UI may justify dependencies; decide
  the policy explicitly.
- **Scope creep:** the repo tends to accumulate one-off experiments. Gate new
  surface area on backlog reduction (Phase 0).

[#1]: https://github.com/edualc-snoiltset13/MicTest12/issues/1
[#2]: https://github.com/edualc-snoiltset13/MicTest12/issues/2
[#3]: https://github.com/edualc-snoiltset13/MicTest12/pull/3
[#26]: https://github.com/edualc-snoiltset13/MicTest12/pull/26
[#27]: https://github.com/edualc-snoiltset13/MicTest12/pull/27
