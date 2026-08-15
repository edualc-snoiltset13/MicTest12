#!/usr/bin/env bash
#
# Points a Samsung device at an intercepting proxy (Charles, Proxyman or
# mitmproxy) running on this workstation, and explains the trust decision that
# determines whether you are testing decryption or testing decryption FAILURE.
#
# Usage:
#   ./setup-proxy.sh 192.168.1.50 8080     route traffic through the proxy
#   ./setup-proxy.sh --clear               stop using the proxy
#   ./setup-proxy.sh --status              show the current setting
#
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib-common.sh"

resolve_device

case "${1:-}" in
  --clear)
    log "clearing the device proxy"
    adbx shell settings put global http_proxy :0
    adbx shell settings delete global global_http_proxy_host >/dev/null 2>&1 || true
    adbx shell settings delete global global_http_proxy_port >/dev/null 2>&1 || true
    ok "proxy cleared"
    exit 0
    ;;
  --status)
    log "current proxy setting: $(adbx shell settings get global http_proxy | tr -d '\r')"
    exit 0
    ;;
  "")
    die "Usage: $0 <proxy-host> <proxy-port> | --clear | --status"
    ;;
esac

HOST="$1"
PORT="${2:-8080}"

log "routing device traffic through ${HOST}:${PORT}"
adbx shell settings put global http_proxy "${HOST}:${PORT}"
ok "proxy set"

cat <<EOF

${C_YELLOW}The trust decision${C_RESET}
------------------
The proxy can only read HTTPS if the device trusts its CA. Which of the two
states you want depends on what you are testing:

  ${C_GREEN}A. Testing what the proxy DOES to traffic${C_RESET}
     (malformed JSON, truncation, throttling, rewritten values)
     -> Install the CA:
          1. On the device, browse to http://mitm.it (mitmproxy) or
             http://chls.pro/ssl (Charles) or http://proxy.man/ssl (Proxyman)
          2. Download and install the certificate
          3. Settings > Biometrics and security > Other security settings >
             Install from device storage > CA certificate
        Note: on Android 7+ an app trusts USER-installed CAs only if its
        network security config opts in. The debug build of the wrapper does;
        the release build does not.

  ${C_RED}B. Testing what happens when decryption FAILS${C_RESET}
     (the "SSL decryption error" case in the QA plan)
     -> Do NOT install the CA, or remove it first:
          Settings > Biometrics and security > Other security settings >
          User credentials > remove the proxy certificate
        Every HTTPS request then fails at the TLS handshake, before any HTTP
        request exists. The dashboard must show a network error state with a
        retry - and must NOT claim to know it was a certificate problem,
        because the browser does not tell it.

Verify which state you are in:
  ./logcat.sh --network        # SSL/TLS failures appear here immediately

Then start the proxy on this workstation, for example:
  mitmdump -s ../proxy/mitmproxy_chaos.py --set chaos_profile=malformed_json
EOF
