#!/usr/bin/env bash
# Shared helpers for the MedSimQA ADB scripts.
#
# Sourced, never executed. Everything here is defensive about the one thing
# that makes device automation miserable: a script that half-works against the
# wrong device, or against no device at all, and reports success.

set -euo pipefail

# --- configuration (override via environment) -------------------------------
: "${MEDSIM_PACKAGE:=dev.medsimqa.wrapper}"
: "${MEDSIM_ACTIVITY:=.MainActivity}"
: "${MEDSIM_APK:=./build/medsimqa-wrapper-debug.apk}"
: "${MEDSIM_HOST_PORT:=4173}"
: "${MEDSIM_API_PORT:=8000}"
: "${ADB:=adb}"

# --- output -----------------------------------------------------------------
if [[ -t 1 ]] && [[ "${NO_COLOR:-}" == "" ]]; then
  C_RESET=$'\033[0m'; C_RED=$'\033[31m'; C_GREEN=$'\033[32m'
  C_YELLOW=$'\033[33m'; C_BLUE=$'\033[34m'; C_DIM=$'\033[2m'
else
  C_RESET=""; C_RED=""; C_GREEN=""; C_YELLOW=""; C_BLUE=""; C_DIM=""
fi

log()   { printf '%s[medsim]%s %s\n' "$C_BLUE" "$C_RESET" "$*"; }
ok()    { printf '%s[  ok  ]%s %s\n' "$C_GREEN" "$C_RESET" "$*"; }
warn()  { printf '%s[ warn ]%s %s\n' "$C_YELLOW" "$C_RESET" "$*" >&2; }
die()   { printf '%s[ fail ]%s %s\n' "$C_RED" "$C_RESET" "$*" >&2; exit 1; }
debug() { [[ "${MEDSIM_DEBUG:-0}" == "1" ]] && printf '%s[debug]%s %s\n' "$C_DIM" "$C_RESET" "$*" >&2 || true; }

# --- device selection -------------------------------------------------------

require_adb() {
  command -v "$ADB" >/dev/null 2>&1 \
    || die "adb not found. Install platform-tools: sudo apt install android-sdk-platform-tools"
}

# Resolves exactly one device. ANDROID_SERIAL is honoured if set; otherwise a
# single connected device is used, and more than one is an error rather than a
# coin flip - running a destructive test against the wrong phone is the failure
# mode this prevents.
resolve_device() {
  require_adb
  "$ADB" start-server >/dev/null 2>&1 || true

  local devices
  devices=$("$ADB" devices | awk 'NR>1 && $2=="device" {print $1}')
  local count
  count=$(printf '%s\n' "$devices" | grep -c . || true)

  if [[ "${ANDROID_SERIAL:-}" != "" ]]; then
    printf '%s\n' "$devices" | grep -qx "$ANDROID_SERIAL" \
      || die "ANDROID_SERIAL=$ANDROID_SERIAL is not connected. Available: ${devices//$'\n'/, }"
    export ANDROID_SERIAL
  elif [[ "$count" -eq 0 ]]; then
    local unauthorised
    unauthorised=$("$ADB" devices | awk 'NR>1 && $2=="unauthorized" {print $1}')
    if [[ -n "$unauthorised" ]]; then
      die "Device $unauthorised is connected but UNAUTHORISED. Unlock the phone and accept the USB debugging prompt."
    fi
    die "No device connected. Enable Developer options > USB debugging, then re-run."
  elif [[ "$count" -gt 1 ]]; then
    die "Multiple devices connected. Set ANDROID_SERIAL to one of: ${devices//$'\n'/, }"
  else
    ANDROID_SERIAL=$(printf '%s\n' "$devices" | head -1)
    export ANDROID_SERIAL
  fi

  debug "using device $ANDROID_SERIAL"
}

adbx() { "$ADB" -s "$ANDROID_SERIAL" "$@"; }

# --- device facts -----------------------------------------------------------

device_prop()   { adbx shell getprop "$1" 2>/dev/null | tr -d '\r'; }
device_model()  { device_prop ro.product.model; }
device_brand()  { device_prop ro.product.brand; }
android_sdk()   { device_prop ro.build.version.sdk; }
android_release() { device_prop ro.build.version.release; }

is_samsung() {
  [[ "$(device_brand | tr '[:upper:]' '[:lower:]')" == "samsung" ]]
}

describe_device() {
  log "device : $(device_brand) $(device_model)"
  log "android: $(android_release) (API $(android_sdk))"
  log "serial : $ANDROID_SERIAL"
  local density size
  density=$(adbx shell wm density 2>/dev/null | tr -d '\r' | tail -1)
  size=$(adbx shell wm size 2>/dev/null | tr -d '\r' | tail -1)
  log "display: $size, $density"
}

package_installed() {
  adbx shell pm list packages 2>/dev/null | tr -d '\r' | grep -qx "package:${MEDSIM_PACKAGE}"
}

require_package() {
  package_installed || die "$MEDSIM_PACKAGE is not installed. Run ./deploy.sh first."
}

# Waits for the device to finish booting. `adb wait-for-device` returns as soon
# as adbd is up, which is minutes before the launcher is usable, so scripts that
# rely on it alone fail intermittently after a reboot.
wait_for_boot() {
  local timeout="${1:-120}" elapsed=0
  adbx wait-for-device
  while [[ "$(device_prop sys.boot_completed)" != "1" ]]; do
    sleep 2
    elapsed=$((elapsed + 2))
    [[ "$elapsed" -ge "$timeout" ]] && die "Device did not finish booting within ${timeout}s"
  done
  ok "device booted"
}

timestamp() { date +%Y%m%d-%H%M%S; }

artifact_dir() {
  local dir="${MEDSIM_ARTIFACTS:-./artifacts}/$(timestamp)"
  mkdir -p "$dir"
  printf '%s\n' "$dir"
}
