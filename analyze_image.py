#!/usr/bin/env python3
"""Usage: analyze_image.py <image> [prompt]   (needs ANTHROPIC_API_KEY)"""
# Standard library imports only — no third-party SDK is needed since we call the
# Anthropic HTTP API directly via urllib.
import base64, json, os, sys, urllib.request, urllib.error

# Map of supported image file extensions to their corresponding MIME media types.
# The Anthropic API requires the media_type to be specified for base64 image content.
MEDIA = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
         ".gif": "image/gif", ".webp": "image/webp"}

# Show usage and exit if no image path was provided or help was requested.
if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
    sys.exit(__doc__)
# First positional argument is the image path; remaining args form the prompt.
path = sys.argv[1]
prompt = " ".join(sys.argv[2:]) or "Describe this image in detail."
# API key must be present in the environment; abort early with a clear message otherwise.
key = os.environ.get("ANTHROPIC_API_KEY") or sys.exit("error: ANTHROPIC_API_KEY not set")
# Validate the file extension against the supported MIME map before reading the file.
ext = os.path.splitext(path)[1].lower()
if ext not in MEDIA:
    sys.exit(f"error: unsupported format {ext!r}")
# Read the image and base64-encode it so it can be embedded in the JSON request body.
with open(path, "rb") as f:
    data = base64.standard_b64encode(f.read()).decode()

# Build the POST request to the Messages API with a single user message
# containing the image followed by the text prompt.
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
# Send the request and surface API-level errors with status code and body for debugging.
try:
    resp = json.loads(urllib.request.urlopen(req, timeout=120).read())
except urllib.error.HTTPError as e:
    sys.exit(f"API error {e.code}: {e.read().decode('utf-8', 'replace')}")

# The response's content is a list of blocks; print only the text blocks joined by newlines.
print("\n".join(b["text"] for b in resp["content"] if b["type"] == "text"))
