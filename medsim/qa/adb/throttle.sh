#!/usr/bin/env bash
#
# Network condition simulation on a physical device.
#
# Two mechanisms, because neither alone is sufficient:
#
#   1. Radio-level, via `adb shell svc data` and the emulator's netdelay/netspeed
#      where available. Blunt but real - it affects the whole device.
#   2. Proxy-level, via the mitmproxy addon in ../proxy. Precise, scriptable,
#      and the only way to throttle a single endpoint rather than the device.
#
# For a Samsung device on real hardware the radio commands below are the ones
# that work; the emulator-only commands are detected and skipped.
#
# Usage:
#   ./throttle.sh 3g            slow 3G (400 kbps, 400ms latency)
#   ./throttle.sh 2g            very slow (100 kbps, 800ms)
#   ./throttle.sh lte           fast (20 Mbps, 40ms)
#   ./throttle.sh offline       airplane mode on
#   ./throttle.sh wifi-only     disable mobile data, keep wifi
#   ./throttle.sh data-only     disable wifi, keep mobile data
#   ./throttle.sh flaky         toggle connectivity every 8 seconds
#   ./throttle.sh reset         restore everything
#
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib-common.sh"

PROFILE="${1:-reset}"
resolve_device

is_emulator() { [[ "$(device_prop ro.kernel.qemu)" == "1" ]] || [[ "$ANDROID_SERIAL" == emulator-* ]]; }

# The emulator console accepts netspeed/netdelay; hardware does not. Attempting
# them on hardware prints a confusing error, so they are gated.
emulator_net() {
  if ! is_emulator; then
    debug "skipping emulator-only command: $*"
    return 0
  fi
  local port="${ANDROID_SERIAL#emulator-}"
  local token_file="$HOME/.emulator_console_auth_token"
  if [[ -f "$token_file" ]]; then
    { printf 'auth %s\n' "$(cat "$token_file")"; printf '%s\n' "$*"; printf 'quit\n'; } \
      | timeout 5 nc localhost "$port" >/dev/null 2>&1 || warn "emulator console command failed: $*"
  else
    warn "no emulator console auth token; skipping: $*"
  fi
}

set_airplane() {
  local state="$1"  # 1 = on
  adbx shell settings put global airplane_mode_on "$state"
  # The broadcast is what actually applies the setting; writing the setting
  # alone changes the toggle's appearance and nothing else. On Android 11+ this
  # needs the shell UID, which adb shell has.
  adbx shell "su -c 'am broadcast -a android.intent.action.AIRPLANE_MODE --ez state $([[ $state == 1 ]] && echo true || echo false)'" >/dev/null 2>&1 \
    || adbx shell "am broadcast -a android.intent.action.AIRPLANE_MODE --ez state $([[ $state == 1 ]] && echo true || echo false)" >/dev/null 2>&1 \
    || warn "could not broadcast the airplane-mode change; toggle it manually if connectivity does not change"
}

case "$PROFILE" in
  3g)
    log "applying slow 3G"
    emulator_net "network speed edge"
    emulator_net "network delay 400"
    ok "radio profile: EDGE, 400ms delay"
    log "for precise per-endpoint throttling run, on the workstation:"
    log "  mitmdump -s ../proxy/mitmproxy_chaos.py --set chaos_profile=slow_3g"
    log "  ./setup-proxy.sh \$(hostname -I | awk '{print \$1}') 8080"
    ;;

  2g)
    log "applying very slow 2G"
    emulator_net "network speed gsm"
    emulator_net "network delay gprs"
    ok "radio profile: GSM, GPRS delay"
    ;;

  lte)
    log "applying fast LTE"
    emulator_net "network speed lte"
    emulator_net "network delay none"
    ok "radio profile: LTE, no added delay"
    ;;

  offline)
    log "enabling airplane mode"
    set_airplane 1
    sleep 3
    ok "device is offline - the dashboard should show its offline banner"
    ;;

  wifi-only)
    log "disabling mobile data, keeping wifi"
    adbx shell svc data disable
    adbx shell svc wifi enable
    ok "wifi only"
    ;;

  data-only)
    log "disabling wifi, keeping mobile data"
    adbx shell svc wifi disable
    adbx shell svc data enable
    ok "mobile data only"
    ;;

  flaky)
    log "toggling connectivity every 8 seconds (Ctrl-C to stop)"
    # This is the condition that exposes retry storms and duplicated requests:
    # a connection that recovers just long enough for a request to start.
    trap 'log "restoring connectivity"; adbx shell svc wifi enable; adbx shell svc data enable; exit 0' INT TERM
    while true; do
      warn "  down"
      adbx shell svc wifi disable
      adbx shell svc data disable
      sleep 8
      ok "  up"
      adbx shell svc wifi enable
      adbx shell svc data enable
      sleep 8
    done
    ;;

  reset)
    log "restoring network settings"
    set_airplane 0
    adbx shell svc wifi enable
    adbx shell svc data enable
    emulator_net "network speed full"
    emulator_net "network delay none"
    adbx shell settings delete global http_proxy >/dev/null 2>&1 || true
    adbx shell settings put global http_proxy :0 >/dev/null 2>&1 || true
    ok "network restored"
    ;;

  *)
    die "Unknown profile: $PROFILE. Run with -h for the list."
    ;;
esac

log "current connectivity:"
adbx shell dumpsys connectivity 2>/dev/null | grep -E "^(NetworkAgentInfo|Active default)" | head -5 | sed 's/^/    /' || true
