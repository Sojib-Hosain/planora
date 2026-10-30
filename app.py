# Student Name: MD. SOJIB HOSAIN
# Student ID: 25044586

from __future__ import annotations

import os
import sqlite3
import uuid
from datetime import date, datetime
from functools import wraps
from pathlib import Path
from io import BytesIO

import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
import qrcode

from flask import (
    Flask,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
    make_response,
)
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
SQLITE_DB_PATH = BASE_DIR / "database" / "planora.db"
SQLITE_SCHEMA_PATH = BASE_DIR / "database" / "schema_sqlite.sql"
MYSQL_SCHEMA_PATH = BASE_DIR / "database" / "schema_mysql.sql"

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "planora-dev-secret-key")
app.config["DB_MODE"] = os.getenv("DB_MODE", "mysql")
app.config["MYSQL_HOST"] = os.getenv("MYSQL_HOST", "127.0.0.1")
app.config["MYSQL_PORT"] = int(os.getenv("MYSQL_PORT", "3306"))
app.config["MYSQL_USER"] = os.getenv("MYSQL_USER", "root")
app.config["MYSQL_PASSWORD"] = os.getenv("MYSQL_PASSWORD", "1234")
app.config["MYSQL_DATABASE"] = os.getenv("MYSQL_DATABASE", "planora")


SEED_CATEGORIES = [
    "Exhibition",
    "Workshop",
    "Sports",
    "Musical",
    "Religious",
    "Theatre",
]

SEED_VENUES = [
    ("Ashton Gate Stadium", "Ashton Road, Bristol", 150, "Musical, Sports, Exhibition"),
    ("Arnolfini", "16 Narrow Quay, Bristol", 100, "Exhibition, Workshop"),
    ("The Bristol Hippodrome", "St Augustine's Parade, Bristol", 120, "Theatre, Musical"),
    ("Bristol Old Vic", "King Street, Bristol", 110, "Theatre"),
    ("Bristol Central Library", "College Green, Bristol", 50, "Exhibition"),
    ("Royal West of England Academy", "Queens Road, Bristol", 100, "Exhibition"),
    ("Creative Space A", "Harbourside, Bristol", 30, "Workshop"),
    ("Creative Space B", "Harbourside, Bristol", 50, "Workshop, Course"),
    ("UWE Exhibition Centre", "Frenchay Campus, Bristol", 300, "Wedding, Workshop, Conference, Exhibition"),
    ("Community Centre A", "Easton, Bristol", 60, "Religious, Private Event"),
]

SEED_EVENTS = [
    {
        "name": "Bristol Spring Art Fair",
        "category": "Exhibition",
        "venue": "Arnolfini",
        "start_date": "2026-04-18",
        "end_date": "2026-04-20",
        "base_price": 0.0,
        "total_tickets": 100,
        "tickets_left": 46,
        "last_booking_date": "2026-04-15",
        "description": "A free contemporary arts exhibition with prior booking required.",
        "condition_notes": "Bring your booking confirmation and arrive 10 minutes early.",
        "is_featured": 1,
        "days": ["2026-04-18", "2026-04-19", "2026-04-20"],
    },
    {
        "name": "Harbourside UX Workshop",
        "category": "Workshop",
        "venue": "Creative Space A",
        "start_date": "2026-05-08",
        "end_date": "2026-05-08",
        "base_price": 18.0,
        "total_tickets": 30,
        "tickets_left": 12,
        "last_booking_date": "2026-05-05",
        "description": "Hands-on design workshop for digital creatives.",
        "condition_notes": "Please bring a laptop.",
        "is_featured": 1,
        "days": ["2026-05-08"],
    },
    {
        "name": "Bristol Legends Live",
        "category": "Musical",
        "venue": "The Bristol Hippodrome",
        "start_date": "2026-05-14",
        "end_date": "2026-05-14",
        "base_price": 42.0,
        "total_tickets": 120,
        "tickets_left": 64,
        "last_booking_date": "2026-05-12",
        "description": "An elegant evening musical performance in the city.",
        "condition_notes": "Smart casual dress suggested.",
        "is_featured": 1,
        "days": ["2026-05-14"],
    },
    {
        "name": "City Derby Fan Day",
        "category": "Sports",
        "venue": "Ashton Gate Stadium",
        "start_date": "2026-06-02",
        "end_date": "2026-06-02",
        "base_price": 50.0,
        "total_tickets": 150,
        "tickets_left": 18,
        "last_booking_date": "2026-05-28",
        "description": "Sports event with fan activities and live entertainment.",
        "condition_notes": "E-ticket required at gate.",
        "is_featured": 0,
        "days": ["2026-06-02"],
    },
    {
        "name": "Faith & Culture Gathering",
        "category": "Religious",
        "venue": "Community Centre A",
        "start_date": "2026-06-12",
        "end_date": "2026-06-12",
        "base_price": 10.0,
        "total_tickets": 60,
        "tickets_left": 25,
        "last_booking_date": "2026-06-10",
        "description": "Community celebration blending music, talks and food.",
        "condition_notes": "Respectful dress required.",
        "is_featured": 0,
        "days": ["2026-06-12"],
    },
    {
        "name": "Shakespeare Under Lights",
        "category": "Theatre",
        "venue": "Bristol Old Vic",
        "start_date": "2026-04-28",
        "end_date": "2026-04-28",
        "base_price": 35.0,
        "total_tickets": 110,
        "tickets_left": 52,
        "last_booking_date": "2026-04-24",
        "description": "A modern theatre retelling in a classic Bristol venue.",
        "condition_notes": "Doors open 30 minutes before show.",
        "is_featured": 0,
        "days": ["2026-04-28"],
    },
]


