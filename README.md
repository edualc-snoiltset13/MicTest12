# Barber Booking Agent

A simple Python CLI agent that manages barber appointment bookings with notifications for both the barber and the client.

## Features

- **Register barbers** with time slots, services, pricing, and email
- **Book appointments** by selecting a barber, date, slot, and service
- **Reschedule appointments** to a different date/time without cancelling
- **View all bookings** (upcoming and past) with service details
- **Cancel bookings** with confirmation
- **Search bookings** by barber or client name
- **Notifications** printed to console on every booking, reschedule, or cancellation
- **Email notifications** sent automatically when SMTP is configured

## Requirements

- Python 3.7+
- No external dependencies (uses only the standard library)

## Usage

```bash
python barber_booking_agent.py
```

Follow the interactive menu:

```
========================================
        Barber Booking Agent
========================================
  1. Register a barber
  2. List barbers
  3. Book an appointment
  4. View all bookings
  5. Cancel a booking
  6. Reschedule a booking
  7. Search bookings
  8. Exit
========================================
```

## Email Notifications (Optional)

Set these environment variables to enable email notifications:

```bash
export SMTP_HOST="smtp.example.com"
export SMTP_PORT="587"
export SMTP_USER="you@example.com"
export SMTP_PASS="your-password"
export SMTP_FROM="noreply@example.com"   # optional, defaults to SMTP_USER
```

When configured, emails are sent to both the barber and the client on booking, rescheduling, and cancellation. If SMTP is not configured, the agent works normally with console-only notifications.

## Data Storage

All bookings are persisted in a local `bookings.json` file so they survive between sessions.

## Image Analysis Script

Analyze an image using Claude's vision API. Standard library only — no pip install needed.

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python analyze_image.py path/to/image.jpg
python analyze_image.py photo.png --prompt "What text appears in this image?"
python analyze_image.py photo.webp --model claude-opus-4-7 --max-tokens 2048
python analyze_image.py photo.gif --json    # raw API response
```

Supported formats: JPEG, PNG, GIF, WebP (max 20 MB). Default model: `claude-sonnet-4-6`.

Exit codes: `0` success · `2` bad args / missing key · `3` image error · `4` API error · `5` network error.

## Compression Utility

`compression.py` provides streaming gzip helpers built on the standard library.
Files are read and written in fixed-size chunks (1 MiB by default), so inputs
much larger than available memory can be processed safely.

```python
from compression import compress_file, decompress_file

# Compress data.json -> data.json.gz (returns the path plus byte sizes)
dst, original, compressed = compress_file("data.json")
print(f"{original} -> {compressed} bytes")

# Decompress back to data.json
decompress_file("data.json.gz")
```

When `dst_path` is omitted, `compress_file` appends `.gz` and `decompress_file`
strips a trailing `.gz`. The compression `level` (1–9, default 6) and
`chunk_size` are both configurable.

## Running Tests

The test suite uses only the standard library:

```bash
python -m unittest discover -s tests -v
```

Tests cover persistence, slot-conflict logic, email notifications (with mocked SMTP), search, and the `analyze_image.py` CLI's argument and format validation paths.
