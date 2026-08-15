#!/usr/bin/env bash
#
# The full on-device sequence: deploy, exercise, capture, report.
#
# This is what runs overnight. Every stage writes to one artifact directory so
# a failure the next morning has logs, a screenshot and a battery series
# alongside it, rather than a bare exit code.
#
# Usage:
#   ./run-suite.sh                  full sequence
#   ./run-suite.sh --quick          skip the soak test
#
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib-common.sh"

QUICK=0
[[ "${1:-}" == "--quick" ]] && QUICK=1

resolve_device
DIR=$(artifact_dir)
log "artifacts: $DIR"

FAILURES=0
stage() {
  local name="$1"; shift
  log "--- $name ---"
  if "$@" >"$DIR/${name// /-}.log" 2>&1; then
    ok "$name"
  else
    warn "$name FAILED (see $DIR/${name// /-}.log)"
    FAILURES=$((FAILURES + 1))
  fi
}

describe_device | tee "$DIR/device.txt"

stage "deploy" ./deploy.sh
stage "reset-network" ./throttle.sh reset

# Screenshot each locale, so a layout regression on the real device is visible
# rather than inferred. Chrome is driven directly because the wrapper is a thin
# WebView over the same URL.
log "--- locale screenshots ---"
for locale in en de es nl ru; do
  adbx shell am start -a android.intent.action.VIEW \
    -d "http://localhost:${MEDSIM_HOST_PORT}/?lang=${locale}" >/dev/null 2>&1 || true
  sleep 4
  adbx exec-out screencap -p > "$DIR/screen-${locale}.png" 2>/dev/null \
    && ok "  captured $locale" \
    || warn "  screenshot failed for $locale"
done

# The narrow-viewport case, which is where localized layouts break.
log "--- narrow layout check ---"
ORIGINAL_SIZE=$(adbx shell wm size | tr -d '\r' | awk '{print $NF}')
adbx shell wm size 320x640 >/dev/null 2>&1 || true
adbx shell am start -a android.intent.action.VIEW \
  -d "http://localhost:${MEDSIM_HOST_PORT}/?lang=de" >/dev/null 2>&1 || true
sleep 4
adbx exec-out screencap -p > "$DIR/screen-narrow-de.png" 2>/dev/null || true
adbx shell wm size "$ORIGINAL_SIZE" >/dev/null 2>&1 || adbx shell wm size reset >/dev/null 2>&1 || true
ok "  restored display size"

stage "network-3g" ./throttle.sh 3g
sleep 10
stage "network-offline" ./throttle.sh offline
sleep 8
adbx exec-out screencap -p > "$DIR/screen-offline.png" 2>/dev/null || true
stage "network-restore" ./throttle.sh reset

stage "crash-check" ./logcat.sh --crash

if [[ "$QUICK" == "0" ]]; then
  log "--- battery soak (10 minutes) ---"
  MEDSIM_ARTIFACTS="$DIR" ./battery.sh --soak 600 | tee "$DIR/battery-soak.log" || FAILURES=$((FAILURES + 1))
fi

./logcat.sh --capture 30 >/dev/null 2>&1 || true

echo
log "================ summary ================"
log "artifacts : $DIR"
log "failures  : $FAILURES"
ls -1 "$DIR" | sed 's/^/    /'

[[ "$FAILURES" -eq 0 ]] && { ok "suite passed"; exit 0; } || { warn "suite completed with $FAILURES failure(s)"; exit 1; }