def get_db():
    if "db" in g:
        return g.db

    mode = app.config["DB_MODE"]
    if mode == "mysql":
        import mysql.connector

        conn = mysql.connector.connect(
            host=app.config["MYSQL_HOST"],
            port=app.config["MYSQL_PORT"],
            user=app.config["MYSQL_USER"],
            password=app.config["MYSQL_PASSWORD"],
            database=app.config["MYSQL_DATABASE"],
        )
        g.db = conn
    else:
        SQLITE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        g.db = conn
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def fetch_all(query: str, params: tuple = ()):
    db = get_db()
    if app.config["DB_MODE"] == "mysql":
        cursor = db.cursor(dictionary=True)
        cursor.execute(query.replace("?", "%s"), params)
        rows = cursor.fetchall()
        cursor.close()
        return rows
    cursor = db.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    return rows


def fetch_one(query: str, params: tuple = ()):
    db = get_db()
    if app.config["DB_MODE"] == "mysql":
        cursor = db.cursor(dictionary=True)
        cursor.execute(query.replace("?", "%s"), params)
        row = cursor.fetchone()
        cursor.close()
        return row
    cursor = db.execute(query, params)
    row = cursor.fetchone()
    cursor.close()
    return row


def execute_db(query: str, params: tuple = ()):
    db = get_db()
    if app.config["DB_MODE"] == "mysql":
        cursor = db.cursor()
        cursor.execute(query.replace("?", "%s"), params)
        db.commit()
        last_id = cursor.lastrowid
        cursor.close()
        return last_id
    cursor = db.execute(query, params)
    db.commit()
    last_id = cursor.lastrowid
    cursor.close()
    return last_id


def execute_script(sql_text: str):
    db = get_db()
    if app.config["DB_MODE"] == "mysql":
        cursor = db.cursor()
        for statement in [s.strip() for s in sql_text.split(";") if s.strip()]:
            cursor.execute(statement)
        db.commit()
        cursor.close()
    else:
        db.executescript(sql_text)
        db.commit()


def row_to_dict(row):
    if row is None:
        return None
    if isinstance(row, sqlite3.Row):
        return dict(row)
    return row


def rows_to_dicts(rows):
    return [row_to_dict(row) for row in rows]


def calculate_advance_discount(days_in_advance: int) -> float:
    if 50 <= days_in_advance <= 60:
        return 0.20
    if 35 <= days_in_advance < 50:
        return 0.15
    if 25 <= days_in_advance < 35:
        return 0.10
    if 15 <= days_in_advance < 25:
        return 0.05
    return 0.0


def calculate_cancellation_charge(event_start_date: str, booking_total: float) -> float:
    event_day = event_start_date
    days_to_event = (event_day - date.today()).days
    if days_to_event >= 40:
        return 0.0
    if 25 <= days_to_event < 40:
        return round(float(booking_total) * 0.40, 2)
    return round(float(booking_total), 2)


