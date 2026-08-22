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

## Number Guessing Game

Guess the secret number with higher/lower feedback. Standard library only.

```bash
python guessing_game.py                          # 1-100 in 7 guesses
python guessing_game.py --difficulty easy        # 1-10 in 5 guesses
python guessing_game.py --difficulty hard        # 1-1000 in 10 guesses
python guessing_game.py --low 1 --high 50 --attempts 0   # custom range, unlimited guesses
python guessing_game.py --seed 7                 # reproducible secret
python guessing_game.py --secret 42              # fixed secret (practice/demo)
```

Type `q` at any prompt to give up. Non-numeric and out-of-range entries are
re-prompted and do not cost a guess.

Exit codes: `0` you won · `1` you lost or quit · `2` bad arguments.

The game logic lives in the `GuessingGame` class, which is I/O-free and can be
driven directly:

```python
from guessing_game import GuessingGame

game = GuessingGame(low=1, high=100, max_attempts=7)
verdict = game.guess(50)      # "too_low", "too_high", or "correct"
print(game.hint(verdict), game.attempts_left)
```

## Running Tests

The test suite uses only the standard library:

```bash
python -m unittest discover -s tests -v
```

Tests cover persistence, slot-conflict logic, email notifications (with mocked SMTP), search, the `analyze_image.py` CLI's argument and format validation paths, and the guessing game's scoring, hint, input-validation, and CLI exit-code paths.
