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
