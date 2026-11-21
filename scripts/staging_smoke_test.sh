#!/usr/bin/env bash
# Non-destructive staging smoke test for AI Family Pandit Ji.
# Usage: BASE_URL=https://staging.example.com bash scripts/staging_smoke_test.sh
set -Eeuo pipefail

BASE_URL="${BASE_URL:-${1:-}}"
if [[ -z "$BASE_URL" ]]; then
  echo "ERROR: set BASE_URL or pass the staging origin as the first argument." >&2
  exit 2
fi
BASE_URL="${BASE_URL%/}"
# Permit plain HTTP only for exact loopback hosts; prefix matching would also
# accept lookalike hosts such as localhost.attacker.example.
python3 - "$BASE_URL" <<'PY'
import sys
from urllib.parse import urlsplit

value = sys.argv[1]
try:
    parsed = urlsplit(value)
    hostname = (parsed.hostname or "").lower()
    _ = parsed.port  # Force validation of malformed ports.
except ValueError:
    raise SystemExit("ERROR: BASE_URL is not a valid URL.")
if parsed.scheme not in {"https", "http"} or not hostname:
    raise SystemExit("ERROR: BASE_URL must be an absolute HTTP(S) URL.")
if parsed.username or parsed.password or parsed.query or parsed.fragment:
    raise SystemExit("ERROR: BASE_URL must not contain credentials, query or fragment.")
if parsed.scheme == "http" and hostname not in {"localhost", "127.0.0.1", "::1"}:
    raise SystemExit("ERROR: use HTTPS for staging (HTTP is allowed only for exact loopback hosts).")
PY

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

request() {
  local method="$1" path="$2" expected="$3" output="$4"
  shift 4
  local status
  status="$(curl --silent --show-error --output "$output" --write-out '%{http_code}' \
    --connect-timeout 10 --max-time 45 -X "$method" "$BASE_URL$path" "$@")"
  if [[ "$status" != "$expected" ]]; then
    echo "FAIL $method $path: expected HTTP $expected, got $status" >&2
    cat "$output" >&2 || true
    exit 1
  fi
  echo "PASS $method $path -> $status"
}

for path in /health /ready /api/trust/status /api/release/readiness /api/modules \
  /api/panchang/overview /api/jyotish/guide /api/pandits /api/temples /api/search?q=Gayatri\&language=en \
  /api/mantras /api/puja-guides /api/samskaras /api/content/review-policy \
  /manifest.webmanifest /sw.js /icons/panditji.svg /privacy /terms; do
  safe_name="${path//\//_}"
  request GET "$path" 200 "$TMP_DIR/$safe_name"
done

request POST /api/ask 200 "$TMP_DIR/ask.json" \
  -H 'Content-Type: application/json' \
  --data '{"question":"गायत्री मंत्र का सामान्य अर्थ बताइए","language":"hi"}'
request POST /api/ask 422 "$TMP_DIR/invalid.json" \
  -H 'Content-Type: application/json' \
  --data '{"question":"hello","language":"fr"}'

request GET /api/release/readiness 200 "$TMP_DIR/readiness.json" \
  -D "$TMP_DIR/headers.txt"
grep -qi '^cache-control:.*no-store' "$TMP_DIR/headers.txt" || {
  echo "FAIL /api/release/readiness: Cache-Control no-store missing" >&2; exit 1;
}
grep -qi '^x-content-type-options: nosniff' "$TMP_DIR/headers.txt" || {
  echo "FAIL /api/release/readiness: X-Content-Type-Options missing" >&2; exit 1;
}
grep -qi '^x-frame-options: DENY' "$TMP_DIR/headers.txt" || {
  echo "FAIL /api/release/readiness: X-Frame-Options missing" >&2; exit 1;
}
python3 - "$TMP_DIR/readiness.json" "$TMP_DIR/ask.json" <<'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as f:
    readiness = json.load(f)
with open(sys.argv[2], encoding="utf-8") as f:
    answer = json.load(f)
assert "production_release_ready" in readiness, "readiness response missing release status"
assert isinstance(readiness.get("checks"), dict), "readiness checks missing"
assert isinstance(answer.get("answer"), str) and answer["answer"].strip(), "ask response missing answer"
print("PASS JSON contracts (readiness + ask)")
PY

echo "ALL STAGING SMOKE TESTS PASSED for $BASE_URL"
