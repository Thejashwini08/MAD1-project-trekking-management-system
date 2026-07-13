from flask import Flask, render_template, request, redirect, url_for, session
from models import db, User, Trek, Booking, init_db
from datetime import date

app = Flask(__name__)
app.secret_key = "simplekey123"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///trekking.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
init_db(app)


# ---------------- HOME / LOGIN / LOGOUT ----------------

@app.route("/")
def home():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email, password=password).first()

        if user is None:
            return render_template("login.html", error="Invalid email or password")

        if user.role in ("staff", "user") and user.status != "Approved":
            return render_template("login.html", error="Your account is not approved yet")

        session["user_id"] = user.id
        session["name"] = user.name
        session["role"] = user.role

        if user.role == "admin":
            return redirect(url_for("admin_dashboard"))
        elif user.role == "staff":
            return redirect(url_for("staff_dashboard"))
        else:
            return redirect(url_for("user_dashboard"))

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        role = request.form["role"]
        contact = request.form.get("contact", "")

        if password != confirm_password:
            return render_template("register.html", error="Passwords do not match")

        existing = User.query.filter_by(email=email).first()
        if existing:
            return render_template("register.html", error="Email already registered")

        status = "Pending" if role == "staff" else "Approved"

        new_user = User(name=name, email=email, password=password, contact=contact, role=role, status=status)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------- ADMIN ----------------

@app.route("/admin/dashboard")
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    total_treks = Trek.query.count()
    total_users = User.query.filter_by(role="user").count()
    total_staff = User.query.filter_by(role="staff").count()
    total_bookings = Booking.query.count()

    recent = Booking.query.order_by(Booking.id.desc()).limit(5).all()
    recent_bookings = []
    for b in recent:
        u = User.query.get(b.user_id)
        t = Trek.query.get(b.trek_id)
        recent_bookings.append({
            "id": b.id,
            "user_name": u.name if u else "-",
            "trek_name": t.name if t else "-",
            "booking_date": b.booking_date,
            "status": b.status
        })

    return render_template("admin_dashboard.html", total_treks=total_treks, total_users=total_users,
                           total_staff=total_staff, total_bookings=total_bookings, recent_bookings=recent_bookings, active="dashboard")


@app.route("/admin/treks")
def admin_treks():
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    treks = Trek.query.all()
    return render_template("admin_treks.html", treks=treks, active="treks")


@app.route("/admin/treks/add", methods=["GET", "POST"])
def admin_add_trek():
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    if request.method == "POST":
        trek = Trek(
            name=request.form["name"],
            location=request.form["location"],
            difficulty=request.form["difficulty"],
            duration=request.form["duration"],
            available_slots=request.form["slots"],
            status="Pending",
            start_date=request.form["start_date"],
            end_date=request.form["end_date"],
            description=request.form.get("description", "")
        )
        db.session.add(trek)
        db.session.commit()
        return redirect(url_for("admin_treks"))

    staff_list = User.query.filter_by(role="staff", status="Approved").all()
    return render_template("admin_add_trek.html", staff_list=staff_list)


@app.route("/admin/treks/edit/<int:trek_id>", methods=["GET", "POST"])
def admin_edit_trek(trek_id):
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    trek = Trek.query.get(trek_id)

    if request.method == "POST":
        trek.name = request.form["name"]
        trek.location = request.form["location"]
        trek.difficulty = request.form["difficulty"]
        trek.duration = request.form["duration"]
        trek.available_slots = request.form["slots"]
        trek.status = request.form["status"]
        staff_id = request.form.get("staff_id")
        trek.staff_id = staff_id if staff_id else None
        trek.start_date = request.form["start_date"]
        trek.end_date = request.form["end_date"]
        trek.description = request.form.get("description", "")
        db.session.commit()
        return redirect(url_for("admin_treks"))

    staff_list = User.query.filter_by(role="staff", status="Approved").all()
    return render_template("admin_edit_trek.html", trek=trek, staff_list=staff_list)


@app.route("/admin/treks/delete/<int:trek_id>")
def admin_delete_trek(trek_id):
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    trek = Trek.query.get(trek_id)
    if trek:
        db.session.delete(trek)
        db.session.commit()
    return redirect(url_for("admin_treks"))


@app.route("/admin/staff")
def admin_staff():
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    staff = User.query.filter_by(role="staff").all()
    return render_template("admin_staff.html", staff=staff, active="staff")


