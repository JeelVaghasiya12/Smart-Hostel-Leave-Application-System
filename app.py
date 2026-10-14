import os
from datetime import date
from functools import wraps

from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from models.user import db, User
from models.leave_request import LeaveRequest
from models.notification import Notification

from sqlalchemy import create_engine

app = Flask(__name__)

MYSQL_DATABASE_URI = "mysql+pymysql://root:password@localhost/hostel_leave_db"
db_uri = os.environ.get("DATABASE_URL", MYSQL_DATABASE_URI)
if db_uri == MYSQL_DATABASE_URI:
    try:
        test_engine = create_engine(db_uri, connect_args={"connect_timeout": 1})
        with test_engine.connect():
            pass
    except Exception:
        db_uri = "sqlite:///hostel_leave.db"

app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-in-production")

db.init_app(app)

with app.app_context():
    db.create_all()
    # Wardens can't self-register, so create one default warden account.
    if not User.query.filter_by(role="warden").first():
        db.session.add(
            User("Warden", "warden@hostel.com", generate_password_hash("warden123"), "warden")
        )
        db.session.commit()


# ---------- helpers ----------

def current_user():
    user_id = session.get("user_id")
    return db.session.get(User, user_id) if user_id else None


def api_auth(role=None):
    """Protect an API route. Passes the logged-in user as the first argument."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = current_user()
            if not user:
                return jsonify(error="Please log in"), 401
            if role and user.role != role:
                return jsonify(error="Not allowed"), 403
            return fn(user, *args, **kwargs)
        return wrapper
    return decorator


def render_page(template, role=None):
    """Show an HTML page, or send the visitor to login if they aren't allowed."""
    user = current_user()
    if not user or (role and user.role != role):
        return redirect(url_for("login_page"))
    return render_template(template, user=user)


def leave_to_dict(leave):
    return {
        "id": leave.id,
        "student_name": leave.student.name,
        "reason": leave.reason,
        "from_date": leave.from_date.isoformat(),
        "to_date": leave.to_date.isoformat(),
        "status": leave.status,
    }


# ---------- pages ----------

@app.route("/")
def home():
    user = current_user()
    if not user:
        return redirect(url_for("login_page"))
    return redirect(url_for("warden_page" if user.is_warden() else "student_page"))


@app.route("/login")
def login_page():
    return render_template("login.html")


@app.route("/register")
def register_page():
    return render_template("register.html")


@app.route("/student")
def student_page():
    return render_page("student.html", role="student")


@app.route("/warden")
def warden_page():
    return render_page("warden.html", role="warden")


# ---------- auth API ----------

@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not name or not email or len(password) < 6:
        return jsonify(error="Enter your name, email and a password of at least 6 characters"), 400
    if User.query.filter_by(email=email).first():
        return jsonify(error="This email is already registered"), 409

    db.session.add(User(name, email, generate_password_hash(password), "student"))
    db.session.commit()
    return jsonify(ok=True), 201


@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify(error="Wrong email or password"), 400

    session["user_id"] = user.id
    return jsonify(redirect="/warden" if user.is_warden() else "/student")


@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify(ok=True)


# ---------- leave API ----------

@app.route("/api/leaves", methods=["GET"])
@api_auth()
def list_leaves(user):
    query = LeaveRequest.query
    if user.is_student():
        query = query.filter_by(student_id=user.id)
    leaves = query.order_by(LeaveRequest.created_at.desc()).all()
    return jsonify([leave_to_dict(leave) for leave in leaves])


@app.route("/api/leaves", methods=["POST"])
@api_auth("student")
def create_leave(user):
    data = request.get_json(silent=True) or {}
    reason = (data.get("reason") or "").strip()

    try:
        from_date = date.fromisoformat(data.get("from_date", ""))
        to_date = date.fromisoformat(data.get("to_date", ""))
    except ValueError:
        return jsonify(error="Choose valid dates"), 400

    if not reason:
        return jsonify(error="Enter a reason for your leave"), 400
    if len(reason) > 500:
        return jsonify(error="Reason must be 500 characters or fewer"), 400
    if to_date < from_date:
        return jsonify(error="The end date can't be before the start date"), 400

    leave = LeaveRequest(user.id, reason, from_date, to_date)
    db.session.add(leave)
    db.session.commit()
    return jsonify(leave_to_dict(leave)), 201


@app.route("/api/leaves/<int:leave_id>/<action>", methods=["POST"])
@api_auth("warden")
def update_leave(user, leave_id, action):
    leave = db.session.get(LeaveRequest, leave_id)
    if not leave:
        return jsonify(error="Leave request not found"), 404
    if action not in ("approve", "reject"):
        return jsonify(error="Unknown action"), 400
    if leave.status != "Pending":
        return jsonify(error=f"This request was already {leave.status.lower()}"), 400

    if action == "approve":
        leave.approve()
    else:
        leave.reject()

    message = (
        f"Your leave from {leave.from_date.strftime('%d %b')} "
        f"to {leave.to_date.strftime('%d %b %Y')} was {leave.status.lower()}."
    )
    db.session.add(Notification(leave.student_id, message))
    db.session.commit()
    return jsonify(leave_to_dict(leave))


# ---------- notifications API ----------

@app.route("/api/notifications", methods=["GET"])
@api_auth("student")
def list_notifications(user):
    items = (
        Notification.query.filter_by(student_id=user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )
    return jsonify([
        {
            "id": n.id,
            "message": n.message,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat() + "Z",  # stored in UTC
        }
        for n in items
    ])


@app.route("/api/notifications/read", methods=["POST"])
@api_auth("student")
def mark_notifications_read(user):
    for n in Notification.query.filter_by(student_id=user.id, is_read=False):
        n.mark_as_read()
    db.session.commit()
    return jsonify(ok=True)


if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "").lower() in ("1", "true")
    app.run(debug=debug_mode, port=5000)
