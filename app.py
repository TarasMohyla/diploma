from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
from database import db
from models import User, Patient, Doctor, Specialty, Symptom, DiagnosisRule, ScheduleSlot, Appointment
from routing_service import recommend_specialty


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    with app.app_context():
        db.create_all()

    register_routes(app)
    return app


def current_user():
    user_id = session.get("user_id")
    return User.query.get(user_id) if user_id else None


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Будь ласка, увійдіть у систему.")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if session.get("role") not in roles:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


def register_routes(app):
    @app.context_processor
    def inject_user():
        return {"current_user": current_user()}

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            username = request.form.get("username", "").strip().lower()
            full_name = request.form.get("full_name", "").strip()
            phone = request.form.get("phone", "").strip()
            password = request.form.get("password", "")

            if not username or not full_name or len(password) < 6:
                flash("Заповніть усі поля. Пароль має містити щонайменше 6 символів.")
                return render_template("register.html")

            if User.query.filter_by(username=username).first():
                flash("Користувач із таким email уже існує.")
                return render_template("register.html")

            user = User(username=username, password_hash=generate_password_hash(password), role="patient")
            db.session.add(user)
            db.session.flush()
            db.session.add(Patient(user_id=user.id, full_name=full_name, phone=phone))
            db.session.commit()
            flash("Реєстрацію завершено. Увійдіть у систему.")
            return redirect(url_for("login"))
        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username", "").strip().lower()
            password = request.form.get("password", "")
            user = User.query.filter_by(username=username).first()
            if user and check_password_hash(user.password_hash, password):
                session["user_id"] = user.id
                session["role"] = user.role
                flash("Вхід виконано успішно.")
                return redirect(url_for("dashboard"))
            flash("Неправильний email або пароль.")
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        flash("Ви вийшли із системи.")
        return redirect(url_for("index"))

    @app.route("/dashboard")
    @login_required
    def dashboard():
        role = session.get("role")
        if role == "admin":
            return redirect(url_for("admin_panel"))
        if role == "doctor":
            return redirect(url_for("doctor_dashboard"))
        return redirect(url_for("symptoms"))

    @app.route("/symptoms", methods=["GET", "POST"])
    @login_required
    @role_required("patient")
    def symptoms():
        all_symptoms = Symptom.query.order_by(Symptom.name).all()
        if request.method == "POST":
            symptom_ids = request.form.getlist("symptoms")
            diagnosis = request.form.get("diagnosis", "").strip()
            if not symptom_ids and not diagnosis:
                flash("Оберіть симптоми або введіть попередній діагноз.")
                return render_template("symptoms.html", symptoms=all_symptoms)
            specialty, scores, symptom_names = recommend_specialty(symptom_ids)
            session["last_diagnosis"] = diagnosis
            session["last_symptoms"] = ", ".join(symptom_names)
            session["recommended_specialty_id"] = specialty.id if specialty else None
            return render_template("recommendation.html", specialty=specialty, scores=scores, symptoms=symptom_names, diagnosis=diagnosis)
        return render_template("symptoms.html", symptoms=all_symptoms)

    @app.route("/doctors")
    @login_required
    @role_required("patient")
    def doctors():
        specialty_id = request.args.get("specialty_id") or session.get("recommended_specialty_id")
        specialty = Specialty.query.get(specialty_id) if specialty_id else None
        items = Doctor.query.filter_by(specialty_id=specialty.id).all() if specialty else Doctor.query.all()
        return render_template("doctors.html", doctors=items, specialty=specialty)

    @app.route("/doctor/<int:doctor_id>")
    @login_required
    @role_required("patient")
    def doctor_detail(doctor_id):
        doctor = Doctor.query.get_or_404(doctor_id)
        slots = ScheduleSlot.query.filter_by(doctor_id=doctor.id, is_available=True).order_by(ScheduleSlot.slot_date, ScheduleSlot.slot_time).all()
        return render_template("doctor_detail.html", doctor=doctor, slots=slots)

    @app.route("/appointment/create/<int:slot_id>", methods=["POST"])
    @login_required
    @role_required("patient")
    def create_appointment(slot_id):
        patient = Patient.query.filter_by(user_id=session["user_id"]).first_or_404()
        slot = ScheduleSlot.query.get_or_404(slot_id)
        if not slot.is_available:
            flash("Обраний час уже зайнятий. Оберіть інший слот.")
            return redirect(url_for("doctor_detail", doctor_id=slot.doctor_id))

        appointment = Appointment(
            patient_id=patient.id,
            doctor_id=slot.doctor_id,
            slot_id=slot.id,
            status="confirmed",
            preliminary_diagnosis=session.get("last_diagnosis", ""),
            selected_symptoms=session.get("last_symptoms", ""),
            recommended_specialty=slot.doctor.specialty.name,
        )
        slot.is_available = False
        db.session.add(appointment)
        db.session.commit()
        return render_template("appointment_confirmation.html", appointment=appointment)

    @app.route("/my-appointments")
    @login_required
    @role_required("patient")
    def my_appointments():
        patient = Patient.query.filter_by(user_id=session["user_id"]).first_or_404()
        appointments = Appointment.query.filter_by(patient_id=patient.id).order_by(Appointment.id.desc()).all()
        return render_template("my_appointments.html", appointments=appointments)

    @app.route("/doctor-dashboard")
    @login_required
    @role_required("doctor")
    def doctor_dashboard():
        appointments = Appointment.query.order_by(Appointment.id.desc()).all()
        return render_template("doctor_dashboard.html", appointments=appointments)

    @app.route("/admin")
    @login_required
    @role_required("admin")
    def admin_panel():
        stats = {
            "doctors": Doctor.query.count(),
            "specialties": Specialty.query.count(),
            "symptoms": Symptom.query.count(),
            "slots": ScheduleSlot.query.count(),
            "appointments": Appointment.query.count(),
        }
        return render_template("admin_panel.html", stats=stats)


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
