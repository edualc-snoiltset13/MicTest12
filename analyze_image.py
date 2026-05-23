#!/usr/bin/env python3
"""Analyze an image with Claude's vision API. Requires ANTHROPIC_API_KEY."""
import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request

MEDIA = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
         ".gif": "image/gif", ".webp": "image/webp"}
MAX_BYTES = 20 * 1024 * 1024

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("image", help="path to image file (jpg/jpeg/png/gif/webp)")
parser.add_argument("--prompt", default="Describe this image in detail.", help="prompt text to send with the image")
parser.add_argument("--model", default="claude-sonnet-4-6", help="model id (default: claude-sonnet-4-6)")
parser.add_argument("--max-tokens", type=int, default=1024, help="max output tokens (default: 1024)")
parser.add_argument("--json", dest="as_json", action="store_true", help="print raw API response as JSON")
args = parser.parse_args()

key = os.environ.get("ANTHROPIC_API_KEY")
if not key:
    print("error: ANTHROPIC_API_KEY not set", file=sys.stderr)
    sys.exit(2)

path = args.image
ext = os.path.splitext(path)[1].lower()
if not os.path.isfile(path):
    print(f"error: image not found: {path}", file=sys.stderr)
    sys.exit(3)
if ext not in MEDIA:
    print(f"error: unsupported format {ext!r}", file=sys.stderr)
    sys.exit(3)
if os.path.getsize(path) > MAX_BYTES:
    print(f"error: image exceeds 20 MB limit", file=sys.stderr)
    sys.exit(3)

with open(path, "rb") as f:
    data = base64.standard_b64encode(f.read()).decode()

req = urllib.request.Request(
    "https://api.anthropic.com/v1/messages",
    data=json.dumps({
        "model": args.model,
        "max_tokens": args.max_tokens,
        "messages": [{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64",
                                         "media_type": MEDIA[ext], "data": data}},
            {"type": "text", "text": args.prompt},
        ]}],
    }).encode(),
    headers={"x-api-key": key, "anthropic-version": "2023-06-01",
             "content-type": "application/json"},
)

try:
    resp = json.loads(urllib.request.urlopen(req, timeout=120).read())
except urllib.error.HTTPError as e:
    print(f"API error {e.code}: {e.read().decode('utf-8', 'replace')}", file=sys.stderr)
    sys.exit(4)
except urllib.error.URLError as e:
    print(f"network error: {e.reason}", file=sys.stderr)
    sys.exit(5)

if args.as_json:
    print(json.dumps(resp, indent=2))
else:
    print("\n".join(b["text"] for b in resp["content"] if b["type"] == "text"))
