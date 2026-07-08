from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(20))
    role = db.Column(db.String(20), nullable=False)   # admin / staff / user
    status = db.Column(db.String(20), nullable=False, default="Approved")  # Pending/Approved/Blacklisted


class Trek(db.Model):
    __tablename__ = "treks"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(150), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    available_slots = db.Column(db.Integer, nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    status = db.Column(db.String(20), nullable=False, default="Pending")
    start_date = db.Column(db.String(20))
    end_date = db.Column(db.String(20))
    description = db.Column(db.Text)


class Booking(db.Model):
    __tablename__ = "bookings"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    trek_id = db.Column(db.Integer, db.ForeignKey("treks.id"), nullable=False)
    booking_date = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Booked")


def init_db(app):
    with app.app_context():
        db.create_all()

        # pre-register admin (only if not already present) - no admin registration allowed
        admin = User.query.filter_by(email="admin@trek.com").first()
        if admin is None:
            admin = User(
                name="Admin",
                email="admin@trek.com",
                password="admin123",
                contact="9999999999",
                role="admin",
                status="Approved"
            )
            db.session.add(admin)
            db.session.commit()
