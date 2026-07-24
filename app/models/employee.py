from datetime import datetime
from app.extensions import db


class Employee(db.Model):
    __tablename__ = "employees"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    department = db.Column(db.String(50))
    position = db.Column(db.String(100))
    email = db.Column(db.String(100))
    enrollment_date = db.Column(db.Date, default=datetime.now)
    status = db.Column(db.String(20), default="active", index=True)
    face_registered = db.Column(db.Boolean, default=False)
    work_days = db.Column(db.String(20), default="1,2,3,4,5")
    work_start_time = db.Column(db.String(5), default="09:00")
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    attendance_records = db.relationship(
        "AttendanceRecord",
        backref="employee",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Employee {self.name}>"

    @property
    def is_active_employee(self):
        return self.status == "active"

    @property
    def work_days_list(self):
        return [int(d) for d in self.work_days.split(",") if d.strip()]

    @property
    def work_days_display(self):
        day_names = {
            0: "Lun", 1: "Mar", 2: "Mié", 3: "Jue", 4: "Vie", 5: "Sáb", 6: "Dom"
        }
        return ", ".join([day_names.get(d, "?") for d in self.work_days_list])

    def should_work_today(self):
        today_weekday = datetime.now().weekday()
        return today_weekday in self.work_days_list

    def today_attendance(self):
        from app.models.attendance import AttendanceRecord

        today = datetime.now().date()
        return (
            AttendanceRecord.query.filter(
                AttendanceRecord.employee_id == self.id,
                db.func.date(AttendanceRecord.check_in_time) == today,
            )
            .order_by(AttendanceRecord.check_in_time.desc())
            .all()
        )
