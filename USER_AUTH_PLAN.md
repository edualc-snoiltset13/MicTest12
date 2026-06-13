# User Authentication — Implementation Plan

This document proposes adding **user authentication and authorization** to the
Barber Booking Agent (`barber_booking_agent.py`). It is written to fit the
repository's existing constraints and conventions, and is organized as a
phased plan so it can be delivered and reviewed incrementally.

---

## 1. Current State

The Barber Booking Agent is an interactive CLI that persists everything to a
local `bookings.json` file via `load_bookings()` / `save_bookings()`:

```json
{ "barbers": { "<name>": { "slots": [...], "services": {...}, "email": "" } },
  "bookings": [ { "barber": "...", "client": "...", "client_email": "...", ... } ] }
```

There is **no concept of an account, identity, or session**. Today:

- Anyone running the CLI can register a barber under any name.
- Anyone can book, **cancel, or reschedule any booking** for any client — the
  menu (`main()`) exposes every action unconditionally.
- A "client" is just a free-text name typed at booking time; nothing ties a
  booking to an authenticated person.
- The barber profile already stores an `email`, which is a convenient natural
  identifier to build accounts around.

This is fine for a demo but means there is no access control and no way to
attribute actions to a real user.

## 2. Goals & Constraints

| Concern | Decision |
|---|---|
| **Zero external dependencies** | Mandatory. README states "uses only the standard library". Use `hashlib`, `secrets`, `getpass`, `json` only — **no** bcrypt/argon2/JWT libraries. |
| Password storage | `hashlib.pbkdf2_hmac("sha256", ...)` with a per-user random salt and a high iteration count. Never store plaintext. |
| Roles | Two roles: **barber** and **client**. Barbers manage their own profile + see their own calendar; clients book and manage their own bookings. |
| Persistence | Reuse the existing JSON file pattern. Add a `users` section (or a sibling `users.json`). |
| Backward compatibility | Existing `bookings.json` files must keep loading. Migrate lazily — treat missing `users` as `{}`. |
| Scope | CLI session auth only (in-memory "logged-in" state). No network, no tokens, no multi-process concurrency guarantees. |
| Testability | Keep auth logic in pure functions so it can be unit-tested without `input()`/`getpass()` (mirrors the existing `tests/` style with mocked I/O). |

## 3. Data Model Changes

Extend the persisted structure (kept inside `bookings.json` for simplicity, or
split into `users.json` — see §7 trade-off):

```json
{
  "users": {
    "<username>": {
      "role": "barber" | "client",
      "email": "person@example.com",
      "pwd_salt": "<hex>",
      "pwd_hash": "<hex>",
      "pwd_iterations": 240000,
      "created_at": "<iso8601>"
    }
  },
  "barbers": { "...": "(unchanged; linked to a user via matching username/email)" },
  "bookings": [
    { "...": "(unchanged) ",
      "client_user": "<username|null>"   // NEW: links booking to a client account
    }
  ]
}
```

- `username` is the dictionary key (unique, case-normalized to lower).
- Barber profiles are linked to a user account of role `barber`. When a barber
  registers an account, `register_barber()` is gated so a barber can only
  create/edit the profile that matches their own account.
- Existing bookings with no `client_user` remain valid (treated as legacy /
  unauthenticated bookings, visible to barbers but not editable by clients).

## 4. New Module: `auth.py`

A small, dependency-free, **pure-function** module so it is fully unit-testable.

```python
# Password hashing ---------------------------------------------------
def hash_password(password, *, iterations=240_000) -> dict
    # returns {"pwd_salt", "pwd_hash", "pwd_iterations"} using
    # secrets.token_hex(16) + hashlib.pbkdf2_hmac("sha256", ...)

def verify_password(password, user_record) -> bool
    # recompute pbkdf2 with stored salt/iterations; hmac.compare_digest()

# User store (operate on the in-memory `data` dict) ------------------
def create_user(data, username, password, role, email) -> dict   # raises on dupe / weak pwd / bad role
def get_user(data, username) -> dict | None
def authenticate(data, username, password) -> dict | None         # the login check

# Validation ---------------------------------------------------------
def validate_username(username) -> None   # non-empty, allowed charset, not taken
def validate_password(password) -> None   # min length, basic strength
```

Notes:
- Use `hmac.compare_digest` for constant-time hash comparison.
- `getpass.getpass()` for password entry in the CLI layer (never echo).
- Keep all `input()` / `getpass()` calls in `barber_booking_agent.py`, not in
  `auth.py`, so the logic stays testable.

