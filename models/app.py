from flask import Flask

from models.user import db
from models.user import User
from models.leave_request import LeaveRequest
from models.notification import Notification

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = (
    "mysql+pymysql://root:password@localhost/hostel_leave_db"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


with app.app_context():
    db.create_all()


@app.route("/")
def home():
    return "Smart Hostel Leave Application System"


if __name__ == "__main__":
    app.run(debug=True)
