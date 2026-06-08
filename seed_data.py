from werkzeug.security import generate_password_hash
from app import app
from database import db
from models import User, Patient, Specialty, Doctor, Symptom, DiagnosisRule, ScheduleSlot


def add_user(username, password, role, full_name=None, phone=None):
    user = User(username=username, password_hash=generate_password_hash(password), role=role)
    db.session.add(user)
    db.session.flush()
    if role == "patient":
        db.session.add(Patient(user_id=user.id, full_name=full_name or "Іваненко Іван Іванович", phone=phone or "+380441234567"))
    return user


def seed():
    db.drop_all()
    db.create_all()

    add_user("patient@example.com", "patient123", "patient", "Іваненко Іван Іванович", "+380441234567")
    add_user("doctor@example.com", "doctor123", "doctor")
    add_user("admin@example.com", "admin123", "admin")

    specialties = [
        ("Сімейний лікар", "Первинна консультація та загальні симптоми"),
        ("Терапевт", "Загальні скарги, температура, кашель, слабкість"),
        ("Кардіолог", "Біль у грудях, підвищений тиск, задишка"),
        ("Невролог", "Головний біль, запаморочення, оніміння"),
        ("Дерматолог", "Висип, свербіж, зміни шкіри"),
        ("Гастроентеролог", "Біль у животі, нудота, печія"),
    ]
    spec = {}
    for name, desc in specialties:
        item = Specialty(name=name, description=desc)
        db.session.add(item)
        spec[name] = item
    db.session.commit()

    symptoms = [
        "температура", "кашель", "біль у горлі", "слабкість",
        "біль у грудях", "задишка", "підвищений тиск",
        "головний біль", "запаморочення", "оніміння",
        "висип", "свербіж", "біль у животі", "печія", "нудота",
    ]
    sym = {}
    for name in symptoms:
        item = Symptom(name=name)
        db.session.add(item)
        sym[name] = item
    db.session.commit()

    rules = [
        ("температура", "Терапевт", 3), ("кашель", "Терапевт", 3), ("біль у горлі", "Терапевт", 2), ("слабкість", "Сімейний лікар", 2),
        ("біль у грудях", "Кардіолог", 5), ("задишка", "Кардіолог", 4), ("підвищений тиск", "Кардіолог", 4),
        ("головний біль", "Невролог", 3), ("запаморочення", "Невролог", 4), ("оніміння", "Невролог", 5),
        ("висип", "Дерматолог", 5), ("свербіж", "Дерматолог", 3),
        ("біль у животі", "Гастроентеролог", 5), ("печія", "Гастроентеролог", 3), ("нудота", "Гастроентеролог", 2),
    ]
    for symptom_name, specialty_name, weight in rules:
        db.session.add(DiagnosisRule(symptom_id=sym[symptom_name].id, specialty_id=spec[specialty_name].id, weight=weight))

    doctors = [
        ("Ковальчук Олена Ігорівна", "Терапевт", "Каб. 204", 11),
        ("Коваленко Андрій Володимирович", "Кардіолог", "Каб. 302", 12),
        ("Семенюк Андрій Петрович", "Сімейний лікар", "Каб. 101", 8),
        ("Мельник Наталія Василівна", "Невролог", "Каб. 307", 10),
        ("Петренко Оксана Олегівна", "Дерматолог", "Каб. 112", 7),
        ("Павленко Ірина Василівна", "Гастроентеролог", "Каб. 214", 9),
    ]
    for full_name, specialty_name, room, exp in doctors:
        d = Doctor(full_name=full_name, specialty_id=spec[specialty_name].id, room=room, experience_years=exp, description="Лікар відповідної спеціальності")
        db.session.add(d)
        db.session.flush()
        for day, tm in [("2026-05-26", "09:00"), ("2026-05-26", "10:30"), ("2026-05-26", "11:30"), ("2026-05-27", "14:00")]:
            db.session.add(ScheduleSlot(doctor_id=d.id, slot_date=day, slot_time=tm, is_available=True))

    db.session.commit()
    print("Demo database created. Use patient@example.com / patient123")


if __name__ == "__main__":
    with app.app_context():
        seed()
