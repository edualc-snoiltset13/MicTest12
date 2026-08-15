#!/usr/bin/env bash
#
# MedSimQA — full-stack deployment for Ubuntu 22.04 / 24.04 LTS.
#
# Installs and configures: Python 3.11+, Node.js 20 LTS, the backend service,
# the built frontend behind nginx, systemd units, a firewall policy, log
# rotation, and optionally Chrome/Brave plus OBS for the display-wall use case.
#
# Design principles, because a deployment script is read far more often than
# it is written:
#
#   * IDEMPOTENT. Re-running it must converge, not duplicate. Every step checks
#     before it acts.
#   * NO SILENT FAILURE. `set -euo pipefail` plus an ERR trap that names the
#     line and the command. A deploy that half-works is worse than one that
#     stops.
#   * EXPLAINS ITSELF. Every non-obvious step says why, especially the package
#     conflicts, because those are what actually consume an afternoon.
#   * SAFE BY DEFAULT. Generates real secrets, refuses to run the API as root,
#     binds the backend to loopback only, and never enables the chaos layer in
#     a production install.
#
# Usage:
#   sudo ./deploy-ubuntu.sh                      full install
#   sudo ./deploy-ubuntu.sh --skip-browsers      no Chrome/Brave
#   sudo ./deploy-ubuntu.sh --with-obs           add OBS + virtual camera
#   sudo ./deploy-ubuntu.sh --domain medsim.example.org --with-tls
#   sudo ./deploy-ubuntu.sh --uninstall
#   sudo ./deploy-ubuntu.sh --dry-run            print actions, change nothing
#
set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

APP_NAME="medsim"
APP_USER="medsim"
APP_GROUP="medsim"
APP_ROOT="/opt/medsim"
DATA_ROOT="/var/lib/medsim"
LOG_ROOT="/var/log/medsim"
VENV="${APP_ROOT}/venv"

BACKEND_PORT=8000
FRONTEND_PORT=80
DOMAIN=""

PYTHON_MIN="3.11"
NODE_MAJOR=20

SKIP_BROWSERS=0
WITH_OBS=0
WITH_TLS=0
UNINSTALL=0
DRY_RUN=0

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# ---------------------------------------------------------------------------
# Output and failure handling
# ---------------------------------------------------------------------------

if [[ -t 1 ]]; then
  C_RESET=$'\033[0m'; C_RED=$'\033[31m'; C_GREEN=$'\033[32m'
  C_YELLOW=$'\033[33m'; C_BLUE=$'\033[34m'; C_BOLD=$'\033[1m'
else
  C_RESET=""; C_RED=""; C_GREEN=""; C_YELLOW=""; C_BLUE=""; C_BOLD=""
fi

STEP=0
step()  { STEP=$((STEP + 1)); printf '\n%s[%02d]%s %s%s%s\n' "$C_BLUE" "$STEP" "$C_RESET" "$C_BOLD" "$*" "$C_RESET"; }
info()  { printf '     %s\n' "$*"; }
ok()    { printf '     %s✓%s %s\n' "$C_GREEN" "$C_RESET" "$*"; }
warn()  { printf '     %s!%s %s\n' "$C_YELLOW" "$C_RESET" "$*" >&2; }
die()   { printf '\n%s✗ FAILED:%s %s\n' "$C_RED" "$C_RESET" "$*" >&2; exit 1; }

on_error() {
  local exit_code=$? line=$1
  printf '\n%s✗ Deployment failed%s at line %s (exit %s)\n' "$C_RED" "$C_RESET" "$line" "$exit_code" >&2
  printf '  Last command: %s\n' "${BASH_COMMAND}" >&2
  printf '\n  The system may be partially configured. Inspect with:\n' >&2
  printf '    systemctl status %s-api\n' "$APP_NAME" >&2
  printf '    journalctl -u %s-api -n 50 --no-pager\n' "$APP_NAME" >&2
  printf '  Then re-run this script; it is idempotent and will converge.\n' >&2
  exit "$exit_code"
}
trap 'on_error $LINENO' ERR