def calculate_receipt(event: dict, quantity: int, booking_date_str: str, is_student: bool):
    booking_day = datetime.strptime(booking_date_str, "%Y-%m-%d").date()
    event_day = event["start_date"]
    days_in_advance = max(0, (event_day - booking_day).days)
    subtotal = round(float(event["base_price"]) * quantity, 2)
    advance_rate = calculate_advance_discount(days_in_advance)
    advance_discount = round(subtotal * advance_rate, 2)
    discounted_subtotal = subtotal - advance_discount
    student_discount = round(discounted_subtotal * 0.10, 2) if is_student else 0.0
    total = round(max(0, discounted_subtotal - student_discount), 2)
    return {
        "days_in_advance": days_in_advance,
        "subtotal": subtotal,
        "advance_rate": advance_rate,
        "advance_discount": advance_discount,
        "student_discount": student_discount,
        "total": total,
    }


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please login first.", "warning")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = get_current_user()
        if not user or user.get("role") != "admin":
            flash("Admin access only.", "danger")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    user = fetch_one("SELECT id, full_name, email, role FROM users WHERE id = ?", (user_id,))
    return row_to_dict(user)


def get_category_id(name: str) -> int:
    row = fetch_one("SELECT id FROM categories WHERE name = ?", (name,))
    return row["id"] if not isinstance(row, sqlite3.Row) else row["id"]


def get_venue_id(name: str) -> int:
    row = fetch_one("SELECT id FROM venues WHERE name = ?", (name,))
    return row["id"] if not isinstance(row, sqlite3.Row) else row["id"]


def get_event(event_id: int):
    row = fetch_one(
        """
        SELECT e.*, c.name AS category_name, v.name AS venue_name, v.address, v.capacity, v.suitable_types
        FROM events e
        JOIN categories c ON c.id = e.category_id
        JOIN venues v ON v.id = e.venue_id
        WHERE e.id = ?
        """,
        (event_id,),
    )
    return row_to_dict(row)


def get_events(filters=None, featured_only=False, status="active"):
    filters = filters or {}
    query = """
        SELECT e.*, c.name AS category_name, v.name AS venue_name, v.address, v.capacity, v.suitable_types
        FROM events e
        JOIN categories c ON c.id = e.category_id
        JOIN venues v ON v.id = e.venue_id
        WHERE e.status = ?
    """
    params = [status]

    if featured_only:
        query += " AND e.is_featured = 1"

    if filters.get("q"):
        query += " AND LOWER(e.name) LIKE ?"
        params.append(f"%{filters['q'].lower()}%")
    if filters.get("category") and filters["category"] != "all":
        query += " AND c.name = ?"
        params.append(filters["category"])
    if filters.get("price") == "free":
        query += " AND e.base_price = 0"
    elif filters.get("price") == "paid":
        query += " AND e.base_price > 0"
    if filters.get("month") and filters["month"] != "all":
        query += " AND substr(e.start_date, 1, 7) = ?"
        params.append(filters["month"])

    query += " ORDER BY e.start_date ASC"
    return rows_to_dicts(fetch_all(query, tuple(params)))


def get_categories():
    return rows_to_dicts(fetch_all("SELECT * FROM categories ORDER BY name ASC"))


def get_venues():
    return rows_to_dicts(fetch_all("SELECT * FROM venues ORDER BY name ASC"))


def get_user_bookings(user_id: int):
    rows = fetch_all(
        """
        SELECT b.*, e.name AS event_name, e.start_date, e.base_price, c.name AS category_name
        FROM bookings b
        JOIN events e ON e.id = b.event_id
        JOIN categories c ON c.id = e.category_id
        WHERE b.user_id = ?
        ORDER BY b.booking_date DESC, b.id DESC
        """,
        (user_id,),
    )
    return rows_to_dicts(rows)


def get_waitlist_count(event_id: int) -> int:
    row = fetch_one(
        "SELECT COUNT(*) AS total FROM waitlist WHERE event_id = ? AND status = 'waiting'",
        (event_id,),
    )
    row = row_to_dict(row)
    return int(row["total"] or 0)


