#!/usr/bin/env python3
"""Send a local image to Claude's vision API and print the response."""

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request

API_URL = "https://api.anthropic.com/v1/messages"
MEDIA = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
         ".gif": "image/gif", ".webp": "image/webp"}
DEFAULT_PROMPT = "Describe this image in detail."


def analyze(path, prompt, model, max_tokens, api_key, timeout=120):
    ext = os.path.splitext(path)[1].lower()
    if ext not in MEDIA:
        sys.exit(f"error: unsupported format {ext!r}; use {sorted(MEDIA)}")
    if not os.path.isfile(path):
        sys.exit(f"error: image not found: {path}")
    if os.path.getsize(path) > 20 * 1024 * 1024:
        sys.exit("error: image exceeds 20 MB API limit")

    with open(path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("ascii")

    payload = json.dumps({
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64",
                                         "media_type": MEDIA[ext], "data": data}},
            {"type": "text", "text": prompt},
        ]}],
    }).encode("utf-8")

    req = urllib.request.Request(API_URL, data=payload, method="POST", headers={
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        msg = (json.loads(body).get("error", {}).get("message")
               if body.startswith("{") else body) or e.reason
        sys.exit(f"API error {e.code}: {msg}")
    except urllib.error.URLError as e:
        sys.exit(f"network error: {e.reason}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("image_path")
    ap.add_argument("-p", "--prompt", default=DEFAULT_PROMPT)
    ap.add_argument("-m", "--model", default="claude-sonnet-4-6")
    ap.add_argument("--max-tokens", type=int, default=1024)
    args = ap.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("error: ANTHROPIC_API_KEY is not set")

    resp = analyze(args.image_path, args.prompt, args.model,
                   args.max_tokens, api_key)
    print("\n".join(b.get("text", "") for b in resp.get("content", [])
                    if b.get("type") == "text"))
    u = resp.get("usage", {})
    print(f"[usage] in={u.get('input_tokens')} out={u.get('output_tokens')} "
          f"model={resp.get('model')}", file=sys.stderr)


if __name__ == "__main__":
    main()
