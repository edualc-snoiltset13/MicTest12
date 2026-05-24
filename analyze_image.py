#!/usr/bin/env python3
"""Usage: analyze_image.py <image> [prompt]   (needs ANTHROPIC_API_KEY)"""
import base64, json, os, sys, urllib.request, urllib.error

MEDIA = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
         ".gif": "image/gif", ".webp": "image/webp"}

if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
    sys.exit(__doc__)
path = sys.argv[1]
prompt = " ".join(sys.argv[2:]) or "Describe this image in detail."
key = os.environ.get("ANTHROPIC_API_KEY") or sys.exit("error: ANTHROPIC_API_KEY not set")
ext = os.path.splitext(path)[1].lower()
if ext not in MEDIA:
    sys.exit(f"error: unsupported format {ext!r}")
with open(path, "rb") as f:
    data = base64.standard_b64encode(f.read()).decode()

req = urllib.request.Request(
    "https://api.anthropic.com/v1/messages",
    data=json.dumps({
        "model": "claude-sonnet-4-6",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64",
                                         "media_type": MEDIA[ext], "data": data}},
            {"type": "text", "text": prompt},
        ]}],
    }).encode(),
    headers={"x-api-key": key, "anthropic-version": "2023-06-01",
             "content-type": "application/json"},
)
try:
    resp = json.loads(urllib.request.urlopen(req, timeout=120).read())
except urllib.error.HTTPError as e:
    sys.exit(f"API error {e.code}: {e.read().decode('utf-8', 'replace')}")

print("\n".join(b["text"] for b in resp["content"] if b["type"] == "text"))