def promote_waitlist(event_id: int):
    event = get_event(event_id)
    if not event or event["tickets_left"] <= 0:
        return
    candidate = fetch_one(
        """
        SELECT id, user_id, quantity
        FROM waitlist
        WHERE event_id = ? AND status = 'waiting'
        ORDER BY created_at ASC, id ASC
        LIMIT 1
        """,
        (event_id,),
    )
    candidate = row_to_dict(candidate)
    if not candidate:
        return
    if candidate["quantity"] > event["tickets_left"]:
        return
    execute_db("UPDATE waitlist SET status = 'offered' WHERE id = ?", (candidate["id"],))
    execute_db(
        "UPDATE events SET tickets_left = tickets_left - ? WHERE id = ?",
        (candidate["quantity"], event_id),
    )


def init_database():
    if app.config["DB_MODE"] == "mysql":
        return
    db_exists = SQLITE_DB_PATH.exists()
    with app.app_context():
        if not db_exists:
            execute_script(SQLITE_SCHEMA_PATH.read_text(encoding="utf-8"))
        row = fetch_one("SELECT COUNT(*) AS total FROM users")
        total_users = row_to_dict(row)["total"]
        if total_users == 0:
            seed_database()


def seed_database():
    for category in SEED_CATEGORIES:
        execute_db("INSERT INTO categories(name) VALUES (?)", (category,))

    for venue in SEED_VENUES:
        execute_db(
            "INSERT INTO venues(name, address, capacity, suitable_types) VALUES (?, ?, ?, ?)",
            venue,
        )

    execute_db(
        "INSERT INTO users(full_name, email, password_hash, role) VALUES (?, ?, ?, ?)",
        (
            "PLANORA Admin",
            "admin@planora.local",
            generate_password_hash(os.getenv("ADMIN_PASSWORD", "admin123"), method="pbkdf2:sha256"),
            "admin",
        ),
    )

    for item in SEED_EVENTS:
        event_id = execute_db(
            """
            INSERT INTO events(
                name, category_id, venue_id, start_date, end_date, base_price,
                total_tickets, tickets_left, last_booking_date, description,
                condition_notes, is_featured, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
            """,
            (
                item["name"],
                get_category_id(item["category"]),
                get_venue_id(item["venue"]),
                item["start_date"],
                item["end_date"],
                item["base_price"],
                item["total_tickets"],
                item["tickets_left"],
                item["last_booking_date"],
                item["description"],
                item["condition_notes"],
                item["is_featured"],
            ),
        )
        total_days = len(item["days"])
        day_price = 0.0 if item["base_price"] == 0 else round(item["base_price"] / total_days, 2)
        for event_day in item["days"]:
            execute_db(
                "INSERT INTO event_days(event_id, event_date, day_price) VALUES (?, ?, ?)",
                (event_id, event_day, day_price),
            )


@app.context_processor
def inject_globals():
    return {
        "current_user": get_current_user(),
        "current_year": date.today().year,
    }


@app.template_filter("money")
def money_filter(value):
    value = float(value or 0)
    return "Free" if value == 0 else f"£{value:,.2f}"


@app.route("/")
def home():
    featured_events = get_events(featured_only=True)[:3]
    total_events = row_to_dict(fetch_one("SELECT COUNT(*) AS total FROM events WHERE status = 'active'"))["total"]
    return render_template("index.html", featured_events=featured_events, total_events=total_events)


@app.route("/events")
def events():
    filters = {
        "q": request.args.get("q", "").strip(),
        "category": request.args.get("category", "all"),
        "price": request.args.get("price", "all"),
        "month": request.args.get("month", "all"),
    }
    event_rows = get_events(filters)
    return render_template(
        "events.html",
        events=event_rows,
        categories=get_categories(),
        filters=filters,
    )


