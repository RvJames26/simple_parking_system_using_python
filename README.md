# Parking System

A small desktop parking lot app built with Python and Tkinter. It displays 90 parking slots, records a plate number at check-in, and calculates the fee at check-out.

Check-in accepts common Philippine private motor vehicle formats (three letters then two to four digits) and motorcycle formats (three digits then two or three letters, or two letters then five digits). A space or hyphen between groups is optional; input is stored in uppercase. This checks the plate shape only; it does not confirm LTO issuance or cover every special, diplomatic, or temporary series.

## Requirements

- Python 3 with Tkinter available

## Run

```powershell
python parking_system.py
```

## Parking fee

The fee is P50 for up to two hours, then P20 per additional hour, prorated by time. The bill displays the duration and amount to two decimal places.

## Notes

- Active parking sessions are saved in `data/active_slots.json` and persist across application restarts.
- Completed check-outs are archived in daily files (`data/records/YYYY-MM-DD.json`) with running vehicle counts and total revenue.
- Use the **Daily Summary** button in the header to view today's revenue and completed transactions.
- “Pay & Exit” clears a slot; the app does not process real payments.