@app.route("/admin/staff/approve/<int:staff_id>")
def admin_approve_staff(staff_id):
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    staff = User.query.get(staff_id)
    if staff:
        staff.status = "Approved"
        db.session.commit()
    return redirect(url_for("admin_staff"))


@app.route("/admin/staff/blacklist/<int:staff_id>")
def admin_blacklist_staff(staff_id):
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    staff = User.query.get(staff_id)
    if staff:
        staff.status = "Blacklisted"
        db.session.commit()
    return redirect(url_for("admin_staff"))


@app.route("/admin/staff/unblacklist/<int:staff_id>")
def admin_unblacklist_staff(staff_id):
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    staff = User.query.get(staff_id)
    if staff:
        staff.status = "Approved"
        db.session.commit()
    return redirect(url_for("admin_staff"))


@app.route("/admin/users")
def admin_users():
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    users = User.query.filter_by(role="user").all()
    return render_template("admin_users.html", users=users, active="users")


@app.route("/admin/users/blacklist/<int:user_id>")
def admin_blacklist_user(user_id):
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    user = User.query.get(user_id)
    if user:
        user.status = "Blacklisted"
        db.session.commit()
    return redirect(url_for("admin_users"))


@app.route("/admin/users/unblacklist/<int:user_id>")
def admin_unblacklist_user(user_id):
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    user = User.query.get(user_id)
    if user:
        user.status = "Approved"
        db.session.commit()
    return redirect(url_for("admin_users"))


@app.route("/admin/bookings")
def admin_bookings():
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    all_bookings = Booking.query.order_by(Booking.id.desc()).all()
    bookings = []
    for b in all_bookings:
        u = User.query.get(b.user_id)
        t = Trek.query.get(b.trek_id)
        bookings.append({
            "id": b.id,
            "user_name": u.name if u else "-",
            "trek_name": t.name if t else "-",
            "booking_date": b.booking_date,
            "status": b.status
        })

    return render_template("admin_bookings.html", bookings=bookings, active="bookings")


@app.route("/admin/search", methods=["GET", "POST"])
def admin_search():
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    results = []
    search_type = "treks"
    query = ""

    if request.method == "POST":
        query = request.form["query"]
        search_type = request.form["search_type"]

        if search_type == "treks":
            results = Trek.query.filter(
                (Trek.name.like(f"%{query}%")) | (Trek.location.like(f"%{query}%"))
            ).all()
        elif search_type == "staff":
            id_match = int(query) if query.isdigit() else -1
            results = User.query.filter_by(role="staff").filter(
                (User.name.like(f"%{query}%")) | (User.id == id_match)
            ).all()
        elif search_type == "users":
            id_match = int(query) if query.isdigit() else -1
            results = User.query.filter_by(role="user").filter(
                (User.name.like(f"%{query}%")) | (User.id == id_match)
            ).all()

    return render_template("admin_search.html", results=results, search_type=search_type, query=query, active="search")


# ---------------- STAFF ----------------

@app.route("/staff/dashboard")
def staff_dashboard():
    if session.get("role") != "staff":
        return redirect(url_for("login"))

    staff_id = session["user_id"]
    treks = Trek.query.filter_by(staff_id=staff_id).all()

    total_participants = 0
    for t in treks:
        count = Booking.query.filter_by(trek_id=t.id, status="Booked").count()
        total_participants += count

    open_treks = Trek.query.filter_by(staff_id=staff_id, status="Open").count()

    return render_template("staff_dashboard.html", treks=treks, total_participants=total_participants,
                           open_treks=open_treks)


@app.route("/staff/trek/<int:trek_id>", methods=["GET", "POST"])
def staff_manage_trek(trek_id):
    if session.get("role") != "staff":
        return redirect(url_for("login"))

    trek = Trek.query.filter_by(id=trek_id, staff_id=session["user_id"]).first()

    if trek is None:
        return redirect(url_for("staff_dashboard"))

    if request.method == "POST":
        trek.available_slots = request.form["slots"]
        trek.status = request.form["status"]
        db.session.commit()

        # Trek status drives booking status: when trek is Completed, all active bookings become Completed
        if trek.status == "Completed":
            Booking.query.filter_by(trek_id=trek_id, status="Booked").update({"status": "Completed"})
            db.session.commit()

    participants_raw = Booking.query.filter_by(trek_id=trek_id).all()
    participants = []
    for b in participants_raw:
        u = User.query.get(b.user_id)
        participants.append({
            "id": b.id,
            "name": u.name if u else "-",
            "email": u.email if u else "-",
            "booking_date": b.booking_date,
            "status": b.status
        })

    return render_template("staff_trek.html", trek=trek, participants=participants)