@app.route("/event/<int:event_id>")
def event_detail(event_id):
    event = get_event(event_id)
    if not event:
        flash("Event not found.", "danger")
        return redirect(url_for("events"))
    event_days = rows_to_dicts(fetch_all("SELECT * FROM event_days WHERE event_id = ? ORDER BY event_date", (event_id,)))
    return render_template(
        "event.html",
        event=event,
        event_days=event_days,
        waitlist_count=get_waitlist_count(event_id),
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not full_name or not email or not password:
            flash("Please complete all fields.", "danger")
        elif password != confirm_password:
            flash("Passwords do not match.", "danger")
        elif fetch_one("SELECT id FROM users WHERE email = ?", (email,)):
            flash("That email address is already registered.", "warning")
        else:
            execute_db(
                "INSERT INTO users(full_name, email, password_hash, role) VALUES (?, ?, ?, 'standard')",
                (full_name, email, generate_password_hash(password, method="pbkdf2:sha256")),
            )
            flash("Registration successful. Please login.", "success")
            return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        row = fetch_one("SELECT id, full_name, email, password_hash, role FROM users WHERE email = ?", (email,))
        user = row_to_dict(row)
        if not user or not check_password_hash(user["password_hash"], password):
            flash("Invalid email or password.", "danger")
        else:
            session["user_id"] = user["id"]
            flash(f"Welcome back, {user['full_name']}.", "success")
            next_url = request.args.get("next")
            return redirect(next_url or (url_for("admin_dashboard") if user["role"] == "admin" else url_for("home")))
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))


