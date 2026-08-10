#!/usr/bin/env bash
# Thin Buttondown API helper for the portfolio newsletter (andreslanzos).
# Auth lives outside the repo: ~/.config/portfolio/buttondown.env
set -euo pipefail

ENV_FILE="${BUTTONDOWN_ENV_FILE:-$HOME/.config/portfolio/buttondown.env}"

usage() {
  cat <<'EOF'
Usage: scripts/buttondown.sh <command> [args]

Commands:
  ping                 Verify the API key (GET /newsletters)
  newsletter           Show newsletter username + name
  subscribers [page]   List subscribers (default page size 20)
  emails [page]        List emails
  announce <article> [--dry-run|--send|--force]
                       Create a newsletter draft from an articles/ path
                       (see scripts/newsletter_from_article.py)
  get <path>           GET /v1/<path>  (example: get subscribers?page_size=5)
  post <path> <json>   POST /v1/<path> with a JSON body
  patch <path> <json>  PATCH /v1/<path> with a JSON body

Auth:
  Prefer BUTTONDOWN_API_KEY in the environment, otherwise load:
    ~/.config/portfolio/buttondown.env
EOF
}

load_env() {
  if [[ -n "${BUTTONDOWN_API_KEY:-}" ]]; then
    : "${BUTTONDOWN_API_BASE:=https://api.buttondown.com/v1}"
    return 0
  fi
  if [[ ! -f "$ENV_FILE" ]]; then
    echo "Missing Buttondown credentials." >&2
    echo "Expected $ENV_FILE or BUTTONDOWN_API_KEY in the environment." >&2
    exit 1
  fi
  # shellcheck disable=SC1090
  set -a
  source "$ENV_FILE"
  set +a
  : "${BUTTONDOWN_API_BASE:=https://api.buttondown.com/v1}"
  if [[ -z "${BUTTONDOWN_API_KEY:-}" ]]; then
    echo "BUTTONDOWN_API_KEY is empty in $ENV_FILE" >&2
    exit 1
  fi
}

api() {
  local method="$1"
  local path="${2#/}"
  local body="${3:-}"
  local url="${BUTTONDOWN_API_BASE%/}/$path"
  if [[ -n "$body" ]]; then
    curl -sS -X "$method" \
      -H "Authorization: Token ${BUTTONDOWN_API_KEY}" \
      -H "Content-Type: application/json" \
      -d "$body" \
      "$url"
  else
    curl -sS -X "$method" \
      -H "Authorization: Token ${BUTTONDOWN_API_KEY}" \
      "$url"
  fi
}

json_pretty() {
  if command -v python3 >/dev/null 2>&1; then
    python3 -m json.tool
  else
    cat
  fi
}

cmd="${1:-}"
shift || true

case "$cmd" in
  ""|-h|--help|help)
    usage
    exit 0
    ;;
esac

load_env

case "$cmd" in
  ping)
    api GET newsletters | python3 -c '
import json, sys
data = json.load(sys.stdin)
results = data.get("results", data if isinstance(data, list) else [data])
n = results[0]
print("ok · {} · {}".format(n.get("username"), n.get("name")))
'
    ;;
  newsletter)
    api GET newsletters | python3 -c '
import json, sys
data = json.load(sys.stdin)
results = data.get("results", data if isinstance(data, list) else [data])
n = results[0]
keep = ("id", "username", "name", "description", "creation_date", "status")
out = {k: n.get(k) for k in keep if k in n}
print(json.dumps(out, indent=2))
'
    ;;
  subscribers)
    page_size="${1:-20}"
    api GET "subscribers?page_size=${page_size}" | json_pretty
    ;;
  emails)
    page_size="${1:-20}"
    api GET "emails?page_size=${page_size}" | json_pretty
    ;;
  announce)
    [[ $# -ge 1 ]] || { echo "announce requires an articles/ path" >&2; exit 1; }
    exec python3 "$(cd "$(dirname "$0")" && pwd)/newsletter_from_article.py" "$@"
    ;;
  get)
    [[ $# -ge 1 ]] || { echo "get requires a path" >&2; exit 1; }
    api GET "$1" | json_pretty
    ;;
  post)
    [[ $# -ge 2 ]] || { echo "post requires <path> <json>" >&2; exit 1; }
    api POST "$1" "$2" | json_pretty
    ;;
  patch)
    [[ $# -ge 2 ]] || { echo "patch requires <path> <json>" >&2; exit 1; }
    api PATCH "$1" "$2" | json_pretty
    ;;
  *)
    echo "Unknown command: $cmd" >&2
    usage >&2
    exit 1
    ;;
esac
