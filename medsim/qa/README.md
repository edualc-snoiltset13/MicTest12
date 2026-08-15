# MedSimQA — QA automation

Three layers of testing, each covering what the others cannot.

| Layer | Location | Runs where | Covers |
|---|---|---|---|
| Browser E2E | `cypress/e2e/` | CI, headless | 50 edge cases: behaviour, clinical rendering, localized layout, network faults |
| Wire-level fault injection | `proxy/` | A workstation with a device attached | TLS interception, real throttling, response rewriting on the wire |
| Device automation | `adb/` | A physical Samsung device over USB | Install, crash triage, battery drain, radio conditions |

## Layer 1 — Cypress (50 edge cases)

```bash
cd medsim/qa
npm install
npm test                    # all 50
npm run test:layout         # localization and layout only
npm run test:network        # network interception only
npm run cy:run:mobile       # the whole suite at 360x740
```

The stack must be running first:

```bash
# terminal 1
cd medsim/backend && ./.venv/bin/python -m uvicorn app.main:app --port 8000
# terminal 2
cd medsim/frontend && npm run build && npm run preview
```

### The 50 cases

| Spec | Range | Focus |
|---|---|---|
| `01-case-library.cy.ts` | EC-01 … EC-13 | Filtering, search, sort, URL state, navigation |
| `02-clinical-rendering.cy.ts` | EC-14 … EC-25 | Flags, timelines, charts, smears, susceptibility, error isolation |
| `03-layout-and-regional-formatting.cy.ts` | EC-26 … EC-38 | 5 locales × 7 viewports, decimal separators, CLDR plurals, Cyrillic, touch targets, contrast, theme |
| `04-network-interception.cy.ts` | EC-39 … EC-50 | Status errors, malformed JSON, truncation, captive portals, drops, TLS failure, stalls, races |

Two custom commands carry most of the localization suite:

- `cy.assertNoHorizontalOverflow()` — the page body must never scroll
  sideways. Wide content scrolls in its own container; that is the design rule.
  On failure it names the offending elements rather than only reporting a pixel
  count.
- `cy.assertNoClippedText(selector)` — text must not be truncated by its own
  box. Elements that truncate deliberately (`line-clamp`, `text-ellipsis`) are
  excluded.

### If the Cypress binary will not download

Some networks truncate the ~200 MB archive. `verify-assertions.mjs` reproduces
the load-bearing assertions using Playwright, which is already present in most
CI images:

```bash
node verify-assertions.mjs http://localhost:4173
```

It is not a substitute for the Cypress run — it covers 23 assertions rather
than 50 — but it is enough to prove the suite's claims hold before a release.

## Layer 2 — Proxy fault injection

`cy.intercept` fakes responses *inside* the browser, so it never touches the
transport. These configurations sit on the wire, which is the only way to test
TLS interception and real throttling.

```bash
pip install mitmproxy
mitmdump -s proxy/mitmproxy_chaos.py --set chaos_profile=malformed_json
```

Profiles: `passthrough`, `malformed_json`, `truncate`, `html_portal`,
`slow_3g`, `stall`, `drop`, `flaky`, `error_503`, `empty_body`,
`ssl_untrusted`.

Equivalents for the commercial tools:

- `proxy/charles-rewrite-rules.xml` — import via Tools ▸ Rewrite
- `proxy/proxyman-breakpoints.json` — Map Local, scripting and throttling scenarios

Enable exactly one at a time. A response corrupted several ways at once cannot
be attributed to any single fault.

### Testing SSL decryption *failure*

This is the case teams usually skip, because it needs the opposite of the
normal setup: the proxy must be active and its CA must **not** be trusted.

```bash
./adb/setup-proxy.sh 192.168.1.50 8080   # then REMOVE the CA from the device
./adb/logcat.sh --network                # watch the handshake fail
```

Expected behaviour: a network error state with a retry. The application must
not claim to know a certificate was the cause — the browser does not tell it,
and an untrusted CA is indistinguishable from a pulled cable at that layer.

## Layer 3 — Device automation (Samsung)

```bash
./adb/deploy.sh              # install, reverse-forward ports, launch
./adb/logcat.sh --follow     # stream only this app's output
./adb/logcat.sh --crash      # find and CLASSIFY the last crash
./adb/throttle.sh 3g         # radio conditions
./adb/battery.sh --soak 600  # 10-minute drain and memory-growth profile
./adb/run-suite.sh           # the full overnight sequence
```

`adb reverse` is what makes this work without putting the phone on the same
network as the workstation: the phone's own `localhost:4173` is tunnelled to
the workstation's over the USB cable, so no LAN IP is hardcoded.

Samsung-specific handling in `deploy.sh`:

- **Doze exemption.** One UI's battery management freezes a backgrounded
  WebView mid-test and reports it as an app hang. This is the single most
  important step for reliable overnight runs on a Galaxy device.
- **Animations off.** At 1× they make waits nondeterministic and cost ~20% of
  suite runtime.
- **Stay awake while charging**, so the device does not sleep mid-run.

`logcat.sh --crash` classifies rather than dumps: out-of-memory, TLS failure,
ANR, native crash and network-on-main-thread each get a named verdict, because
the alternative is reading 80 lines of stack trace to learn it was an OOM.

## What the suite found

Running these assertions against the application during development surfaced
six real defects, all fixed:

1. Visually-hidden labels inside flag badges are `position: absolute` with no
   positioned ancestor, so they escaped their scroll container's clipping and
   added 172 px of horizontal page scroll at 375 px — worse in German, where
   the wider table pushed them further right.
2. The chart header's control group would not wrap, overflowing a 320 px
   viewport with German labels.
3. `Laboratoriumuitslagen` — an unbreakable Dutch compound — widened its stat
   tile's grid track rather than wrapping.
4. Russian filtered counts read `1 из 25 случая`; agreement in that
   construction follows the total, not the count.
5. Error states lost the request id when an intermediary stripped
   `X-Request-ID`, instead of falling back to the RFC-7807 body.
6. `<select>` controls stayed at 36 px on coarse pointers because the
   component's own `min-height` was declared after the media query in the same
   cascade layer.

Every one of those is a localization or device bug that an English desktop
smoke test would have passed.
