# UPSPRING — Platform Specifications

UPSPRING is a lightweight **class discussion platform** that lets students and
instructors hold threaded conversations around course topics. Access is
role-based: **moderators** steer and police discussions, while **contributors**
participate.

> **Status:** Reference / demo implementation. Authentication and persistence
> run client-side (`localStorage`) so the platform can be explored without a
> backend. The data model and flows below describe how a production build
> should behave.

---

## 1. Goals

| # | Goal |
|---|------|
| 1 | Give a class a single, focused space for asynchronous discussion. |
| 2 | Clearly separate **moderator** authority from **contributor** participation. |
| 3 | Keep important threads visible (pinning) and stop derailed ones (locking). |
| 4 | Be self-contained and trivial to host as static files. |

---

## 2. Pages

| Page | File | Purpose |
|------|------|---------|
| Sign In | `signin.html` | Collects name, email, access code, and role; validates and starts a session. |
| Class Discussion | `discussion.html` | The discussion board: create threads, reply, and (for moderators) pin/lock/remove. |
| Specifications | `SPECIFICATIONS.md` | This document. |

---

## 3. Roles & Permissions

There are two roles, selected at sign-in and validated against a role-specific
access code.

| Capability | Contributor | Moderator |
|------------|:-----------:|:---------:|
| View all discussions and replies | ✅ | ✅ |
| Create a new discussion thread | ✅ | ✅ |
| Post a reply | ✅ | ✅ |
| Delete **own** thread / reply | ✅ | ✅ |
| Delete **any** thread / reply | ❌ | ✅ |
| Pin / unpin a thread | ❌ | ✅ |
| Lock / unlock a thread | ❌ | ✅ |

**Access codes (demo):**

| Role | Code |
|------|------|
| Contributor | `class2026` |
| Moderator | `mod-upspring` |

> In production these codes are replaced by real authentication (SSO / LMS
> integration) and role claims issued by the server, never validated in the
> browser.

---

## 4. Authentication & Session

1. The user enters **display name**, **email**, **access code**, and selects a
   **role**.
2. The form validates that all fields are present, the email is well-formed,
   and the access code matches the selected role.
3. On success a session object is stored and the user is sent to the
   discussion page.
4. The discussion page is **guarded**: if no session exists, the user is
   redirected back to sign-in.
5. **Sign out** clears the session and returns to the sign-in page.

**Session object**

```json
{
  "name": "Jordan Lee",
  "email": "jordan@school.edu",
  "role": "contributor",
  "signedInAt": "2026-05-30T14:00:00.000Z"
}
```

---

## 5. Data Model

### Thread
```json
{
  "id": "string (unique)",
  "title": "string (<= 140 chars)",
  "body": "string",
  "author": "display name",
  "authorEmail": "owner email (used for ownership checks)",
  "role": "moderator | contributor",
  "createdAt": "ISO 8601 timestamp",
  "pinned": false,
  "locked": false,
  "replies": [ /* Reply */ ]
}
```

### Reply
```json
{
  "id": "string (unique)",
  "author": "display name",
  "authorEmail": "owner email",
  "role": "moderator | contributor",
  "text": "string",
  "createdAt": "ISO 8601 timestamp"
}
```

Threads are persisted under the `upspring_threads` key; the session under
`upspring_session`.

---

## 6. Discussion Behaviour

- **Ordering:** pinned threads appear first, then newest-first by creation time.
- **Pinning** (moderator): highlights a thread and floats it to the top.
- **Locking** (moderator): disables the reply form and shows a "locked" notice.
  Existing replies remain visible.
- **Deletion:** removing a thread also removes its replies (with confirmation).
  Contributors may delete only items they authored; moderators may delete any.
- **Moderator badge:** replies and threads authored by a moderator are marked
  so the class can distinguish official guidance.
- **Reply shortcut:** pressing **Enter** in a reply box submits the reply.

---

## 7. Security Notes (Production Hardening)

The demo intentionally cuts corners that a real deployment must not:

- Move **all** authentication and authorization to the server; never trust a
  client-supplied role.
- Enforce per-action permission checks server-side (the UI hiding a button is
  not a security control).
- Sanitize and escape all user content on output (the demo HTML-escapes text to
  prevent script injection — keep this behaviour).
- Add rate limiting, audit logs for moderator actions, and content reporting.
- Use durable storage (a database) instead of `localStorage`.

---

## 8. Quick Start

1. Open `upspring/signin.html` in a browser.
2. Sign in as a **contributor** (`class2026`) or **moderator** (`mod-upspring`).
3. Create a discussion, reply to threads, and — as a moderator — pin, lock, or
   remove content.
4. Use **Sign out** to end the session.

---

*© 2026 UPSPRING · Educational use.*
