#!/usr/bin/env bash
#
# Deploys the MedSimQA mobile wrapper to a connected Samsung device and points
# it at a dashboard running on this workstation.
#
# The reverse-port-forward is what makes this work without putting the phone on
# the same network as the dev machine, and without hardcoding a LAN IP that
# changes every time you move desks: `adb reverse` makes the phone's own
# localhost:4173 resolve to the workstation's localhost:4173 over the USB cable.
#
# Usage:
#   ./deploy.sh                      install and launch
#   ./deploy.sh --reinstall          uninstall first (clears app data)
#   ./deploy.sh --no-launch          install only
#   ./deploy.sh --apk path/to.apk    override the APK
#
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib-common.sh"

REINSTALL=0
LAUNCH=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --reinstall) REINSTALL=1; shift ;;
    --no-launch) LAUNCH=0; shift ;;
    --apk) MEDSIM_APK="$2"; shift 2 ;;
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
    *) die "Unknown argument: $1" ;;
  esac
done

resolve_device
describe_device

is_samsung || warn "This device is not a Samsung. The One UI-specific steps below will be skipped."

# --- 1. host reachability ---------------------------------------------------
log "checking the dashboard is up on this workstation"
curl -sf "http://localhost:${MEDSIM_HOST_PORT}/" >/dev/null \
  || die "Nothing is serving http://localhost:${MEDSIM_HOST_PORT}. Start it with: npm run preview (in medsim/frontend)"
curl -sf "http://localhost:${MEDSIM_API_PORT}/healthz" >/dev/null \
  || die "The API is not up on port ${MEDSIM_API_PORT}. Start it with: uvicorn app.main:app (in medsim/backend)"
ok "dashboard and API are reachable locally"

# --- 2. reverse port forwarding --------------------------------------------
# Removed first: a stale forward from a previous session silently points the
# app at a dead port, and the resulting "network error" wastes an afternoon.
log "setting up reverse port forwarding over USB"
adbx reverse --remove-all >/dev/null 2>&1 || true
adbx reverse "tcp:${MEDSIM_HOST_PORT}" "tcp:${MEDSIM_HOST_PORT}"
adbx reverse "tcp:${MEDSIM_API_PORT}" "tcp:${MEDSIM_API_PORT}"
adbx reverse --list | sed 's/^/    /'
ok "phone localhost:${MEDSIM_HOST_PORT} now reaches this workstation"

# --- 3. install -------------------------------------------------------------
if [[ "$REINSTALL" == "1" ]] && package_installed; then
  log "uninstalling the existing build (this clears app data)"
  adbx uninstall "$MEDSIM_PACKAGE" >/dev/null
fi

if [[ -f "$MEDSIM_APK" ]]; then
  log "installing $MEDSIM_APK"
  # -r replace, -d allow downgrade, -g grant all runtime permissions so the
  # first launch is not blocked by a permission dialog no script can dismiss.
  if ! adbx install -r -d -g "$MEDSIM_APK" 2>&1 | tee /tmp/medsim-install.log | sed 's/^/    /'; then
    if grep -q INSTALL_FAILED_UPDATE_INCOMPATIBLE /tmp/medsim-install.log; then
      die "Signature mismatch with the installed build. Re-run with --reinstall."
    fi
    if grep -q INSTALL_FAILED_INSUFFICIENT_STORAGE /tmp/medsim-install.log; then
      die "Not enough storage on the device. Free space and retry."
    fi
    die "Install failed. See /tmp/medsim-install.log"
  fi
  ok "installed $MEDSIM_PACKAGE"
else
  warn "APK not found at $MEDSIM_APK - skipping install."
  warn "The wrapper is a thin WebView shell; you can also test in Chrome:"
  warn "  adb shell am start -a android.intent.action.VIEW -d http://localhost:${MEDSIM_HOST_PORT}/"
fi

# --- 4. Samsung-specific preparation ---------------------------------------
if is_samsung; then
  log "applying Samsung One UI test preparation"

  # One UI's aggressive battery management will freeze a backgrounded WebView
  # mid-test and report it as an app hang. Exempting the package is the single
  # most important step for reliable overnight runs on a Galaxy device.
  if package_installed; then
    adbx shell dumpsys deviceidle whitelist "+${MEDSIM_PACKAGE}" >/dev/null 2>&1 \
      && ok "battery optimisation exemption applied" \
      || warn "could not apply the doze whitelist (needs no root, but some carrier builds block it)"
  fi

  # Animations at 1x make waits nondeterministic and slow the suite by ~20%.
  for scale in window_animation_scale transition_animation_scale animator_duration_scale; do
    adbx shell settings put global "$scale" 0.0 >/dev/null 2>&1 || true
  done
  ok "animations disabled (restore with ./deploy.sh --restore-animations)"

  # Keeps the screen on while charging so the device does not sleep mid-run.
  adbx shell settings put global stay_on_while_plugged_in 3 >/dev/null 2>&1 || true
  ok "screen will stay on while plugged in"
fi

# --- 5. launch --------------------------------------------------------------
if [[ "$LAUNCH" == "1" ]]; then
  if package_installed; then
    log "launching $MEDSIM_PACKAGE"
    adbx shell am force-stop "$MEDSIM_PACKAGE" || true
    adbx shell am start -n "${MEDSIM_PACKAGE}/${MEDSIM_ACTIVITY}" \
      -a android.intent.action.VIEW \
      -d "http://localhost:${MEDSIM_HOST_PORT}/" >/dev/null
    sleep 2
    if adbx shell pidof "$MEDSIM_PACKAGE" >/dev/null 2>&1; then
      ok "app is running (pid $(adbx shell pidof "$MEDSIM_PACKAGE" | tr -d '\r'))"
    else
      die "App did not stay running. Capture the crash with: ./logcat.sh --crash"
    fi
  else
    log "launching the dashboard in the device browser instead"
    adbx shell am start -a android.intent.action.VIEW \
      -d "http://localhost:${MEDSIM_HOST_PORT}/" >/dev/null
    ok "opened in the default browser"
  fi
fi

cat <<EOF

Next steps:
  ./logcat.sh --follow          stream filtered logs
  ./throttle.sh 3g              simulate a slow network
  ./battery.sh --report         capture a battery/power profile
  ./run-suite.sh                run the full on-device sequence
EOF