run() {
  if [[ "$DRY_RUN" == "1" ]]; then
    printf '     %s[dry-run]%s %s\n' "$C_YELLOW" "$C_RESET" "$*"
  else
    "$@"
  fi
}

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-browsers) SKIP_BROWSERS=1; shift ;;
    --with-obs)      WITH_OBS=1; shift ;;
    --with-tls)      WITH_TLS=1; shift ;;
    --domain)        DOMAIN="$2"; shift 2 ;;
    --port)          FRONTEND_PORT="$2"; shift 2 ;;
    --uninstall)     UNINSTALL=1; shift ;;
    --dry-run)       DRY_RUN=1; shift ;;
    -h|--help)       sed -n '2,30p' "$0"; exit 0 ;;
    *) die "Unknown argument: $1 (try --help)" ;;
  esac
done

[[ "$WITH_TLS" == "1" && -z "$DOMAIN" ]] && die "--with-tls requires --domain"

# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------

preflight() {
  step "Preflight checks"

  [[ "$EUID" -eq 0 ]] || die "This script must run as root: sudo $0"

  [[ -f /etc/os-release ]] || die "Cannot identify the OS: /etc/os-release is missing"
  # shellcheck disable=SC1091
  . /etc/os-release

  if [[ "${ID:-}" != "ubuntu" ]]; then
    warn "This script targets Ubuntu; detected ${PRETTY_NAME:-unknown}."
    warn "Debian derivatives usually work. Continuing in 5 seconds - Ctrl-C to abort."
    sleep 5
  else
    ok "Ubuntu ${VERSION_ID}"
    case "${VERSION_ID}" in
      22.04|24.04) ;;
      *) warn "Tested on 22.04 and 24.04; ${VERSION_ID} is untested." ;;
    esac
  fi

  local arch; arch="$(dpkg --print-architecture)"
  ok "architecture ${arch}"
  [[ "$arch" == "amd64" || "$arch" == "arm64" ]] \
    || warn "Browser packages below may not exist for ${arch}."

  # Disk. A build plus node_modules plus the venv needs roughly 3 GB; running
  # out halfway through leaves apt in a state that needs manual repair.
  local free_mb; free_mb=$(df -Pm /opt | awk 'NR==2 {print $4}')
  info "free space on /opt: ${free_mb} MB"
  (( free_mb >= 3000 )) || die "At least 3 GB free is required on /opt; ${free_mb} MB available."

  local mem_mb; mem_mb=$(awk '/MemTotal/ {print int($2/1024)}' /proc/meminfo)
  info "memory: ${mem_mb} MB"
  if (( mem_mb < 2048 )); then
    warn "Under 2 GB of RAM. The Vite build is memory-hungry and may be OOM-killed."
    warn "A swap file is added later in that case."
  fi

  # An apt lock held by unattended-upgrades is THE most common cause of a
  # failed first deploy on a fresh cloud image. Wait rather than fail.
  if fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1; then
    warn "Another package manager holds the dpkg lock (usually unattended-upgrades)."
    info "Waiting up to 300s for it to finish..."
    local waited=0
    while fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1; do
      sleep 5; waited=$((waited + 5))
      (( waited >= 300 )) && die "dpkg lock still held after 300s. Retry later, or: sudo systemctl stop unattended-upgrades"
    done
    ok "lock released after ${waited}s"
  fi

  run systemctl is-system-running >/dev/null 2>&1 || warn "systemd reports a degraded state; continuing."
  ok "preflight complete"
}

# ---------------------------------------------------------------------------
# Uninstall
# ---------------------------------------------------------------------------

uninstall() {
  step "Uninstalling MedSimQA"
  for unit in "${APP_NAME}-api" "${APP_NAME}-kiosk"; do
    if systemctl list-unit-files | grep -q "^${unit}.service"; then
      run systemctl disable --now "${unit}.service" || true
      run rm -f "/etc/systemd/system/${unit}.service"
      ok "removed ${unit}.service"
    fi
  done
  run systemctl daemon-reload

  run rm -f /etc/nginx/sites-enabled/"${APP_NAME}" /etc/nginx/sites-available/"${APP_NAME}"
  systemctl is-active --quiet nginx && run nginx -t && run systemctl reload nginx || true

  run rm -f /etc/logrotate.d/"${APP_NAME}"
  run rm -rf "$APP_ROOT"

  # Data is deliberately preserved. An operator who wants it gone can say so;
  # a script that silently deletes a database during an uninstall is a script
  # nobody runs twice.
  warn "Left in place: ${DATA_ROOT} (database) and ${LOG_ROOT} (logs)"
  warn "Remove them manually if intended:  sudo rm -rf ${DATA_ROOT} ${LOG_ROOT}"
  warn "The '${APP_USER}' system user was also left in place."

  ok "uninstall complete"
  exit 0
}

