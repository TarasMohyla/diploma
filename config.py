from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = "demo-secret-key-change-before-production"
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{BASE_DIR / 'doctor_appointment.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
