# PLANORA – Event Booking System

A full-stack event booking web application built with **Python, Flask and MySQL/SQLite**. Users can browse events, book tickets and download PDF tickets with QR codes. Admins manage events from a dashboard.

Built for the *Web Development and Databases* module (BSc Computer Science, UWE Bristol). **Mark: 88%.**

## Features

- **Accounts:** user registration and login with hashed passwords (Werkzeug PBKDF2-SHA256), and separate user and admin access
- **Events:** search and filter by name, category, price and month, with featured events, multi-day events and archiving
- **Booking engine:**
  - Early-booking discounts (5–20% depending on how far ahead you book)
  - A 10% student discount
  - Cancellation charges based on how close the event is
- **Waiting list:** when an event is full, users join a queue. A cancellation automatically offers the freed place to the next person.
- **PDF tickets:** generated with ReportLab, each with a unique QR code
- **Admin dashboard:** live counts of events, bookings, waiting list and revenue, plus event creation, archiving and restoring
- **JSON API:** `/api/events`

## Tech stack

| Layer | Technology |
| --- | --- |
| Backend | Python 3, Flask |
| Database | MySQL (default) or SQLite: 7 relational tables (users, categories, venues, events, event_days, bookings, waitlist) |
| PDF / QR | ReportLab, qrcode, Pillow |
| Frontend | Jinja2 templates, HTML, CSS |

## Run it locally

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Quickest option: SQLite (no database server needed)
DB_MODE=sqlite python app.py    # Windows (PowerShell): $env:DB_MODE="sqlite"; python app.py
```

Then open http://127.0.0.1:5000. The SQLite database is created and filled with demo data on first run.

To use MySQL instead, import `database/schema_mysql.sql` and set `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD` and `MYSQL_DATABASE` as environment variables.

## Project structure

```
app.py               Flask routes, booking logic, PDF/QR generation
database/            MySQL and SQLite schemas
templates/           Jinja2 pages (events, booking, my bookings, admin dashboard)
static/              CSS and event images
```

## Author

**Md Sojib Hosain**, BSc (Hons) Computer Science, UWE Bristol
[LinkedIn](https://www.linkedin.com/in/sojib-hosain) · [GitHub](https://github.com/Sojib-Hosain)
