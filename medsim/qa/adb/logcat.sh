#!/usr/bin/env bash
#
# Log capture and crash triage for the MedSimQA mobile wrapper.
#
# The problem this solves: `adb logcat` on a modern Samsung device emits several
# hundred lines a second from carrier and OEM services, and the twelve lines you
# need are buried in it. Every mode below narrows to a specific question.
#
# Usage:
#   ./logcat.sh --follow            stream only this app's output
#   ./logcat.sh --crash             show the most recent crash for this app
#   ./logcat.sh --anr               pull ANR (application-not-responding) traces
#   ./logcat.sh --webview           WebView console + JS errors only
#   ./logcat.sh --network           network and TLS failures only
#   ./logcat.sh --capture 60        record 60 seconds to an artifact directory
#   ./logcat.sh --watch             fail loudly the moment a crash appears
#
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib-common.sh"

MODE="follow"
DURATION=60

while [[ $# -gt 0 ]]; do
  case "$1" in
    --follow)  MODE="follow"; shift ;;
    --crash)   MODE="crash"; shift ;;
    --anr)     MODE="anr"; shift ;;
    --webview) MODE="webview"; shift ;;
    --network) MODE="network"; shift ;;
    --watch)   MODE="watch"; shift ;;
    --capture) MODE="capture"; DURATION="${2:-60}"; shift 2 ;;
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
    *) die "Unknown argument: $1" ;;
  esac
done

resolve_device

# The app's PID is the only reliable filter. Package-name filtering misses
# native crashes (which are logged by the tombstone daemon under a different
# tag) and misses anything logged before the app sets its tag.
app_pid() { adbx shell pidof "$MEDSIM_PACKAGE" 2>/dev/null | tr -d '\r' | awk '{print $1}'; }

case "$MODE" in

  follow)
    PID=$(app_pid) || true
    if [[ -z "${PID:-}" ]]; then
      warn "$MEDSIM_PACKAGE is not running; falling back to a tag filter."
      log "streaming (Ctrl-C to stop)"
      adbx logcat -v time \
        MedSimQA:V chromium:V WebView:V ActivityManager:I AndroidRuntime:E \
        DEBUG:E System.err:W '*:S'
    else
      log "streaming logs for pid $PID (Ctrl-C to stop)"
      adbx logcat -v time --pid="$PID"
    fi
    ;;

  crash)
    log "searching the log buffer for the most recent crash"
    # -b crash is a dedicated ring buffer; it survives the app dying, which the
    # main buffer's contents may not under memory pressure.
    CRASH=$(adbx logcat -b crash -d -v time 2>/dev/null | grep -A 60 -i "$MEDSIM_PACKAGE" | tail -80 || true)

    if [[ -z "$CRASH" ]]; then
      log "nothing in the crash buffer; checking the main buffer"
      CRASH=$(adbx logcat -d -v time AndroidRuntime:E DEBUG:E '*:S' 2>/dev/null | tail -60 || true)
    fi

    if [[ -z "$CRASH" ]]; then
      ok "no crash found for $MEDSIM_PACKAGE"
      exit 0
    fi

    printf '%s\n' "$CRASH"

    # Name the failure class rather than leaving the reader to read 80 lines of
    # stack trace to find out it was an OOM.
    echo
    if grep -q "OutOfMemoryError" <<<"$CRASH"; then
      warn "classified: OUT OF MEMORY - the WebView heap was exhausted."
      warn "  Likely cause: rendering a large case with every chart mounted at once."
    elif grep -q "NetworkOnMainThreadException" <<<"$CRASH"; then
      warn "classified: NETWORK ON MAIN THREAD"
    elif grep -qi "SSLHandshakeException\|CertPathValidatorException" <<<"$CRASH"; then
      warn "classified: TLS FAILURE - the device does not trust the server or proxy certificate."
      warn "  If a proxy is active, install its CA (see ./setup-proxy.sh) or expect this."
    elif grep -q "ANR in" <<<"$CRASH"; then
      warn "classified: ANR - the main thread was blocked."
    elif grep -q "SIGSEGV\|SIGABRT" <<<"$CRASH"; then
      warn "classified: NATIVE CRASH - see the tombstone under /data/tombstones."
    else
      warn "classified: unrecognised. The full trace is above."
    fi
    exit 1
    ;;

  anr)
    log "pulling ANR traces"
    DIR=$(artifact_dir)
    # /data/anr is not world-readable on modern Android, so try both the
    # bugreport path and the direct path; one of the two usually works without
    # root depending on the OEM build.
    if adbx shell ls /data/anr/ >/dev/null 2>&1; then
      adbx pull /data/anr "$DIR/anr" 2>/dev/null && ok "pulled to $DIR/anr" || warn "could not pull /data/anr directly"
    fi
    adbx logcat -b events -d | grep -i "am_anr" | tail -20 | sed 's/^/    /' || true
    ok "ANR event records above; full traces in $DIR if the pull succeeded"
    ;;

  webview)
    log "streaming WebView console and JS errors (Ctrl-C to stop)"
    # chromium:D carries console.log from the page; the app's own tag carries
    # anything the wrapper logs deliberately.
    adbx logcat -v time chromium:D "cr_Ime:D" MedSimQA:V '*:S' \
      | grep --line-buffered -Ei "console|javascript|uncaught|error|warn"
    ;;

  network)
    log "streaming network and TLS failures (Ctrl-C to stop)"
    adbx logcat -v time '*:W' \
      | grep --line-buffered -Ei \
        "ssl|tls|certificate|handshake|ERR_|net::|socket|timeout|unreachable|refused|dns"
    ;;

  capture)
    DIR=$(artifact_dir)
    log "capturing ${DURATION}s of logs to $DIR"
    adbx logcat -c   # clear, so the capture contains only this window
    adbx logcat -v threadtime > "$DIR/full.log" &
    LOGCAT_PID=$!
    # shellcheck disable=SC2064
    trap "kill $LOGCAT_PID 2>/dev/null || true" EXIT

    for ((i = DURATION; i > 0; i--)); do
      printf '\r    %ds remaining ' "$i"
      sleep 1
    done
    printf '\r%*s\r' 30 ''

    kill "$LOGCAT_PID" 2>/dev/null || true
    wait "$LOGCAT_PID" 2>/dev/null || true

    # Split the capture into the views a triager actually wants.
    grep -Ei "$MEDSIM_PACKAGE" "$DIR/full.log" > "$DIR/app.log" || true
    grep -Ei "fatal|AndroidRuntime|DEBUG.*signal" "$DIR/full.log" > "$DIR/crashes.log" || true
    grep -Ei "ssl|tls|certificate|net::|ERR_" "$DIR/full.log" > "$DIR/network.log" || true
    grep -Ei "chromium|console" "$DIR/full.log" > "$DIR/webview.log" || true

    adbx bugreport "$DIR/bugreport.zip" >/dev/null 2>&1 && ok "bugreport captured" || warn "bugreport unavailable"

    ok "captured to $DIR"
    wc -l "$DIR"/*.log | sed 's/^/    /'
    ;;

  watch)
    log "watching for crashes (Ctrl-C to stop)"
    adbx logcat -c
    adbx logcat -v time AndroidRuntime:E DEBUG:E '*:S' | while read -r line; do
      if grep -qi "$MEDSIM_PACKAGE\|FATAL EXCEPTION" <<<"$line"; then
        printf '%s[CRASH]%s %s\n' "$C_RED" "$C_RESET" "$line"
        # A terminal bell, because this mode exists to be left running while
        # someone else does something more interesting.
        printf '\a'
      fi
    done
    ;;
esac