# ---------------------------------------------------------------------------
# System packages
# ---------------------------------------------------------------------------

install_system_packages() {
  step "Installing system packages"

  export DEBIAN_FRONTEND=noninteractive
  run apt-get update -qq

  # curl and gnupg are needed before the third-party repositories below.
  local packages=(
    ca-certificates curl gnupg lsb-release apt-transport-https
    build-essential pkg-config git
    nginx
    ufw
    logrotate
    jq
    unzip
  )

  info "installing: ${packages[*]}"
  run apt-get install -y -qq "${packages[@]}"
  ok "base packages installed"
}

# ---------------------------------------------------------------------------
# Python
# ---------------------------------------------------------------------------

version_at_least() {
  # Returns 0 if $1 >= $2, comparing dotted versions.
  printf '%s\n%s\n' "$2" "$1" | sort -V -C
}

install_python() {
  step "Installing Python ${PYTHON_MIN}+"

  local current=""
  if command -v python3 >/dev/null 2>&1; then
    current="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
    info "system python3: ${current}"
  fi

  if [[ -n "$current" ]] && version_at_least "$current" "$PYTHON_MIN"; then
    ok "python ${current} satisfies the >= ${PYTHON_MIN} requirement"
  else
    warn "python ${current:-none} is older than ${PYTHON_MIN}; installing from deadsnakes"
    # ------------------------------------------------------------------
    # CONFLICT: on Ubuntu 22.04 the system python3 is 3.10, and several
    # OS tools (notably apt itself via python3-apt) are bound to it.
    # Replacing /usr/bin/python3 breaks apt in a way that is genuinely
    # painful to recover from. So we INSTALL ALONGSIDE and point only the
    # application's venv at the new interpreter - never update-alternatives.
    # ------------------------------------------------------------------
    run add-apt-repository -y ppa:deadsnakes/ppa
    run apt-get update -qq
    run apt-get install -y -qq python3.11 python3.11-venv python3.11-dev
    ok "python3.11 installed alongside the system python (system python3 untouched)"
  fi

  # python3-venv is a separate package on Ubuntu and its absence produces the
  # infamous "ensurepip is not available" error, which reads like a Python bug.
  local py; py="$(select_python)"
  if ! "$py" -c 'import venv, ensurepip' >/dev/null 2>&1; then
    local suffix; suffix="$("$py" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
    warn "venv/ensurepip missing for ${py}; installing python${suffix}-venv"
    run apt-get install -y -qq "python${suffix}-venv"
  fi
  ok "using interpreter: $(select_python)"
}

select_python() {
  for candidate in python3.13 python3.12 python3.11 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
      local version; version="$("$candidate" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || echo 0)"
      if version_at_least "$version" "$PYTHON_MIN"; then
        command -v "$candidate"
        return 0
      fi
    fi
  done
  die "No Python >= ${PYTHON_MIN} found after installation."
}

# ---------------------------------------------------------------------------
# Node.js
# ---------------------------------------------------------------------------

install_node() {
  step "Installing Node.js ${NODE_MAJOR} LTS"

  if command -v node >/dev/null 2>&1; then
    local current; current="$(node --version | sed 's/^v//')"
    local major="${current%%.*}"
    info "existing node: v${current}"
    if (( major >= NODE_MAJOR )); then
      ok "node v${current} is recent enough"
      return 0
    fi
    warn "node v${current} is older than ${NODE_MAJOR}; upgrading"
    # ------------------------------------------------------------------
    # CONFLICT: Ubuntu's `nodejs` package and NodeSource's both provide
    # /usr/bin/node, and having both installed produces "dpkg: error
    # processing archive ... trying to overwrite /usr/include/node/common.gypi".
    # The Ubuntu package also ships npm separately, which then mismatches.
    # Removing both first is what avoids that.
    # ------------------------------------------------------------------
    run apt-get remove -y -qq nodejs npm libnode-dev || true
    run apt-get autoremove -y -qq || true
  fi

  info "adding the NodeSource repository"
  run install -d -m 0755 /usr/share/keyrings
  if [[ "$DRY_RUN" != "1" ]]; then
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key \
      | gpg --dearmor --yes -o /usr/share/keyrings/nodesource.gpg
    chmod 0644 /usr/share/keyrings/nodesource.gpg
    printf 'deb [signed-by=/usr/share/keyrings/nodesource.gpg] https://deb.nodesource.com/node_%s.x nodistro main\n' \
      "$NODE_MAJOR" > /etc/apt/sources.list.d/nodesource.list
  fi

  run apt-get update -qq
  run apt-get install -y -qq nodejs

  [[ "$DRY_RUN" == "1" ]] || ok "node $(node --version), npm $(npm --version)"
}

