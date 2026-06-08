from database import db

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), nullable=False, default="patient")

    patient = db.relationship("Patient", backref="user", uselist=False, cascade="all, delete-orphan")

class Patient(db.Model):
    __tablename__ = "patients"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    full_name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(40))

    appointments = db.relationship("Appointment", backref="patient", lazy=True)

class Specialty(db.Model):
    __tablename__ = "specialties"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text)

    doctors = db.relationship("Doctor", backref="specialty", lazy=True)
    rules = db.relationship("DiagnosisRule", backref="specialty", lazy=True)

class Doctor(db.Model):
    __tablename__ = "doctors"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    specialty_id = db.Column(db.Integer, db.ForeignKey("specialties.id"), nullable=False)
    description = db.Column(db.Text)
    room = db.Column(db.String(40))
    experience_years = db.Column(db.Integer, default=0)

    slots = db.relationship("ScheduleSlot", backref="doctor", lazy=True)
    appointments = db.relationship("Appointment", backref="doctor", lazy=True)

class Symptom(db.Model):
    __tablename__ = "symptoms"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)

    rules = db.relationship("DiagnosisRule", backref="symptom", lazy=True)

class DiagnosisRule(db.Model):
    __tablename__ = "diagnosis_rules"

    id = db.Column(db.Integer, primary_key=True)
    symptom_id = db.Column(db.Integer, db.ForeignKey("symptoms.id"), nullable=False)
    specialty_id = db.Column(db.Integer, db.ForeignKey("specialties.id"), nullable=False)
    weight = db.Column(db.Integer, nullable=False, default=1)

class ScheduleSlot(db.Model):
    __tablename__ = "schedule_slots"

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctors.id"), nullable=False)
    slot_date = db.Column(db.String(20), nullable=False)
    slot_time = db.Column(db.String(20), nullable=False)
    is_available = db.Column(db.Boolean, nullable=False, default=True)

    appointment = db.relationship("Appointment", backref="slot", uselist=False)

class Appointment(db.Model):
    __tablename__ = "appointments"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctors.id"), nullable=False)
    slot_id = db.Column(db.Integer, db.ForeignKey("schedule_slots.id"), nullable=False, unique=True)
    status = db.Column(db.String(30), nullable=False, default="created")
    preliminary_diagnosis = db.Column(db.Text)
    selected_symptoms = db.Column(db.Text)
    recommended_specialty = db.Column(db.String(120))
