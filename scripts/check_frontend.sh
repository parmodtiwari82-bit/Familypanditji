#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMP_JS="$(mktemp --suffix=.js)"
trap 'rm -f "$TEMP_JS"' EXIT

python - "$ROOT/index.html" "$TEMP_JS" <<'PY'
from html.parser import HTMLParser
from pathlib import Path
import sys

source, destination = map(Path, sys.argv[1:])

class InlineScriptExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.collecting = False
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "script":
            self.collecting = not any(key.lower() == "src" for key, _ in attrs)

    def handle_endtag(self, tag):
        if tag.lower() == "script":
            self.collecting = False

    def handle_data(self, data):
        if self.collecting:
            self.parts.append(data)

parser = InlineScriptExtractor()
parser.feed(source.read_text(encoding="utf-8"))
javascript = "\n".join(parser.parts)
if not javascript.strip():
    raise SystemExit("No inline JavaScript found in index.html")
destination.write_text(javascript, encoding="utf-8")
print(f"Extracted {len(javascript)} characters of inline JavaScript.")
PY

node --check "$TEMP_JS"
echo "Frontend JavaScript syntax check passed."