# ---------------------------------------------------------------------------
# Browsers
# ---------------------------------------------------------------------------

install_browsers() {
  [[ "$SKIP_BROWSERS" == "1" ]] && { info "skipping browsers (--skip-browsers)"; return 0; }
  step "Installing browsers (Chrome and Brave)"

  # ------------------------------------------------------------------------
  # CONFLICT, and the one that surprises people: on Ubuntu 22.04+ the
  # `chromium-browser` apt package is a TRANSITIONAL SNAP wrapper. Installing
  # it pulls in snapd, and the resulting confined browser cannot read
  # /var/lib/medsim or drive a kiosk session reliably. So we install Google
  # Chrome from Google's own .deb repository instead, and never touch
  # chromium-browser.
  # ------------------------------------------------------------------------
  if dpkg -l chromium-browser 2>/dev/null | grep -q '^ii'; then
    warn "the snap-backed chromium-browser package is installed."
    warn "It is confined and cannot reliably drive a kiosk session."
    warn "Consider: sudo apt remove chromium-browser && sudo snap remove chromium"
  fi

  # --- Google Chrome ---
  if command -v google-chrome >/dev/null 2>&1; then
    ok "google-chrome already installed ($(google-chrome --version 2>/dev/null || echo present))"
  else
    info "adding Google's repository"
    if [[ "$DRY_RUN" != "1" ]]; then
      curl -fsSL https://dl.google.com/linux/linux_signing_key.pub \
        | gpg --dearmor --yes -o /usr/share/keyrings/google-chrome.gpg
      chmod 0644 /usr/share/keyrings/google-chrome.gpg
      printf 'deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] https://dl.google.com/linux/chrome/deb/ stable main\n' \
        > /etc/apt/sources.list.d/google-chrome.list
    fi
    run apt-get update -qq
    run apt-get install -y -qq google-chrome-stable \
      || warn "Chrome install failed (expected on arm64, where Google ships no .deb)"
  fi

  # --- Brave ---
  if command -v brave-browser >/dev/null 2>&1; then
    ok "brave-browser already installed"
  else
    info "adding Brave's repository"
    if [[ "$DRY_RUN" != "1" ]]; then
      curl -fsSL https://brave-browser-apt-release.s3.brave.com/brave-browser-archive-keyring.gpg \
        -o /usr/share/keyrings/brave-browser-archive-keyring.gpg
      chmod 0644 /usr/share/keyrings/brave-browser-archive-keyring.gpg
      printf 'deb [signed-by=/usr/share/keyrings/brave-browser-archive-keyring.gpg] https://brave-browser-apt-release.s3.brave.com/ stable main\n' \
        > /etc/apt/sources.list.d/brave-browser-release.list
    fi
    run apt-get update -qq
    run apt-get install -y -qq brave-browser || warn "Brave install failed; continuing without it"
  fi

  ok "browser installation finished"
}

# ---------------------------------------------------------------------------
# Application user and directories
# ---------------------------------------------------------------------------

create_user_and_dirs() {
  step "Creating the service account and directories"

  if id "$APP_USER" >/dev/null 2>&1; then
    ok "user ${APP_USER} exists"
  else
    # A system account with no login shell and no home in /home: this process
    # serves HTTP and must not be a usable login.
    run useradd --system --create-home --home-dir "$DATA_ROOT" \
      --shell /usr/sbin/nologin --comment "MedSimQA service account" "$APP_USER"
    ok "created system user ${APP_USER}"
  fi

  for dir in "$APP_ROOT" "$DATA_ROOT" "$LOG_ROOT"; do
    run install -d -o "$APP_USER" -g "$APP_GROUP" -m 0750 "$dir"
  done
  # nginx (www-data) must traverse the app root to serve the built frontend.
  run chmod 0755 "$APP_ROOT"
  ok "directories ready"
}

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

