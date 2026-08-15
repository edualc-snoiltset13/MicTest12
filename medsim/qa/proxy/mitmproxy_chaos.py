"""mitmproxy addon reproducing Charles Proxy / Proxyman fault injection.

Why this exists alongside the Cypress network spec: `cy.intercept` fakes the
response *inside* the browser, so it exercises the application's error handling
but never touches the transport. This addon sits on the wire, so it also
exercises TLS interception, connection resets, real throttling and the OS-level
behaviour of a device that trusts (or does not trust) the proxy CA. That is the
difference between "the app handles a malformed body" and "the app handles a
malformed body arriving over a decrypted TLS connection on a Samsung phone".

Install
-------
    pip install mitmproxy
    mitmdump -s mitmproxy_chaos.py --set chaos_profile=malformed_json

On the device (see ../adb/setup-proxy.sh):
    Settings > Wi-Fi > (network) > Advanced > Proxy > Manual
    Host: <workstation IP>   Port: 8080
    Then trust the CA from http://mitm.it - EXCEPT for the ssl_untrusted
    profile, which deliberately requires the CA NOT be installed.

Profiles
--------
    passthrough      no interference; use to confirm the harness itself is sane
    malformed_json   rewrites JSON bodies to be unparseable at a plausible offset
    truncate         cuts the body short, as a dropped packet mid-transfer does
    html_portal      replaces the body with a captive-portal login page
    slow_3g          adds 400ms latency and throttles to ~400 kbps
    stall            holds the response past the client's 15s timeout
    drop             kills the connection after the request is sent
    flaky            fails one request in three, at random but seeded
    error_503        returns a well-formed RFC-7807 503
    empty_body       returns 200 with a zero-length body
    ssl_untrusted    documents the untrusted-CA case (see the note below)

Equivalent configurations for the commercial tools are in the same directory:
    charles-rewrite-rules.xml
    proxyman-breakpoints.json
"""

from __future__ import annotations

import json
import random
import time
from typing import Any

from mitmproxy import ctx, http

API_MARKER = "/api/v1/"

PROFILES = (
    "passthrough",
    "malformed_json",
    "truncate",
    "html_portal",
    "slow_3g",
    "stall",
    "drop",
    "flaky",
    "error_503",
    "empty_body",
    "ssl_untrusted",
)


