# LLM Test Coverage Plan

This plan covers testing the LLM-powered functionality in this repository. The
only LLM-touching code today is [`analyze_image.py`](analyze_image.py) — a
Claude vision call against the Anthropic Messages API
(`model: claude-sonnet-4-6`, `anthropic-version: 2023-06-01`).

The current suite ([`tests/test_analyze_image.py`](tests/test_analyze_image.py))
deliberately stops at argument and image-format validation and **never
exercises the network or model path** ("Network paths are not invoked here").
Closing that gap is the goal.

The plan separates two things that are often conflated:

- **Testing the code around the LLM** — deterministic, cheap, belongs in every
  CI run.
- **Testing the model's behavior** — non-deterministic, needs evals, runs
  gated against a live model.

---

## Layer 1 — Deterministic plumbing (offline, every CI run)

Classic unit tests with the HTTP layer mocked. No API key, no network, no cost.
This is where most of the missing coverage lives.

For `analyze_image.py`, cover the paths that currently aren't tested:

- **Request construction** — mock `urllib.request.urlopen` and assert the
  request body: correct `model`, `max_tokens`, the `anthropic-version` and
  `content-type` headers, `x-api-key` present, the image block carries the
  right `media_type` and base64 `data`, and the prompt text follows the image.
- **Response parsing** — feed a fake Messages-API JSON response and assert that
  only `type == "text"` blocks are printed and joined correctly.
- **Error handling** — simulate `HTTPError` (401/429/500) and assert the
  `API error {code}: ...` message plus a non-zero exit; simulate
  `URLError`/timeout, which is **currently unhandled** — the script crashes with
  a traceback. The test will surface that as a bug to fix.
- **Edge inputs** — missing/empty `ANTHROPIC_API_KEY`, unsupported extension,
  multi-word prompt joining, and the default-prompt fallback.

> **Prerequisite refactor:** the script does all its work at import time. To
> unit-test internals cleanly, refactor into functions
> (`build_request()`, `parse_response()`, `main()`) guarded by
> `if __name__ == "__main__":`. This refactor is a precondition for good
> Layer 1 coverage.

**Target:** ~100% line/branch coverage of the plumbing, measured with
`coverage.py`.

## Layer 2 — API contract tests (offline)

Guard against the request drifting out of spec with the Anthropic Messages API:
required fields, valid roles, content-block shapes, and model-id format. A
schema assertion (jsonschema or hand-rolled) catches breakage when someone edits
the payload — without hitting the network.

## Layer 3 — Behavioral / quality evals (gated, live model)

Non-deterministic output means asserting **properties, not exact strings**.
Build a small eval harness:

- **Eval dataset** — a handful of fixture images with expected properties (an
  image of text → output contains that text; a photo of a dog → mentions
  "dog"/animal).
- **Assertion styles** — keyword/regex presence; structured-output validation
  (if JSON is requested, it parses and matches a schema); and **LLM-as-judge**
  for fuzzy quality ("does this description accurately match the image?" scored
  against a rubric).
- **Determinism controls** — pin the model id, set low/zero temperature where it
  matters, and treat scores as thresholds (e.g. judge ≥ 4/5) rather than
  equality.

## Layer 4 — Regression / golden tests

Snapshot known-good outputs (or judge scores) for the eval set and alert on
drift when the model id is bumped (e.g. `sonnet-4-6` → a newer model). This is
how quality regressions from model upgrades get caught.

## Layer 5 — Safety & robustness

- Adversarial / prompt-injection inputs (e.g. an image containing "ignore your
  instructions" text) — assert the agent isn't hijacked.
- Malformed / oversized images, declared media type vs. real bytes, and the
  20 MB limit noted in the README.
- Refusal handling — assert the code handles a refusal / unexpected
  `stop_reason` gracefully rather than crashing.

## Layer 6 — Performance & cost

Track latency and token usage (the `usage` field in the response), assert
against a budget, and fail the gated job if cost-per-eval spikes. Keeps live
evals from becoming an expensive surprise.

---

## CI strategy

| | Layers 1–2 | Layers 3–6 |
|---|---|---|
| **Trigger** | every push / PR | nightly or manual, key-gated |
| **Network** | mocked | live Anthropic API |
| **Cost** | $0 | metered |
| **Blocking?** | yes | report-only / threshold |

Gate the live layers behind `if ANTHROPIC_API_KEY` so contributors without a key
still get full Layer 1–2 coverage locally. Add `coverage.py` reporting and wire
a job under `.github/workflows/`.

## Suggested rollout order

1. Refactor `analyze_image.py` into testable functions.
2. Write Layer 1 + 2 tests, add `coverage.py`, get plumbing to ~100%.
3. Stand up the Layer 3 eval harness with 5–10 fixtures + an LLM judge.
4. Add golden snapshots (Layer 4) and the key-gated nightly workflow.
5. Layer in safety (Layer 5) and cost (Layer 6) checks.
