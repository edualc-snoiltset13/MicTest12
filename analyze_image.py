#!/usr/bin/env python3
"""
Image Analysis Script
A small CLI that sends a local image to Claude's vision API and prints
the model's description. Uses only the Python standard library.

Usage:
  export ANTHROPIC_API_KEY=sk-ant-...
  python analyze_image.py path/to/image.jpg
  python analyze_image.py photo.png --prompt "Transcribe any text."
"""

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request


# ── Constants ──────────────────────────────────────────────────────

API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_PROMPT = (
    "Describe this image in detail. Note key objects, people, setting, "
    "colors, text, and anything noteworthy."
)
DEFAULT_MAX_TOKENS = 1024
DEFAULT_TIMEOUT = 120.0
HARD_MAX_BYTES = 20 * 1024 * 1024
SOFT_MAX_BYTES = 5 * 1024 * 1024

MEDIA_TYPES = {
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png":  "image/png",
    ".gif":  "image/gif",
    ".webp": "image/webp",
}


# ── Image encoding ─────────────────────────────────────────────────


def encode_image(path):
    """Read an image from disk and return (media_type, base64_data)."""
    if not os.path.isfile(path):
        raise FileNotFoundError(f"image not found: {path}")

    ext = os.path.splitext(path)[1].lower()
    media_type = MEDIA_TYPES.get(ext)
    if media_type is None:
        supported = ", ".join(sorted(MEDIA_TYPES))
        raise ValueError(
            f"unsupported image format: {ext or '(none)'}. Supported: {supported}"
        )

    size = os.path.getsize(path)
    if size > HARD_MAX_BYTES:
        raise ValueError(
            f"image too large: {size} bytes (max {HARD_MAX_BYTES} bytes / 20 MB)"
        )
    if size > SOFT_MAX_BYTES:
        print(
            f"warning: image is {size / 1024 / 1024:.1f} MB; uploads may be slow.",
            file=sys.stderr,
        )

    with open(path, "rb") as f:
        raw = f.read()
    return media_type, base64.standard_b64encode(raw).decode("ascii")


# ── Request / response ────────────────────────────────────────────


def build_payload(b64, media_type, prompt, model, max_tokens):
    """Build the Anthropic /v1/messages JSON payload."""
    return {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": b64,
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    }


def call_anthropic(payload, api_key, timeout):
    """POST the payload to Anthropic and return the parsed JSON response."""
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(API_URL, data=body, method="POST")
    req.add_header("x-api-key", api_key)
    req.add_header("anthropic-version", ANTHROPIC_VERSION)
    req.add_header("content-type", "application/json")

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    return json.loads(raw.decode("utf-8"))


def extract_text(response):
    """Concatenate all text blocks from a messages response."""
    parts = []
    for block in response.get("content", []):
        if block.get("type") == "text":
            parts.append(block.get("text", ""))
    return "\n".join(parts) if parts else "(no text content returned)"


def format_api_error(err):
    """Turn an HTTPError into a human-readable one-liner."""
    try:
        body = err.read().decode("utf-8", errors="replace")
    except Exception:
        body = ""
    msg = None
    if body:
        try:
            obj = json.loads(body)
            msg = obj.get("error", {}).get("message")
        except Exception:
            msg = body.strip()
    if not msg:
        msg = err.reason or "unknown error"
    return f"API error {err.code}: {msg}"


# ── CLI ────────────────────────────────────────────────────────────


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Analyze a local image with Claude's vision API (stdlib only).",
        epilog=(
            "Example:\n"
            "  export ANTHROPIC_API_KEY=sk-ant-...\n"
            "  python analyze_image.py photo.jpg --prompt 'Is there text?'"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("image_path", help="Path to a local image file.")
    parser.add_argument(
        "-p", "--prompt", default=DEFAULT_PROMPT,
        help="Instruction sent alongside the image.",
    )
    parser.add_argument(
        "-m", "--model", default=DEFAULT_MODEL,
        help=f"Claude model ID (default: {DEFAULT_MODEL}).",
    )
    parser.add_argument(
        "--max-tokens", type=int, default=DEFAULT_MAX_TOKENS,
        help=f"Max response tokens (default: {DEFAULT_MAX_TOKENS}).",
    )
    parser.add_argument(
        "--timeout", type=float, default=DEFAULT_TIMEOUT,
        help=f"HTTP timeout in seconds (default: {DEFAULT_TIMEOUT}).",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Print the raw JSON API response instead of just the text.",
    )
    args = parser.parse_args(argv)
    if args.max_tokens < 1:
        parser.error("--max-tokens must be >= 1")
    if args.timeout <= 0:
        parser.error("--timeout must be > 0")
    return args


def main(argv=None):
    args = parse_args(argv)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("error: ANTHROPIC_API_KEY environment variable is not set",
              file=sys.stderr)
        return 2

    try:
        media_type, b64 = encode_image(args.image_path)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 3
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 3

    payload = build_payload(b64, media_type, args.prompt,
                            args.model, args.max_tokens)

    try:
        response = call_anthropic(payload, api_key, args.timeout)
    except urllib.error.HTTPError as e:
        print(format_api_error(e), file=sys.stderr)
        return 4
    except urllib.error.URLError as e:
        print(f"network error: {e.reason}", file=sys.stderr)
        return 5

    if args.json:
        json.dump(response, sys.stdout, indent=2)
        print()
    else:
        print(extract_text(response))
        usage = response.get("usage", {})
        print(
            f"[usage] input_tokens={usage.get('input_tokens')} "
            f"output_tokens={usage.get('output_tokens')} "
            f"model={response.get('model')}",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
