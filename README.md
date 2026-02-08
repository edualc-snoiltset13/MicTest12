# Barber Booking Agent

A simple Python CLI agent that manages barber appointment bookings with notifications for both the barber and the client.

## Features

- **Register barbers** with their available time slots
- **Book appointments** by selecting a barber, date, and open slot
- **Token numbers** assigned to each booking for easy reference and lookup
- **Look up bookings** by token number
- **View all bookings** (upcoming and past) with token numbers
- **Cancel bookings** with confirmation
- **Notifications** printed to both the barber and the client on booking/cancellation (includes token numbers)

## Requirements

- Python 3.7+
- No external dependencies (uses only the standard library)

## Usage

```bash
python barber_booking_agent.py
```

Follow the interactive menu to register barbers, book appointments, and manage the calendar.

## Data Storage

All bookings are persisted in a local `bookings.json` file so they survive between sessions.