## 5. CLI / UX Changes (`barber_booking_agent.py`)

1. **Pre-menu auth gate.** On startup show:
   ```
   1. Log in   2. Sign up (barber)   3. Sign up (client)   4. Exit
   ```
   `main()` keeps a `session = {"username": ..., "role": ...}` once logged in.

2. **Role-aware menu.** Replace the single static `MENU` with menus rendered
   per role:
   - **Barber:** Edit my profile/slots/services · View *my* calendar ·
     Cancel/Reschedule *my* appointments · Log out.
   - **Client:** Book an appointment · View *my* bookings ·
     Cancel/Reschedule *my own* bookings · Log out.

3. **Authorization checks** added to the mutating actions:
   - `cancel_booking` / `reschedule_booking`: clients may act only on bookings
     where `booking["client_user"] == session["username"]`; barbers only on
     bookings where `booking["barber"]` is their own profile. Filter
     `_select_booking()` to the caller's permitted set.
   - `register_barber` becomes "create/edit my barber profile", tied to the
     logged-in barber account (removes the "register anyone" hole).
   - `book_appointment` stamps `client_user = session["username"]` and
     pre-fills name/email from the account.

4. **Logout** clears the session and returns to the auth gate.

## 6. Testing Plan (`tests/test_auth.py` + extend booking tests)

Following the existing `unittest` + mocked-I/O style already used in
`tests/test_barber_booking_agent.py`:

- `hash_password` produces distinct salts; `verify_password` accepts the right
  password and rejects wrong ones.
- Stored records never contain the plaintext password.
- `create_user` rejects duplicates, weak passwords, and invalid roles.
- `authenticate` returns the user on success, `None` on failure.
- Authorization: a client cannot cancel/reschedule another user's booking; a
  barber cannot edit another barber's profile (assert the action is refused).
- Backward-compat: a legacy `bookings.json` with no `users` key loads cleanly.
- CI: existing GitHub Actions workflow runs `python -m unittest discover -s
  tests` — the new tests are picked up automatically.

## 7. Key Trade-offs & Decisions

- **PBKDF2 vs. bcrypt/argon2.** bcrypt/argon2 are stronger but require pip
  installs, which violates the repo's stdlib-only rule. `pbkdf2_hmac` with a
  high iteration count is the strongest fully-stdlib option and is the right
  choice here. (If the no-deps rule is ever relaxed, swap in argon2 behind the
  same `auth.py` interface.)
- **Same file vs. `users.json`.** Keeping `users` inside `bookings.json` is
  simplest and atomic with booking writes. A separate `users.json` better
  isolates credentials (and is easier to `.gitignore`). **Recommendation:**
  separate `users.json`, added to `.gitignore` alongside the existing
  `bookings.json` entry, so credentials are never committed.
- **CLI session only.** No tokens/JWT/refresh — out of scope for a local CLI
  and would pull in complexity with no benefit. Documented as a non-goal.
- **No password reset / MFA / lockout** in v1. Listed below as future work.

## 8. Phased Delivery

1. **Phase 1 — Foundation:** add `auth.py` (hashing + user store) and tests.
   No behavior change to the running CLI yet.
2. **Phase 2 — Auth gate:** add signup/login/logout and the `session` object;
   persist `users`. App still functional for everyone once logged in.
3. **Phase 3 — Authorization:** role-aware menus + ownership checks on
   book/cancel/reschedule/profile-edit; stamp `client_user` on bookings.
4. **Phase 4 — Hardening & docs:** lazy migration of legacy data, update
   `README.md` (auth section + `.gitignore` note), add edge-case tests.

## 9. Future Work (out of scope for v1)

- Password reset flow (email-based, reusing the existing SMTP/email template
  infrastructure in `email_template.py`).
- Account lockout / rate limiting after repeated failed logins.
- Optional MFA (TOTP via `hmac` + `hashlib`, still stdlib-only).
- Admin role for managing all barbers/bookings.

## 10. Affected Files Summary

| File | Change |
|---|---|
| `auth.py` | **New.** Hashing, verification, user store, validation. |
| `barber_booking_agent.py` | Auth gate, `session`, role menus, ownership checks, `client_user` stamping. |
| `tests/test_auth.py` | **New.** Unit tests for hashing/auth/validation. |
| `tests/test_barber_booking_agent.py` | Extend with authorization + backward-compat cases. |
| `.gitignore` | Add `users.json` (if split out). |
| `README.md` | Document login/signup, roles, and credential storage. |