@app.route("/booking", methods=["GET", "POST"])
@login_required
def booking():
    selected_id = request.args.get("event_id", type=int) or request.form.get("event_id", type=int)
    selected_event = get_event(selected_id) if selected_id else None
    receipt = None
    waitlist_message = None
    booking_id = None

    if request.method == "POST":
        card_number = request.form.get("card_number")
        expiry = request.form.get("expiry")
        cvv = request.form.get("cvv")
        if not card_number or not expiry or not cvv:
            flash("Payment details required.", "danger")    
            return redirect(url_for("booking"))

        event = get_event(request.form.get("event_id", type=int))
        quantity = max(1, request.form.get("quantity", type=int))
        booking_date = request.form.get("booking_date") or date.today().isoformat()
        is_student = request.form.get("is_student") == "on"

        if not event:
            flash("Please select a valid event.", "danger")
            return redirect(url_for("booking"))
        else:
            receipt = calculate_receipt(event, quantity, booking_date, is_student)
            selected_event = event
            if quantity > event["tickets_left"]:
                already_waiting = fetch_one(
                    "SELECT id FROM waitlist WHERE user_id = ? AND event_id = ? AND status = 'waiting'",
                    (session["user_id"], event["id"]),
                )
                if already_waiting:
                    waitlist_message = "You are already on the waiting list for this event."
                else:
                    execute_db(
                        "INSERT INTO waitlist(user_id, event_id, quantity, created_at, status) VALUES (?, ?, ?, ?, 'waiting')",
                        (session["user_id"], event["id"], quantity, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                    )
                    waitlist_message = "This event is currently full, so you were added to the waiting list."
            else:
                receipt_code = f"PLN-{uuid.uuid4().hex[:8].upper()}"
                conn = get_db()
                cursor = conn.cursor()

                cursor.execute("""
                INSERT INTO bookings (
                user_id, event_id, quantity, booking_date,
                    days_in_advance, subtotal, advance_discount_amount, student_discount_amount,
                    total_price,
                    receipt_code, status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'confirmed')
                """, (
                    session["user_id"],
                    event["id"],
                    quantity,
                    booking_date,
                    receipt["days_in_advance"],
                    receipt["subtotal"],
                    receipt["advance_discount"],
                    receipt["student_discount"],
                    receipt["total"],
                    receipt_code
                ))

                conn.commit()
                booking_id = cursor.lastrowid

                execute_db(
                    "UPDATE events SET tickets_left = tickets_left - ? WHERE id = ?",
                    (quantity, event["id"]),
                )
                flash("Payment successful! Booking confirmed.", "success")

    return render_template(
        "booking.html",
        events=get_events(),
        selected_event=selected_event,
        receipt=receipt,
        waitlist_message=waitlist_message,
        booking_id=booking_id,
        today=date.today().isoformat(),
    )


@app.route("/my-bookings")
@login_required
def my_bookings():
    return render_template("my_bookings.html", bookings=get_user_bookings(session["user_id"]))


@app.route("/download-receipt/<int:booking_id>")
def download_receipt(booking_id):
    if "user_id" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            b.id,
            b.user_id,
            b.receipt_code,
            b.booking_date,
            b.quantity,
            b.subtotal,
            b.advance_discount_rate,
            b.advance_discount_amount,
            b.student_discount_amount,
            b.total_price,
            b.status,
            e.name AS event_name,
            e.start_date,
            e.end_date,
            v.name AS venue_name
            FROM bookings b
            JOIN events e ON b.event_id = e.id
            JOIN venues v ON e.venue_id = v.id
        WHERE b.id = %s
    """, (booking_id,))

    booking = cursor.fetchone()

    if not booking:
        flash("Receipt not found.", "error")
        return redirect(url_for("my_bookings"))

    if booking["user_id"] != session["user_id"] and session.get("role") != "admin":
        flash("You are not allowed to download this receipt.", "error")
        return redirect(url_for("my_bookings"))

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    page_width, page_height = letter

    # Background
    p.setFillColor(colors.HexColor("#0B1020"))
    p.rect(0, 0, page_width, page_height, fill=1, stroke=0)

    # Main ticket card
    card_x = 40
    card_y = 120
    card_w = page_width - 80
    card_h = 580

    p.setFillColor(colors.HexColor("#121A33"))
    p.roundRect(card_x, card_y, card_w, card_h, 22, fill=1, stroke=0)

    # Top gradient-style bands
    p.setFillColor(colors.HexColor("#7C5CFF"))
    p.roundRect(card_x, card_y + card_h - 90, card_w, 90, 22, fill=1, stroke=0)

    p.setFillColor(colors.HexColor("#31CFFF"))
    p.rect(card_x + card_w * 0.52, card_y + card_h - 90, card_w * 0.48, 90, fill=1, stroke=0)

    # Title
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 24)
    p.drawString(card_x + 24, card_y + card_h - 42, "PLANORA")

    p.setFont("Helvetica", 11)
    p.drawString(card_x + 24, card_y + card_h - 62, "Event Ticket & Booking Receipt")

    # Confirmed badge
    badge_w = 92
    badge_h = 26
    badge_x = card_x + card_w - badge_w - 24
    badge_y = card_y + card_h - 56
    p.setFillColor(colors.HexColor("#0F172A"))
    p.roundRect(badge_x, badge_y, badge_w, badge_h, 13, fill=1, stroke=0)
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 10)
    p.drawCentredString(badge_x + badge_w / 2, badge_y + 8, "CONFIRMED")

    # Event title section
    text_x = card_x + 24
    content_top = card_y + card_h - 125

    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 20)
    p.drawString(text_x, content_top, booking["event_name"])

    p.setFont("Helvetica", 11)
    p.setFillColor(colors.HexColor("#C7D2FE"))
    p.drawString(text_x, content_top - 18, f"Receipt Code: {booking['receipt_code']}")
    p.drawString(text_x, content_top - 34, f"Booking ID: {booking['id']}")

    # Meta info boxes
    box_y = content_top - 82
    box_w = 155
    box_h = 58
    gap = 12

    meta_boxes = [
        ("Venue", booking["venue_name"]),
        ("Date", f"{booking['start_date']}"),
        ("Tickets", str(booking["quantity"])),
    ]

    for i, (label, value) in enumerate(meta_boxes):
        bx = text_x + i * (box_w + gap)
        p.setFillColor(colors.HexColor("#1B2545"))
        p.roundRect(bx, box_y, box_w, box_h, 14, fill=1, stroke=0)
        p.setFillColor(colors.HexColor("#94A3B8"))
        p.setFont("Helvetica", 9)
        p.drawString(bx + 12, box_y + 39, label)
        p.setFillColor(colors.white)
        p.setFont("Helvetica-Bold", 10)
        safe_value = str(value)
        if len(safe_value) > 24:
            safe_value = safe_value[:21] + "..."
        p.drawString(bx + 12, box_y + 20, safe_value)

    # Divider
    div_y = box_y - 22
    p.setStrokeColor(colors.HexColor("#334155"))
    p.setDash(5, 4)
    p.line(card_x + 24, div_y, card_x + card_w - 24, div_y)
    p.setDash()

    # Price section
    left_x = text_x
    right_x = card_x + card_w - 185
    price_y = div_y - 30

    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 13)
    p.drawString(left_x, price_y, "Payment Summary")

    p.setFont("Helvetica", 11)

    lines = [
        ("Base Subtotal", f"GBP {booking['subtotal']:.2f}"),
        (
            f"Advance Discount ({booking['advance_discount_rate'] * 100:.0f}%)",
            f"-GBP {booking['advance_discount_amount']:.2f}",
        ),
        ("Student Discount", f"-GBP {booking['student_discount_amount']:.2f}"),
        ("Status", str(booking["status"]).title()),
    ]

    y = price_y - 24
    for label, value in lines:
        p.setFillColor(colors.HexColor("#CBD5E1"))
        p.drawString(left_x, y, label)
        p.setFillColor(colors.white)
        p.drawRightString(right_x, y, value)
        y -= 24

    # Add more space after the payment lines
    y -= 38

    # Total box
    total_box_y = y - 8
    total_box_h = 56
    total_box_w = right_x - left_x

    # background
    p.setFillColor(colors.HexColor("#0F172A"))
    p.roundRect(left_x, total_box_y, total_box_w, total_box_h, 16, fill=1, stroke=0)

    # subtle border
    p.setStrokeColor(colors.HexColor("#334155"))
    p.setLineWidth(1)
    p.roundRect(left_x, total_box_y, total_box_w, total_box_h, 16, fill=0, stroke=1)

    # label
    p.setFillColor(colors.HexColor("#93C5FD"))
    p.setFont("Helvetica-Bold", 11)
    p.drawString(left_x + 16, total_box_y + 34, "TOTAL PAID")

    # amount
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 18)
    p.drawRightString(
    left_x + total_box_w - 16,
    total_box_y + 32,
    f"GBP {booking['total_price']:.2f}"
    )

    # helper text
    p.setFillColor(colors.HexColor("#94A3B8"))
    p.setFont("Helvetica", 8)
    p.drawString(left_x + 16, total_box_y + 14, "Includes all discounts")

    # QR code content
    qr_data = (
        f"PLANORA | Receipt: {booking['receipt_code']} | "
        f"Booking ID: {booking['id']} | Event: {booking['event_name']}"
    )

    qr = qrcode.QRCode(box_size=6, border=1)
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    qr_buffer = BytesIO()
    qr_img.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)

    qr_reader = ImageReader(qr_buffer)

    qr_size = 110
    qr_x = card_x + card_w - qr_size - 24
    qr_y = card_y + 34

    p.drawImage(qr_reader, qr_x, qr_y, width=qr_size, height=qr_size, mask="auto")

    p.setFillColor(colors.HexColor("#CBD5E1"))
    p.setFont("Helvetica", 9)
    p.drawCentredString(qr_x + qr_size / 2, qr_y - 12, "Scan / Verify Ticket")

    # Footer notes
    note_x = card_x + 24
    note_y = card_y + 76

    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 11)
    p.drawString(note_x, note_y, "Entry Instructions")

    p.setFillColor(colors.HexColor("#CBD5E1"))
    p.setFont("Helvetica", 10)
    p.drawString(note_x, note_y - 18, "Bring this ticket or show the PDF at the venue entrance.")
    p.drawString(note_x, note_y - 34, "Students should carry a valid student ID for discount verification.")

    # Decorative footer
    p.setFillColor(colors.HexColor("#7C5CFF"))
    p.roundRect(card_x, card_y, card_w, 14, 7, fill=1, stroke=0)

    p.showPage()
    p.save()

    buffer.seek(0)

    response = make_response(buffer.getvalue())
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f'attachment; filename=receipt_{booking["receipt_code"]}.pdf'
    return response

@app.post("/booking/<int:booking_id>/cancel")
@login_required
def cancel_booking(booking_id):
    booking = fetch_one(
        """
        SELECT b.*, e.start_date, e.id AS event_id
        FROM bookings b
        JOIN events e ON e.id = b.event_id
        WHERE b.id = ? AND b.user_id = ?
        """,
        (booking_id, session["user_id"]),
    )
    booking = row_to_dict(booking)
    if not booking or booking["status"] != "confirmed":
        flash("Booking could not be cancelled.", "danger")
        return redirect(url_for("my_bookings"))

    cancellation_charge = calculate_cancellation_charge(booking["start_date"], booking["total_price"])
    execute_db(
        "UPDATE bookings SET status = 'cancelled', cancellation_charge = ? WHERE id = ?",
        (cancellation_charge, booking_id),
    )
    execute_db(
        "UPDATE events SET tickets_left = tickets_left + ? WHERE id = ?",
        (booking["quantity"], booking["event_id"]),
    )
    promote_waitlist(booking["event_id"])
    if cancellation_charge:
        flash(f"Booking cancelled. Cancellation charge applied: £{cancellation_charge:.2f}", "warning")
    else:
        flash("Booking cancelled with no cancellation charge.", "success")
    return redirect(url_for("my_bookings"))


@app.route("/admin")
@admin_required
def admin_dashboard():
    stats = {
        "events": row_to_dict(fetch_one("SELECT COUNT(*) AS total FROM events WHERE status = 'active'"))["total"],
        "bookings": row_to_dict(fetch_one("SELECT COUNT(*) AS total FROM bookings WHERE status = 'confirmed'"))["total"],
        "waiting": row_to_dict(fetch_one("SELECT COUNT(*) AS total FROM waitlist WHERE status = 'waiting'"))["total"],
        "revenue": row_to_dict(fetch_one("SELECT COALESCE(SUM(total_price), 0) AS total FROM bookings WHERE status = 'confirmed'"))["total"],
    }
    recent_bookings = rows_to_dicts(
        fetch_all(
            """
            SELECT b.id, b.receipt_code, b.total_price, b.status, u.full_name, e.name AS event_name
            FROM bookings b
            JOIN users u ON u.id = b.user_id
            JOIN events e ON e.id = b.event_id
            ORDER BY b.id DESC
            LIMIT 8
            """
        )
    )
    archived_events = get_events(status="archived")
    return render_template(
        "admin_dashboard.html",
        stats=stats,
        events=get_events(),
        archived_events=archived_events,
        categories=get_categories(),
        venues=get_venues(),
        recent_bookings=recent_bookings,
    )


@app.post("/admin/events/new")
@admin_required
def admin_add_event():
    name = request.form.get("name", "").strip()
    category_id = request.form.get("category_id", type=int)
    venue_id = request.form.get("venue_id", type=int)
    start_date = request.form.get("start_date")
    end_date = request.form.get("end_date") or start_date
    base_price = request.form.get("base_price", type=float) or 0.0
    total_tickets = request.form.get("total_tickets", type=int) or 0
    description = request.form.get("description", "").strip()
    image_url = request.form.get("image_url", "").strip()
    condition_notes = request.form.get("condition_notes", "").strip()
    is_featured = 1 if request.form.get("is_featured") == "on" else 0

    if not all([name, category_id, venue_id, start_date, total_tickets]):
        flash("Please complete the required admin event fields.", "danger")
        return redirect(url_for("admin_dashboard"))

    event_id = execute_db(
        """
        INSERT INTO events(
            name, category_id, venue_id, start_date, end_date, base_price,
            total_tickets, tickets_left, last_booking_date, description,
            condition_notes, is_featured, image_url, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
        """,
        (
            name,
            category_id,
            venue_id,
            start_date,
            end_date,
            base_price,
            total_tickets,
            total_tickets,
            start_date,
            description,
            condition_notes,
            is_featured,
            image_url,
        ),
    )
    execute_db(
        "INSERT INTO event_days(event_id, event_date, day_price) VALUES (?, ?, ?)",
        (event_id, start_date, base_price),
    )
    flash("New event added successfully.", "success")
    return redirect(url_for("admin_dashboard"))


@app.post("/admin/events/<int:event_id>/delete")
@admin_required
def admin_delete_event(event_id):
    execute_db("UPDATE events SET status = 'archived' WHERE id = ?", (event_id,))
    flash("Event archived.", "info")
    return redirect(url_for("admin_dashboard"))


@app.post("/admin/events/<int:event_id>/restore")
@admin_required
def admin_restore_event(event_id):
    execute_db("UPDATE events SET status = 'active' WHERE id = ?", (event_id,))
    flash("Event restored successfully.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/api/events")
def api_events():
    return {"events": get_events()}


# Automatically prepare the MySQL demo database when the app starts.
# if app.config["DB_MODE"] == "mysql":
#     with app.app_context():
#         execute_script(MYSQL_SCHEMA_PATH.read_text(encoding="utf-8"))
#         seed_database()

if __name__ == "__main__":
    init_database()  # creates and seeds the SQLite database on first run
    app.run(debug=True)