deploy_backend() {
  step "Deploying the backend"

  [[ -d "${REPO_ROOT}/backend" ]] || die "Backend source not found at ${REPO_ROOT}/backend"

  info "copying source to ${APP_ROOT}/backend"
  run rm -rf "${APP_ROOT}/backend"
  run install -d -o "$APP_USER" -g "$APP_GROUP" "${APP_ROOT}/backend"
  run cp -r "${REPO_ROOT}/backend/app" "${REPO_ROOT}/backend/data" \
    "${REPO_ROOT}/backend/requirements.txt" "${APP_ROOT}/backend/"
  run cp -r "${REPO_ROOT}/ml" "${APP_ROOT}/ml"
  run chown -R "$APP_USER:$APP_GROUP" "${APP_ROOT}/backend" "${APP_ROOT}/ml"

  local py; py="$(select_python)"
  info "creating the virtual environment with ${py}"
  run rm -rf "$VENV"
  run sudo -u "$APP_USER" "$py" -m venv "$VENV"

  info "installing Python dependencies"
  run sudo -u "$APP_USER" "${VENV}/bin/pip" install --quiet --upgrade pip setuptools wheel
  run sudo -u "$APP_USER" "${VENV}/bin/pip" install --quiet -r "${APP_ROOT}/backend/requirements.txt" \
    || die "Dependency installation failed. If it was psycopg, either install libpq-dev or drop psycopg from requirements.txt (SQLite is the default)."
  ok "backend dependencies installed"

  # --- environment file ---
  local env_file="${APP_ROOT}/backend/.env"
  if [[ -f "$env_file" ]]; then
    ok "existing .env preserved (secrets not regenerated)"
  else
    info "generating ${env_file} with a fresh secret"
    if [[ "$DRY_RUN" != "1" ]]; then
      local secret; secret="$(openssl rand -hex 32)"
      cat > "$env_file" <<EOF
# Generated by deploy-ubuntu.sh on $(date -Is)
# Regenerating MEDSIM_JWT_SECRET invalidates every issued token.

MEDSIM_ENVIRONMENT=production
MEDSIM_DEBUG=false
MEDSIM_LOG_LEVEL=INFO
MEDSIM_LOG_JSON=true

MEDSIM_HOST=127.0.0.1
MEDSIM_PORT=${BACKEND_PORT}
MEDSIM_DATABASE_URL=sqlite:///${DATA_ROOT}/medsim.db

MEDSIM_JWT_SECRET=${secret}
MEDSIM_CORS_ORIGINS=${DOMAIN:+https://${DOMAIN},}http://localhost,http://127.0.0.1

MEDSIM_AUTO_SEED=true
MEDSIM_RESEED_ON_BOOT=false

# The chaos layer is a QA affordance. The application refuses to start with it
# enabled while MEDSIM_ENVIRONMENT=production; this line is belt and braces.
MEDSIM_CHAOS_ENABLED=false
EOF
      chown "$APP_USER:$APP_GROUP" "$env_file"
      chmod 0600 "$env_file"
    fi
    ok "environment file written (mode 0600)"
  fi

  info "seeding the database"
  run sudo -u "$APP_USER" env -C "${APP_ROOT}/backend" "${VENV}/bin/python" -m app.seed \
    || die "Seeding failed. Validate the corpus with: ${VENV}/bin/python -m app.seed --validate"
  ok "database seeded at ${DATA_ROOT}/medsim.db"
}

deploy_frontend() {
  step "Building and deploying the frontend"

  [[ -d "${REPO_ROOT}/frontend" ]] || die "Frontend source not found at ${REPO_ROOT}/frontend"

  local build_dir="/tmp/${APP_NAME}-build-$$"
  run rm -rf "$build_dir"
  run mkdir -p "$build_dir"
  run cp -r "${REPO_ROOT}/frontend/." "$build_dir/"
  run rm -rf "${build_dir}/node_modules" "${build_dir}/dist"

  # Low-memory hosts OOM during the Vite build. Adding swap is less surprising
  # than a build that dies with a bare "Killed".
  local mem_mb; mem_mb=$(awk '/MemTotal/ {print int($2/1024)}' /proc/meminfo)
  if (( mem_mb < 2048 )) && [[ ! -f /swapfile ]]; then
    warn "adding a 2 GB swap file for the build"
    run fallocate -l 2G /swapfile
    run chmod 600 /swapfile
    run mkswap /swapfile
    run swapon /swapfile
    grep -q '/swapfile' /etc/fstab || run bash -c 'echo "/swapfile none swap sw 0 0" >> /etc/fstab'
  fi

  info "installing npm dependencies (this is the slow step)"
  run bash -c "cd '$build_dir' && npm ci --no-audit --no-fund --loglevel=error" \
    || run bash -c "cd '$build_dir' && npm install --no-audit --no-fund --loglevel=error" \
    || die "npm install failed. Check network egress and any corporate proxy settings."

  info "building"
  run bash -c "cd '$build_dir' && NODE_OPTIONS=--max-old-space-size=1536 npm run build" \
    || die "Frontend build failed. Reproduce with: cd ${REPO_ROOT}/frontend && npm run build"

  run rm -rf "${APP_ROOT}/frontend"
  run install -d -o "$APP_USER" -g "$APP_GROUP" -m 0755 "${APP_ROOT}/frontend"
  run cp -r "${build_dir}/dist/." "${APP_ROOT}/frontend/"
  run chown -R "$APP_USER:$APP_GROUP" "${APP_ROOT}/frontend"
  run chmod -R a+rX "${APP_ROOT}/frontend"
  run rm -rf "$build_dir"

  ok "frontend built and installed to ${APP_ROOT}/frontend"
}

# ---------------------------------------------------------------------------
# systemd
# ---------------------------------------------------------------------------

install_systemd_units() {
  step "Installing systemd units"

  local src="${SCRIPT_DIR}/systemd"
  [[ -d "$src" ]] || die "systemd unit templates not found at ${src}"

  for unit in "${APP_NAME}-api.service"; do
    info "installing ${unit}"
    run install -m 0644 "${src}/${unit}" "/etc/systemd/system/${unit}"
  done

  run systemctl daemon-reload
  run systemctl enable "${APP_NAME}-api.service"
  run systemctl restart "${APP_NAME}-api.service"

  if [[ "$DRY_RUN" != "1" ]]; then
    info "waiting for the API to become healthy"
    local waited=0
    until curl -sf "http://127.0.0.1:${BACKEND_PORT}/healthz" >/dev/null 2>&1; do
      sleep 1; waited=$((waited + 1))
      if (( waited >= 45 )); then
        journalctl -u "${APP_NAME}-api" -n 40 --no-pager >&2
        die "API did not become healthy within 45s. Logs above."
      fi
    done
    ok "API healthy after ${waited}s"

    local ready; ready="$(curl -sf "http://127.0.0.1:${BACKEND_PORT}/readyz" || echo '{}')"
    local cases; cases="$(printf '%s' "$ready" | jq -r '.case_count // 0' 2>/dev/null || echo 0)"
    if [[ "$cases" -ge 25 ]]; then
      ok "corpus loaded: ${cases} cases"
    else
      warn "readiness reports only ${cases} cases; expected at least 25"
    fi
  fi
}

# ---------------------------------------------------------------------------
# nginx
# ---------------------------------------------------------------------------

configure_nginx() {
  step "Configuring nginx"

  local conf="/etc/nginx/sites-available/${APP_NAME}"
  local server_name="${DOMAIN:-_}"

  if [[ "$DRY_RUN" != "1" ]]; then
    cat > "$conf" <<EOF
# MedSimQA - generated by deploy-ubuntu.sh on $(date -Is)
#
# The frontend is a static SPA; the backend is reverse-proxied under /api.
# Serving both from one origin is what keeps the CSP's connect-src 'self'
# honest and removes CORS from the browser's path entirely.

upstream ${APP_NAME}_api {
    server 127.0.0.1:${BACKEND_PORT} fail_timeout=0;
    keepalive 16;
}

server {
    listen ${FRONTEND_PORT};
    listen [::]:${FRONTEND_PORT};
    server_name ${server_name};

    root ${APP_ROOT}/frontend;
    index index.html;

    access_log ${LOG_ROOT}/nginx-access.log;
    error_log  ${LOG_ROOT}/nginx-error.log warn;

    # The app's own CSP is served by the API for its responses; these are the
    # transport-level headers nginx is responsible for.
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header Referrer-Policy "no-referrer" always;
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;

    client_max_body_size 8m;

    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/javascript application/json image/svg+xml;

    # Hashed assets are immutable by construction, so they can be cached hard.
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        try_files \$uri =404;
    }

    # index.html must NEVER be cached: it is what points at the hashed assets,
    # and a cached copy pins users to a previous deployment.
    location = /index.html {
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        expires -1;
    }

    location /api/ {
        proxy_pass http://${APP_NAME}_api;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Connection "";

        # Generous, because the evaluation batch endpoint is legitimately slow.
        proxy_connect_timeout 5s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # Pass the request id through in both directions so a trace survives
        # the hop.
        proxy_set_header X-Request-ID \$request_id;
        add_header X-Request-ID \$request_id always;
    }

    location = /healthz { proxy_pass http://${APP_NAME}_api; access_log off; }
    location = /readyz  { proxy_pass http://${APP_NAME}_api; access_log off; }

    # SPA fallback. Every unmatched path returns index.html so client-side
    # routes such as /cases/THY-001 are shareable and survive a reload.
    location / {
        try_files \$uri \$uri/ /index.html;
    }
}
EOF
  fi

  run ln -sf "$conf" "/etc/nginx/sites-enabled/${APP_NAME}"

  # The default site binds :80 and would shadow ours.
  if [[ -e /etc/nginx/sites-enabled/default ]]; then
    info "removing the default nginx site (it would shadow this one on :80)"
    run rm -f /etc/nginx/sites-enabled/default
  fi

  run nginx -t || die "nginx configuration test failed; the generated file is at ${conf}"
  run systemctl enable nginx
  run systemctl reload nginx
  ok "nginx serving on port ${FRONTEND_PORT}"

  if [[ "$WITH_TLS" == "1" ]]; then
    info "requesting a certificate for ${DOMAIN}"
    run apt-get install -y -qq certbot python3-certbot-nginx
    run certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos \
      --register-unsafely-without-email --redirect \
      || warn "certbot failed. DNS must resolve ${DOMAIN} to this host and :80 must be reachable."
  fi
}

# ---------------------------------------------------------------------------
# Firewall and log rotation
# ---------------------------------------------------------------------------

configure_firewall() {
  step "Configuring the firewall"

  # Order matters: allowing SSH BEFORE enabling ufw is what prevents locking
  # yourself out of a remote host. This has bitten everyone once.
  run ufw allow OpenSSH >/dev/null 2>&1 || run ufw allow 22/tcp >/dev/null
  ok "SSH allowed"

  run ufw allow "${FRONTEND_PORT}/tcp" >/dev/null
  [[ "$WITH_TLS" == "1" ]] && run ufw allow 443/tcp >/dev/null

  # The API is bound to loopback and reached only through nginx; opening 8000
  # would bypass the reverse proxy and its headers.
  info "port ${BACKEND_PORT} deliberately NOT opened (loopback only, proxied by nginx)"

  if ufw status | grep -q "Status: active"; then
    ok "ufw already active"
  else
    run bash -c "yes | ufw enable" >/dev/null
    ok "ufw enabled"
  fi
  [[ "$DRY_RUN" == "1" ]] || ufw status numbered | sed 's/^/     /'
}

configure_logrotate() {
  step "Configuring log rotation"
  if [[ "$DRY_RUN" != "1" ]]; then
    cat > "/etc/logrotate.d/${APP_NAME}" <<EOF
${LOG_ROOT}/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 ${APP_USER} ${APP_GROUP}
    sharedscripts
    postrotate
        # nginx keeps its log file handles open; without this it writes to the
        # rotated inode and the new file stays empty.
        [ -f /var/run/nginx.pid ] && kill -USR1 \$(cat /var/run/nginx.pid) || true
    endscript
}
EOF
  fi
  run logrotate -d "/etc/logrotate.d/${APP_NAME}" >/dev/null 2>&1 || warn "logrotate config test reported issues"
  ok "log rotation configured (14 days)"
}

# ---------------------------------------------------------------------------
# OBS
# ---------------------------------------------------------------------------

install_obs() {
  [[ "$WITH_OBS" == "1" ]] || return 0
  step "Installing OBS Studio and the virtual camera"

  run add-apt-repository -y ppa:obsproject/obs-studio
  run apt-get update -qq
  run apt-get install -y -qq obs-studio v4l2loopback-dkms v4l-utils ffmpeg

  # ------------------------------------------------------------------------
  # CONFLICT: OBS's virtual camera needs the v4l2loopback kernel module, which
  # is built by DKMS against the RUNNING kernel. On a host that has been
  # upgraded but not rebooted, the module builds against the new kernel and
  # fails to load into the old one, with a "module not found" that has nothing
  # to do with the installation.
  # ------------------------------------------------------------------------
  if [[ "$DRY_RUN" != "1" ]]; then
    if ! modprobe v4l2loopback exclusive_caps=1 card_label="MedSimQA Virtual Camera" 2>/dev/null; then
      warn "v4l2loopback failed to load."
      warn "If the kernel was updated recently, reboot and re-run:"
      warn "  sudo modprobe v4l2loopback exclusive_caps=1 card_label='MedSimQA Virtual Camera'"
    else
      ok "v4l2loopback loaded"
      # Persist across reboots.
      echo "v4l2loopback" > /etc/modules-load.d/v4l2loopback.conf
      echo "options v4l2loopback exclusive_caps=1 card_label=\"MedSimQA Virtual Camera\"" \
        > /etc/modprobe.d/v4l2loopback.conf
      ok "module configured to load at boot"
    fi
  fi

  run install -d -m 0755 "${APP_ROOT}/obs"
  if [[ -d "${SCRIPT_DIR}/obs" ]]; then
    run cp -r "${SCRIPT_DIR}/obs/." "${APP_ROOT}/obs/"
    ok "OBS scene collection and profile installed to ${APP_ROOT}/obs"
    info "import via OBS: Scene Collection > Import, then Profile > Import"
  fi
}

# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

verify() {
  step "Verifying the deployment"
  [[ "$DRY_RUN" == "1" ]] && { info "skipped in dry-run"; return 0; }

  local failures=0
  check() {
    local name="$1"; shift
    if "$@" >/dev/null 2>&1; then ok "$name"; else warn "$name FAILED"; failures=$((failures + 1)); fi
  }

  check "API service is active"       systemctl is-active --quiet "${APP_NAME}-api"
  check "nginx is active"             systemctl is-active --quiet nginx
  check "API liveness"                curl -sf "http://127.0.0.1:${BACKEND_PORT}/healthz"
  check "API readiness"               curl -sf "http://127.0.0.1:${BACKEND_PORT}/readyz"
  check "frontend index is served"    curl -sf "http://127.0.0.1:${FRONTEND_PORT}/"
  check "API proxied through nginx"   curl -sf "http://127.0.0.1:${FRONTEND_PORT}/api/v1/cases?limit=1"
  check "SPA deep link falls back"    curl -sf "http://127.0.0.1:${FRONTEND_PORT}/cases/THY-001"
  check "database is present"         test -f "${DATA_ROOT}/medsim.db"

  # The production configuration must actually be production.
  if curl -sf "http://127.0.0.1:${BACKEND_PORT}/readyz" | grep -q '"chaos":"disabled"'; then
    ok "chaos layer disabled"
  else
    warn "chaos layer is NOT disabled - check MEDSIM_CHAOS_ENABLED"; failures=$((failures + 1))
  fi

  local count
  count="$(curl -sf "http://127.0.0.1:${FRONTEND_PORT}/api/v1/cases/stats" | jq -r '.total_cases // 0' 2>/dev/null || echo 0)"
  if [[ "$count" -ge 25 ]]; then ok "corpus: ${count} cases"; else warn "only ${count} cases loaded"; failures=$((failures + 1)); fi

  echo
  if (( failures == 0 )); then
    printf '%s✓ All checks passed%s\n' "$C_GREEN" "$C_RESET"
  else
    printf '%s! %d check(s) failed%s\n' "$C_YELLOW" "$failures" "$C_RESET"
    return 1
  fi
}

summary() {
  local address="http://$(hostname -I 2>/dev/null | awk '{print $1}'):${FRONTEND_PORT}"
  [[ -n "$DOMAIN" ]] && address="http${WITH_TLS:+s}://${DOMAIN}"

  cat <<EOF

${C_BOLD}MedSimQA is deployed.${C_RESET}

  Dashboard   ${address}
  API docs    ${address}/docs
  Health      ${address}/healthz

  Service     systemctl status ${APP_NAME}-api
  Logs        journalctl -u ${APP_NAME}-api -f
  Restart     systemctl restart ${APP_NAME}-api
  Config      ${APP_ROOT}/backend/.env  (mode 0600)
  Database    ${DATA_ROOT}/medsim.db

  Re-run this script to update; it is idempotent.
  Remove with: sudo $0 --uninstall

EOF
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

main() {
  printf '%s\n' "${C_BOLD}MedSimQA deployment${C_RESET}"
  [[ "$DRY_RUN" == "1" ]] && warn "DRY RUN - no changes will be made"

  [[ "$UNINSTALL" == "1" ]] && uninstall

  preflight
  install_system_packages
  install_python
  install_node
  install_browsers
  create_user_and_dirs
  deploy_backend
  deploy_frontend
  install_systemd_units
  configure_nginx
  configure_firewall
  configure_logrotate
  install_obs
  verify
  summary
}

main "$@"