class ChaosAddon:
    """Applies one named fault profile to every API response."""

    def __init__(self) -> None:
        # Seeded so a failing run is reproducible. An unseeded chaos proxy
        # produces bug reports nobody can reproduce, which is worse than no
        # chaos proxy.
        self.rng = random.Random(20260815)
        self.request_count = 0

    def load(self, loader: Any) -> None:
        loader.add_option(
            name="chaos_profile",
            typespec=str,
            default="passthrough",
            help=f"Fault profile to apply. One of: {', '.join(PROFILES)}",
        )
        loader.add_option(
            name="chaos_paths",
            typespec=str,
            default=API_MARKER,
            help="Only requests whose path contains this substring are affected.",
        )
        loader.add_option(
            name="chaos_rate",
            typespec=float,
            default=1.0,
            help="Fraction of matching requests to affect, 0.0-1.0.",
        )

    # -- helpers ----------------------------------------------------------

    def _applies(self, flow: http.HTTPFlow) -> bool:
        if ctx.options.chaos_paths not in flow.request.path:
            return False
        if ctx.options.chaos_rate >= 1.0:
            return True
        return self.rng.random() < ctx.options.chaos_rate

    @staticmethod
    def _log(profile: str, flow: http.HTTPFlow, note: str = "") -> None:
        ctx.log.warn(f"[chaos:{profile}] {flow.request.method} {flow.request.path} {note}")

    # -- hooks ------------------------------------------------------------

    def request(self, flow: http.HTTPFlow) -> None:
        """Faults that must act before the request reaches the server."""
        profile = ctx.options.chaos_profile
        if profile == "passthrough" or not self._applies(flow):
            return

        self.request_count += 1

        if profile == "drop":
            # Kills the connection with the request in flight. In the browser
            # this is indistinguishable from an untrusted certificate, which is
            # exactly the point: the application must not claim to know which.
            self._log(profile, flow, "killing connection")
            flow.kill()

        elif profile == "stall":
            # Holds past the client's 15s timeout without ever responding. This
            # is the failure a naive fetch() with no AbortController hangs on
            # forever, and the one users describe as "it just spins".
            self._log(profile, flow, "stalling 20s")
            time.sleep(20)

        elif profile == "error_503":
            self._log(profile, flow, "synthesising 503")
            flow.response = http.Response.make(
                503,
                json.dumps(
                    {
                        "type": "https://medsimqa.dev/errors/503",
                        "title": "Service unavailable",
                        "status": 503,
                        "detail": "Injected by the mitmproxy chaos addon.",
                        "instance": flow.request.path,
                        "errors": [],
                        "request_id": f"chaos-{self.request_count:06d}",
                    }
                ).encode(),
                {"Content-Type": "application/json", "X-Chaos-Profile": profile},
            )

        elif profile == "flaky":
            if self.request_count % 3 == 0:
                self._log(profile, flow, "failing 1 in 3")
                flow.kill()

    def response(self, flow: http.HTTPFlow) -> None:
        """Faults that rewrite a response the server actually produced."""
        profile = ctx.options.chaos_profile
        if profile == "passthrough" or not self._applies(flow) or flow.response is None:
            return

        if profile == "malformed_json":
            # Corrupt at a PLAUSIBLE offset, not byte 0. A body that fails on
            # the first character is trivially caught; one that fails halfway
            # through is what a real rewrite rule produces, and it is the case
            # that breaks streaming parsers and partially-populated state.
            body = flow.response.content or b"{}"
            midpoint = max(1, len(body) // 2)
            flow.response.content = body[:midpoint] + b',,{"truncated_by_proxy": true'
            flow.response.headers["X-Chaos-Profile"] = profile
            self._log(profile, flow, f"corrupted at byte {midpoint}")

        elif profile == "truncate":
            body = flow.response.content or b""
            flow.response.content = body[: max(1, len(body) // 3)]
            # Deliberately leave the ORIGINAL Content-Length in place. A
            # truncated body with a matching length is a different (and easier)
            # bug than one whose declared length disagrees with what arrived.
            flow.response.headers["X-Chaos-Profile"] = profile
            self._log(profile, flow, "truncated to one third")

        elif profile == "html_portal":
            flow.response.content = (
                b"<!doctype html><html><head><title>Network sign-in</title></head>"
                b"<body><h1>Sign in to continue</h1>"
                b"<form><input name=user><input type=password name=pass></form>"
                b"</body></html>"
            )
            flow.response.headers["Content-Type"] = "text/html; charset=utf-8"
            flow.response.status_code = 200
            self._log(profile, flow, "replaced with a captive portal page")

        elif profile == "empty_body":
            flow.response.content = b""
            flow.response.headers["Content-Type"] = "application/json"
            self._log(profile, flow, "emptied body")

        elif profile == "slow_3g":
            # Approximates a poor mobile connection: 400ms of latency plus a
            # transfer time derived from ~400 kbps. The dashboard's skeleton
            # states and abort-on-refetch behaviour are what this exercises.
            size_bits = len(flow.response.content or b"") * 8
            transfer_seconds = size_bits / 400_000
            time.sleep(0.4 + transfer_seconds)
            flow.response.headers["X-Chaos-Profile"] = profile
            self._log(profile, flow, f"delayed {0.4 + transfer_seconds:.2f}s")

        elif profile == "ssl_untrusted":
            # There is nothing to do here. This profile is a documentation
            # marker: to exercise the untrusted-CA path you must run mitmproxy
            # WITHOUT installing its certificate on the device. The TLS
            # handshake then fails before any HTTP flow exists, so no addon
            # hook can observe it - which is itself the lesson. See the README.
            self._log(profile, flow, "no-op; see README for the untrusted-CA procedure")


addons = [ChaosAddon()]
