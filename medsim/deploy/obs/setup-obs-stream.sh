#!/usr/bin/env bash
#
# Streams the MedSimQA dashboard to an external display or an Android TV box.
#
# Three delivery options, because they suit genuinely different situations:
#
#   1. RTMP to a local server, then any client pulls it. Highest latency
#      (2-5s), works over any network, and one stream serves many screens.
#      This is the right choice for a ward display wall.
#
#   2. SRT, low latency (~200ms), point to point. Use when someone is
#      interacting with the dashboard and watching the remote screen.
#
#   3. Virtual camera, for feeding the dashboard into a video call rather than
#      a display. Needs v4l2loopback.
#
# Usage:
#   ./setup-obs-stream.sh --check
#   ./setup-obs-stream.sh --rtmp-server              start a local RTMP relay
#   ./setup-obs-stream.sh --stream rtmp://host/live/medsim
#   ./setup-obs-stream.sh --srt --target 192.168.1.42:9999
#   ./setup-obs-stream.sh --virtual-camera
#   ./setup-obs-stream.sh --android-tv 192.168.1.42  cast to an ATV box
#
set -euo pipefail

DISPLAY_URL="${MEDSIM_URL:-http://localhost/}"
CAPTURE_WIDTH=1920
CAPTURE_HEIGHT=1080
FRAMERATE=30
BITRATE_KBPS=4500

C_GREEN=$'\033[32m'; C_YELLOW=$'\033[33m'; C_RED=$'\033[31m'; C_RESET=$'\033[0m'
ok()   { printf '%s✓%s %s\n' "$C_GREEN" "$C_RESET" "$*"; }
warn() { printf '%s!%s %s\n' "$C_YELLOW" "$C_RESET" "$*" >&2; }
die()  { printf '%s✗%s %s\n' "$C_RED" "$C_RESET" "$*" >&2; exit 1; }

check_prerequisites() {
  local missing=0
  for tool in obs ffmpeg; do
    if command -v "$tool" >/dev/null 2>&1; then
      ok "$tool present"
    else
      warn "$tool NOT found"
      missing=1
    fi
  done

  if [[ "${XDG_SESSION_TYPE:-}" == "wayland" ]]; then
    warn "Wayland session detected."
    warn "OBS window capture on Wayland requires the PipeWire portal; use"
    warn "'Screen Capture (PipeWire)' rather than 'Window Capture (Xcomposite)',"
    warn "which silently produces a black frame under Wayland."
  else
    ok "X11 session (window capture works directly)"
  fi

  if lsmod | grep -q v4l2loopback; then
    ok "v4l2loopback loaded: $(v4l2-ctl --list-devices 2>/dev/null | grep -A1 -i virtual | tail -1 | tr -d '\t' || echo '/dev/video?')"
  else
    warn "v4l2loopback not loaded - the virtual camera will be unavailable"
    warn "  sudo modprobe v4l2loopback exclusive_caps=1 card_label='MedSimQA Virtual Camera'"
  fi

  # NVENC or VAAPI hardware encoding drops CPU use for a 1080p30 stream from
  # roughly 60% of a core to near zero, which matters on the small-form-factor
  # boxes these displays usually run on.
  if command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi >/dev/null 2>&1; then
    ok "NVIDIA GPU present - use the NVENC encoder in OBS"
  elif [[ -e /dev/dri/renderD128 ]]; then
    ok "VAAPI render node present - use the VAAPI encoder in OBS"
  else
    warn "No hardware encoder detected; x264 will use significant CPU"
  fi

  (( missing == 0 )) || die "Install the missing tools first: sudo apt install obs-studio ffmpeg"
}