# ---------------- USER (TREKKER) ----------------

@app.route("/user/dashboard")
def user_dashboard():
    if session.get("role") != "user":
        return redirect(url_for("login"))

    treks = Trek.query.filter_by(status="Open").all()

    bookings_raw = Booking.query.filter_by(user_id=session["user_id"]).all()
    bookings = []
    for b in bookings_raw:
        t = Trek.query.get(b.trek_id)
        bookings.append({
            "trek_name": t.name if t else "-",
            "booking_date": b.booking_date,
            "status": b.status
        })

    return render_template("user_dashboard.html", treks=treks, bookings=bookings, active="dashboard")


@app.route("/user/treks", methods=["GET"])
def user_browse_treks():
    if session.get("role") != "user":
        return redirect(url_for("login"))

    difficulty = request.args.get("difficulty", "")
    location = request.args.get("location", "")

    query = Trek.query.filter_by(status="Open")

    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    if location:
        query = query.filter(Trek.location.like(f"%{location}%"))

    treks = query.all()

    return render_template("user_treks.html", treks=treks, difficulty=difficulty, location=location, active="treks")


@app.route("/user/trek/<int:trek_id>", methods=["GET", "POST"])
def user_trek_details(trek_id):
    if session.get("role") != "user":
        return redirect(url_for("login"))

    trek = Trek.query.get(trek_id)

    if request.method == "POST":
        existing_booking = Booking.query.filter(
            Booking.user_id == session["user_id"],
            Booking.trek_id == trek_id,
            Booking.status.in_(["Booked", "Completed"])
        ).first()
        if existing_booking:
            return render_template("user_trek_details.html", trek=trek, error="You have already booked this trek")

        if trek.status == "Open" and trek.available_slots > 0:
            booking = Booking(user_id=session["user_id"], trek_id=trek_id,
                               booking_date=date.today().isoformat(), status="Booked")
            db.session.add(booking)
            trek.available_slots = trek.available_slots - 1
            db.session.commit()
            return redirect(url_for("user_my_bookings"))
        else:
            return render_template("user_trek_details.html", trek=trek, error="Trek is not open or slots are full")

    return render_template("user_trek_details.html", trek=trek)


@app.route("/user/bookings")
def user_my_bookings():
    if session.get("role") != "user":
        return redirect(url_for("login"))

    bookings_raw = Booking.query.filter_by(user_id=session["user_id"]).all()
    bookings = []
    for b in bookings_raw:
        t = Trek.query.get(b.trek_id)
        bookings.append({
            "id": b.id,
            "trek_name": t.name if t else "-",
            "start_date": t.start_date if t else "-",
            "end_date": t.end_date if t else "-",
            "booking_date": b.booking_date,
            "status": b.status
        })

    return render_template("user_bookings.html", bookings=bookings, active="bookings")


@app.route("/user/bookings/cancel/<int:booking_id>")
def user_cancel_booking(booking_id):
    if session.get("role") != "user":
        return redirect(url_for("login"))

    booking = Booking.query.filter_by(id=booking_id, user_id=session["user_id"]).first()

    if booking and booking.status == "Booked":
        booking.status = "Cancelled"
        trek = Trek.query.get(booking.trek_id)
        if trek:
            trek.available_slots = trek.available_slots + 1
        db.session.commit()

    return redirect(url_for("user_my_bookings"))


@app.route("/user/history")
def user_history():
    if session.get("role") != "user":
        return redirect(url_for("login"))

    bookings_raw = Booking.query.filter_by(user_id=session["user_id"], status="Completed").all()
    history = []
    for b in bookings_raw:
        t = Trek.query.get(b.trek_id)
        history.append({
            "trek_name": t.name if t else "-",
            "start_date": t.start_date if t else "-",
            "end_date": t.end_date if t else "-",
            "status": b.status
        })

    return render_template("user_history.html", history=history, active="history")


@app.route("/user/profile", methods=["GET", "POST"])
def user_profile():
    if session.get("role") != "user":
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])

    if request.method == "POST":
        user.name = request.form["name"]
        user.contact = request.form["contact"]
        db.session.commit()
        session["name"] = user.name

    return render_template("user_profile.html", user=user, active="profile")


if __name__ == "__main__":
    app.run(debug=True)
