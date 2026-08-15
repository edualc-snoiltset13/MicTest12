#!/usr/bin/env bash
#
# Battery and power profiling for the MedSimQA mobile wrapper.
#
# The question this answers: does leaving the dashboard open on a ward round
# flatten the phone? A WebView polling an API with animated charts is a
# plausible battery offender, and `batterystats` is the only way to attribute
# drain to a package rather than guess.
#
# Usage:
#   ./battery.sh --reset             clear stats and start a measurement window
#   ./battery.sh --report            summarise drain attributed to the app
#   ./battery.sh --simulate 15       report the device at 15% battery
#   ./battery.sh --unplug            tell Android the charger is disconnected
#   ./battery.sh --restore           undo all simulation
#   ./battery.sh --soak 600          run a 10-minute soak and report
#
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib-common.sh"

MODE="report"
VALUE=15
SOAK_SECONDS=600

while [[ $# -gt 0 ]]; do
  case "$1" in
    --reset)    MODE="reset"; shift ;;
    --report)   MODE="report"; shift ;;
    --simulate) MODE="simulate"; VALUE="${2:-15}"; shift 2 ;;
    --unplug)   MODE="unplug"; shift ;;
    --restore)  MODE="restore"; shift ;;
    --soak)     MODE="soak"; SOAK_SECONDS="${2:-600}"; shift 2 ;;
    -h|--help)  sed -n '2,16p' "$0"; exit 0 ;;
    *) die "Unknown argument: $1" ;;
  esac
done

resolve_device

battery_level() { adbx shell dumpsys battery 2>/dev/null | awk -F': ' '/level/{print $2}' | tr -d '\r'; }
battery_temp()  { adbx shell dumpsys battery 2>/dev/null | awk -F': ' '/temperature/{print $2/10}' | tr -d '\r'; }

case "$MODE" in
  reset)
    log "clearing battery statistics"
    # Unplugging is required: while charging, batterystats attributes almost
    # nothing, and a "measurement" taken on the cable is meaningless.
    adbx shell dumpsys battery unplug >/dev/null
    adbx shell dumpsys batterystats --reset >/dev/null
    adbx shell dumpsys batterystats --enable full-wake-history >/dev/null 2>&1 || true
    ok "stats cleared, charger reported as disconnected"
    log "level now ${C_YELLOW}$(battery_level)%${C_RESET}, temp $(battery_temp)C"
    warn "remember to run --restore afterwards, or the phone will keep believing it is unplugged"
    ;;

  report)
    require_package
    log "battery report for $MEDSIM_PACKAGE"
    UID_LINE=$(adbx shell dumpsys package "$MEDSIM_PACKAGE" 2>/dev/null | grep -m1 userId= | tr -d '\r' || true)
    APP_UID="${UID_LINE#*userId=}"; APP_UID="${APP_UID%% *}"
    log "uid: ${APP_UID:-unknown}"

    echo
    log "--- estimated power use (mAh) ---"
    adbx shell dumpsys batterystats --charged "$MEDSIM_PACKAGE" 2>/dev/null \
      | grep -E "Estimated power|Uid $APP_UID|Wake lock|Foreground|Cpu time|Mobile radio|Wifi" \
      | head -25 | sed 's/^/    /' || warn "no attributed stats yet - run --reset, use the app, then --report"

    echo
    log "--- wake locks held ---"
    adbx shell dumpsys power 2>/dev/null | grep -A 5 "Wake Locks" | head -12 | sed 's/^/    /' || true

    echo
    log "--- current state ---"
    printf '    level: %s%%\n    temperature: %sC\n' "$(battery_level)" "$(battery_temp)"
    ;;

  simulate)
    (( VALUE >= 0 && VALUE <= 100 )) || die "Battery level must be 0-100"
    log "reporting battery at ${VALUE}%"
    adbx shell dumpsys battery set level "$VALUE" >/dev/null
    adbx shell dumpsys battery unplug >/dev/null
    ok "device now believes it is at ${VALUE}% and unplugged"
    if (( VALUE <= 15 )); then
      warn "below 15%, One UI may enable power saving, which throttles the CPU and"
      warn "can suspend background WebView timers. That is the condition being tested."
    fi
    ;;

  unplug)
    adbx shell dumpsys battery unplug >/dev/null
    ok "charger reported as disconnected"
    ;;

  restore)
    log "restoring real battery reporting"
    adbx shell dumpsys battery reset >/dev/null
    ok "restored - level is once again $(battery_level)%"
    ;;

  soak)
    require_package
    DIR=$(artifact_dir)
    log "running a ${SOAK_SECONDS}s soak; results to $DIR"

    adbx shell dumpsys battery unplug >/dev/null
    adbx shell dumpsys batterystats --reset >/dev/null
    START_LEVEL=$(battery_level)
    START_TEMP=$(battery_temp)
    log "start: ${START_LEVEL}%, ${START_TEMP}C"

    adbx shell am force-stop "$MEDSIM_PACKAGE" || true
    adbx shell am start -n "${MEDSIM_PACKAGE}/${MEDSIM_ACTIVITY}" \
      -d "http://localhost:${MEDSIM_HOST_PORT}/" >/dev/null

    # Sample every 30s so a thermal or drain cliff is visible in the series
    # rather than averaged away by a single before/after pair.
    printf 'elapsed_s,level_pct,temp_c,rss_kb\n' > "$DIR/soak.csv"
    for ((elapsed = 0; elapsed < SOAK_SECONDS; elapsed += 30)); do
      RSS=$(adbx shell dumpsys meminfo "$MEDSIM_PACKAGE" 2>/dev/null | awk '/TOTAL PSS/{print $3; exit}' | tr -d '\r')
      printf '%s,%s,%s,%s\n' "$elapsed" "$(battery_level)" "$(battery_temp)" "${RSS:-0}" >> "$DIR/soak.csv"
      printf '\r    %ds / %ds  level=%s%%  temp=%sC  pss=%sKB ' \
        "$elapsed" "$SOAK_SECONDS" "$(battery_level)" "$(battery_temp)" "${RSS:-?}"
      sleep 30
    done
    echo

    END_LEVEL=$(battery_level)
    DRAIN=$((START_LEVEL - END_LEVEL))
    adbx shell dumpsys batterystats --charged "$MEDSIM_PACKAGE" > "$DIR/batterystats.txt" 2>/dev/null || true
    adbx shell dumpsys meminfo "$MEDSIM_PACKAGE" > "$DIR/meminfo.txt" 2>/dev/null || true
    adbx shell dumpsys battery reset >/dev/null

    ok "soak complete: ${DRAIN}% drained over $((SOAK_SECONDS / 60)) minutes"
    log "series: $DIR/soak.csv"

    # A memory series that only ever rises is the signature of a leak, and a
    # WebView with charts is a plausible place for one.
    FIRST_RSS=$(awk -F, 'NR==2{print $4}' "$DIR/soak.csv")
    LAST_RSS=$(tail -1 "$DIR/soak.csv" | awk -F, '{print $4}')
    if [[ -n "$FIRST_RSS" && -n "$LAST_RSS" && "$FIRST_RSS" -gt 0 ]]; then
      GROWTH=$(( (LAST_RSS - FIRST_RSS) * 100 / FIRST_RSS ))
      if (( GROWTH > 50 )); then
        warn "memory grew ${GROWTH}% during the soak - investigate for a leak"
      else
        ok "memory growth ${GROWTH}% - within tolerance"
      fi
    fi
    ;;
esac