start_rtmp_server() {
  command -v ffmpeg >/dev/null || die "ffmpeg is required"
  ok "Starting a local RTMP relay on rtmp://0.0.0.0:1935/live"
  cat <<EOF

Point OBS at:
  Settings > Stream > Service: Custom
  Server:     rtmp://localhost:1935/live
  Stream key: medsim

Then play it on the Android TV box (VLC, or any RTMP-capable player):
  rtmp://$(hostname -I | awk '{print $1}'):1935/live/medsim

EOF
  # nginx-rtmp is the production answer; this ffmpeg listener is enough for a
  # single consumer and needs no extra package.
  ffmpeg -loglevel warning -listen 1 -f flv -i rtmp://0.0.0.0:1935/live/medsim -c copy -f flv - >/dev/null
}

stream_to() {
  local target="$1"
  ok "Streaming ${DISPLAY_URL} to ${target}"
  # Captures the X display directly, which avoids needing OBS at all for a
  # headless relay box.
  ffmpeg -loglevel warning \
    -f x11grab -framerate "$FRAMERATE" -video_size "${CAPTURE_WIDTH}x${CAPTURE_HEIGHT}" -i "${DISPLAY:-:0}" \
    -c:v libx264 -preset veryfast -tune zerolatency \
    -b:v "${BITRATE_KBPS}k" -maxrate "${BITRATE_KBPS}k" -bufsize "$((BITRATE_KBPS * 2))k" \
    -pix_fmt yuv420p -g "$((FRAMERATE * 2))" \
    -f flv "$target"
}

stream_srt() {
  local target="$1"
  ok "Low-latency SRT to srt://${target}"
  ffmpeg -loglevel warning \
    -f x11grab -framerate "$FRAMERATE" -video_size "${CAPTURE_WIDTH}x${CAPTURE_HEIGHT}" -i "${DISPLAY:-:0}" \
    -c:v libx264 -preset ultrafast -tune zerolatency \
    -b:v "${BITRATE_KBPS}k" -pix_fmt yuv420p -g "$FRAMERATE" \
    -f mpegts "srt://${target}?mode=caller&latency=200000"
}

virtual_camera() {
  lsmod | grep -q v4l2loopback || die "v4l2loopback is not loaded (see --check)"
  local device
  device=$(v4l2-ctl --list-devices 2>/dev/null | grep -A1 -i "MedSimQA" | tail -1 | tr -d '\t ' || echo /dev/video10)
  ok "Feeding the dashboard into ${device}"
  ffmpeg -loglevel warning \
    -f x11grab -framerate "$FRAMERATE" -video_size "${CAPTURE_WIDTH}x${CAPTURE_HEIGHT}" -i "${DISPLAY:-:0}" \
    -pix_fmt yuv420p -f v4l2 "$device"
}

cast_to_android_tv() {
  local host="$1"
  command -v adb >/dev/null || die "adb is required: sudo apt install android-sdk-platform-tools"

  ok "Connecting to the Android TV box at ${host}"
  adb connect "${host}:5555" || die "Could not connect. Enable Developer options > USB debugging (network) on the box."
  sleep 2

  # Opening the dashboard directly on the box is far better than streaming
  # video to it: no encoder, no latency, no bandwidth, and the text stays
  # crisp because it is rendered natively rather than compressed.
  ok "Opening the dashboard natively on the box (better than streaming video)"
  adb -s "${host}:5555" shell am start -a android.intent.action.VIEW -d "$DISPLAY_URL" \
    || warn "Could not launch a browser; is one installed on the box?"

  cat <<EOF

Prefer the native route above. Stream video only if the box cannot reach the
dashboard's network, in which case:

  ./setup-obs-stream.sh --rtmp-server          # on this machine
  # then on the box, open: rtmp://$(hostname -I | awk '{print $1}'):1935/live/medsim

EOF
}

case "${1:-}" in
  --check)          check_prerequisites ;;
  --rtmp-server)    start_rtmp_server ;;
  --stream)         stream_to "${2:?target URL required}" ;;
  --srt)            shift; [[ "${1:-}" == "--target" ]] && shift; stream_srt "${1:?host:port required}" ;;
  --virtual-camera) virtual_camera ;;
  --android-tv)     cast_to_android_tv "${2:?host required}" ;;
  *) sed -n '2,26p' "$0"; exit 1 ;;
esac
