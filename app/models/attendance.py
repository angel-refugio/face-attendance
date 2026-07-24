from datetime import datetime
from app.extensions import db


class AttendanceRecord(db.Model):
    __tablename__ = "attendance_records"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(
        db.Integer, db.ForeignKey("employees.id"), nullable=False, index=True
    )
    check_in_time = db.Column(db.DateTime, nullable=False, default=datetime.now, index=True)
    confidence_score = db.Column(db.Float)
    status = db.Column(db.String(20), default="on_time", index=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f"<Attendance {self.employee_id} at {self.check_in_time}>"

    @property
    def is_late(self):
        return self.status == "late"
