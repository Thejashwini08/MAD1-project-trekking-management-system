# Trekking Management Application — MAD 1

A trek booking and coordination web app built for adventure organizations, connecting the **Admin**, **Trek Staff**, and **Trekkers (Users)** around one shared set of treks and bookings.

The whole app is a single Flask project — Jinja2 templates render every page server-side, styled with Bootstrap 5, and the database is SQLite. There is no separate frontend build, no JavaScript, and no external API — every action is a normal form submission or link click that Flask handles and re-renders.

---

## 1. What this app does

- **Admin** logs in with a pre-seeded account, creates and edits treks, approves new Trek Staff registrations, assigns staff to specific treks, and can blacklist/unblacklist any Staff or User account. The admin dashboard shows live counts of treks, staff, users, and bookings, plus the 5 most recent bookings.
- **Trek Staff** accounts are created by self-registration, but a new staff account stays `Pending` until the Admin approves it — only then can the staff member log in and reach their dashboard. Each staff member sees only the treks assigned to them, can update a trek's available slots and status, and can view everyone booked on their treks.
- **Users (Trekkers)** self-register (approved immediately), browse and filter open treks by difficulty and location, book a slot, cancel a booking (which frees the slot back up), edit their profile, and look at their booking history and past (completed) treks.

A trek moves through the lifecycle `Pending → Approved → Open → Closed/Completed`, and a booking follows `Booked → Cancelled/Completed`. When a staff member marks a trek `Completed`, every still-`Booked` booking on that trek is automatically flipped to `Completed` too.

## 2. Project layout

```
trekking_final/
├── app.py                     # all routes: auth, admin, staff, and user views
├── models.py                  # User, Trek, Booking (SQLAlchemy models) + init_db()
├── requirements.txt
├── static/                    # place for any custom images/assets (currently empty)
└── templates/
    ├── base.html               # shared layout, nav bar, Bootstrap + Google Font imports
    ├── login.html / register.html
    ├── admin_dashboard.html / admin_treks.html / admin_add_trek.html / admin_edit_trek.html
    ├── admin_staff.html / admin_users.html / admin_bookings.html / admin_search.html
    ├── staff_dashboard.html / staff_trek.html
    └── user_dashboard.html / user_treks.html / user_trek_details.html
        user_bookings.html / user_history.html / user_profile.html
```

There's no `routes/` package or blueprints here — every view function lives directly in `app.py`, grouped under comment headers (`AUTH`, `ADMIN`, `STAFF`, `USER`) for readability.

## 3. Running it locally

Only one thing needs to run — the Flask app itself.

```bash
cd trekking_management_app
pip install -r requirements.txt
python app.py                       # http://127.0.0.1:5000
```

The database (`trekking.db`) is created automatically the first time the app starts, via `init_db()` in `models.py`, and the single Admin account is seeded programmatically at the same time — there's no admin registration page.

**Default admin login:** `admin@trek.com` / `admin123`

## 4. Roles and access control

Access control is done with simple session checks at the top of each view (`session.get("role") != "admin"`, etc.) rather than a Flask extension like Flask-Login — every protected route redirects back to `/login` if the session role doesn't match what that page needs.

- A **Trek Staff** account is unusable until the Admin approves it (`status` moves from `Pending` to `Approved`); a blacklisted account is blocked from logging in again, same as a blacklisted user.
- A **User** account is `Approved` the moment they register, since only staff accounts need admin sign-off before they can log in.

## 5. Notable business rules enforced server-side

- A user cannot book the same trek twice while an existing booking on it is `Booked` or `Completed` — only a `Cancelled` booking on that trek frees them up to book it again.
- Booking is only allowed while a trek's status is exactly `Open` and `available_slots` is greater than zero — checked in the route handler, not just hidden in the template.
- Cancelling a booking puts the freed slot straight back into the trek's `available_slots`.
- Only the staff member a trek is actually assigned to (`staff_id`) can view or update that trek's slots/status or see its participant list.
- Marking a trek `Completed` cascades: every `Booked` booking on that trek is updated to `Completed` in the same request.
- Admin search covers treks (by name/location), staff, and users (by name or numeric ID) from one shared search page.
