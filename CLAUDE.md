# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Online doctor appointment system (bachelor's thesis project). Patients enter symptoms or a preliminary diagnosis, receive a specialty recommendation via a weighted rule algorithm, then pick a doctor and a time slot.

## Running the app

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python seed_data.py          # populate DB with test data (run once)
python app.py                # starts Flask dev server on http://127.0.0.1:5000
```

Test credentials: `patient@example.com / patient123`, `doctor@example.com / doctor123`, `admin@example.com / admin123`.

## Architecture

All Flask routes live in `app.py` inside `register_routes()`. There is no Blueprint separation. Authentication is cookie-session-based (`session["user_id"]`, `session["role"]`); `login_required` and `role_required` are plain function decorators defined in the same file.

**Data model** (`models.py`) — key relationships:
- `User` (role: `patient` | `doctor` | `admin`) → one `Patient` profile (created at registration)
- `Doctor` → belongs to a `Specialty`; has many `ScheduleSlot`s
- `DiagnosisRule` links `Symptom` → `Specialty` with an integer `weight`
- `Appointment` references `Patient`, `Doctor`, and a unique `ScheduleSlot`; booking flips `slot.is_available = False`

**Specialty recommendation** (`routing_service.py`): sums `DiagnosisRule.weight` per specialty for the selected symptom IDs, returns the highest-scoring specialty. Falls back to "Сімейний лікар" when no rules match.

**Database**: SQLite file `doctor_appointment.db` in the app directory. `db.create_all()` runs on startup; `seed_data.py` populates reference data and test users.

**Templates**: Jinja2 in `templates/`, all extending `base.html`. `current_user` is injected globally via a `context_processor`.

**Config** (`config.py`): `SECRET_KEY` and `SQLALCHEMY_DATABASE_URI` — change `SECRET_KEY` before any non-demo deployment.
