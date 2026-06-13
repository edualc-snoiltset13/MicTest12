# CLAUDE.md

Guidance for AI assistants (and humans) working in this repository.

## What this repository is

`MicTest12` is a collection of small, **self-contained Python utilities** plus a
couple of static HTML pages and an architecture-planning document. The modules
are mostly independent of one another — there is no single application entry
point, package, or framework tying them together. Think of it as a grab-bag of
standalone scripts that happen to share a repo.

The one cluster of genuinely related files is the **Barber Booking Agent**
(`barber_booking_agent.py` + `email_template.py`), which is also the subject of
`README.md`, the HTML pages, and the `compression.py` helper.

### Hard rule: standard library only

**Every Python module here uses only the Python standard library. There are no
third-party dependencies, no `requirements.txt`, no `pyproject.toml`, and no
virtualenv.** Preserve this. If a task seems to need a third-party package,
prefer a stdlib solution (`urllib`, `html.parser`, `gzip`, `smtplib`, `json`,
`argparse`, `unittest`, `unittest.mock`) and only raise the dependency question
with the user if there is truly no stdlib path.

## Layout

| Path | What it is |
|---|---|
| `barber_booking_agent.py` | Interactive CLI to register barbers, book/reschedule/cancel/search appointments. Persists to `bookings.json`. Sends console + optional SMTP email notifications. |
| `email_template.py` | Renders multipart (text + HTML) booking emails. Imported by the booking agent. |
| `compression.py` | Streaming gzip compress/decompress helpers (chunked, memory-safe). |
| `calculator.py` | Expression-evaluating calculator (tokenizer → shunting-yard → RPN eval) with a REPL. |
| `simple_calculator.py` | A separate, class-based calculator with memory + history. Unrelated to `calculator.py`. |
| `web_scraper.py` | Fetches URLs, parses HTML with `html.parser`, emits JSON/CSV analysis records. Honors `robots.txt`. |
| `analyze_image.py` | Minimal CLI that sends an image to the Claude vision API (`claude-sonnet-4-6` by default). Runs entirely at import time. |
| `index.html`, `about.html` | Static marketing pages for the booking agent. No build step. |
| `GAMING_MICROSERVICES_PLAN.md` | A standalone design document. Not code; not wired to anything. |
| `tests/` | Unittest suite **discovered by CI**. |
| `test_calculator.py`, `test_compression.py` | Root-level unittest files **NOT discovered by CI** (see Testing). |

## Testing

The project uses `unittest` from the standard library. **Tests live in two
places and this distinction matters:**

1. `tests/` — `tests/test_barber_booking_agent.py`, `tests/test_analyze_image.py`.
   These are what CI runs.
2. Repo root — `test_calculator.py`, `test_compression.py`. These are **not**
   picked up by the CI's discovery command and must be run by name.

CI (`.github/workflows/tests.yml`) runs on every push and PR across Python
3.9–3.12 with:

```bash
python -m unittest discover -s tests -v
```

To run everything locally (CI suite + the root-level files):

```bash
python -m unittest discover -s tests -v        # tests/ — matches CI
python -m unittest test_calculator test_compression -v   # root-level files
```

Or run a single module / case:

```bash
python -m unittest tests.test_barber_booking_agent -v
python -m unittest tests.test_barber_booking_agent.SlotLogicTests
```

### Testing conventions to follow

- **Stdlib only in tests too** — use `unittest`, `unittest.mock`, `io.StringIO`,
  `tempfile`, `subprocess`. No pytest, no fixtures library.
- **No real network or SMTP.** `analyze_image.py` tests drive the script via
  `subprocess` and only exercise argument/format/key-validation paths — they
  never hit the API. SMTP is mocked via `mock.patch.object(smtplib, "SMTP")`.
- **Interactive input is mocked** with `mock.patch("builtins.input", ...)` and
  stdout is captured with `redirect_stdout(io.StringIO())`.
- **Filesystem side effects are isolated** by `chdir`-ing into a temp dir in
  `setUp`/`tearDown` (the booking agent writes `bookings.json` into the CWD).
- `tests/test_analyze_image.py` includes a check that the README's documented
  supported image formats stay in sync with the script. If you change the
  format table in `analyze_image.py`, update the README too or that test fails.
- **If you add a new test file, put it in `tests/` so CI actually runs it.**
  Adding a `test_*.py` at the repo root will silently be skipped by CI.

## Conventions

- **Python style:** 4-space indent, module-level docstring on every file
  describing purpose + usage, function docstrings throughout. Section banners
  using box-drawing comments (`# ── Section ──`) are used in the larger modules
  — match the local style of the file you are editing.
- **Naming:** internal helpers are prefixed with a single underscore
  (`_select_barber`, `_is_slot_taken`, `_row`). Public functions are the
  user-facing operations.
- **CLI scripts** guard execution with `if __name__ == "__main__":` and a
  `main()` (except `analyze_image.py`, which deliberately runs at import time —
  keep it that way; its tests depend on it).
- **Error handling in CLIs:** validate input, print a clear message, and return
  to the menu rather than raising. `calculator.py`/`web_scraper.py` use exit
  codes; `analyze_image.py` documents its exit codes in the README.
- **Data persistence:** the booking agent reads/writes `bookings.json` in the
  current working directory. This file is git-ignored (along with `__pycache__/`
  and `*.pyc`) — never commit it.

## Configuration / environment variables

- **SMTP (booking agent email):** `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`,
  `SMTP_PASS`, and optional `SMTP_FROM`. If unset, the agent runs fine with
  console-only notifications — email is strictly optional and must degrade
  gracefully.
- **Claude vision (`analyze_image.py`):** `ANTHROPIC_API_KEY` is required. The
  default model is `claude-sonnet-4-6`. When touching model defaults, prefer
  current Claude model IDs.

## Running the tools

```bash
python barber_booking_agent.py                 # interactive booking menu
python calculator.py "2 + 3 * 4"               # one-shot; no args = REPL
python web_scraper.py https://example.com --format csv --output out.csv
ANTHROPIC_API_KEY=sk-ant-... python analyze_image.py photo.png "What is this?"
```

## Git workflow

- Active development branch for AI-assisted work: `claude/claude-md-docs-1kadfk`.
  Develop and push there; create it locally if missing. Do not push to other
  branches without explicit permission.
- Push with `git push -u origin <branch>`.
- **Do not open a pull request unless explicitly asked.**
- History shows changes land via PRs merged to the default branch; keep commits
  focused with clear, descriptive messages.

## When making changes — checklist

1. Stay within the standard library.
2. Add or update tests in `tests/` (so CI runs them).
3. Match the existing docstring + section-comment style of the file.
4. If you change `analyze_image.py`'s supported formats, update `README.md`
   to keep the sync-check test passing.
5. Run the full local suite (both `tests/` and the root-level files) before
   pushing.
6. Never commit `bookings.json`.
