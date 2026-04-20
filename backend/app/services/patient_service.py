"""Shared logic for creating patient accounts (admin + doctor + AI flows)."""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.patient import Patient
from app.schemas import PatientCreate
from app.services.auth_service import hash_password
from app.services.email_service import send_welcome_email
from app.security.sanitizer import sanitize_string


def create_patient_account(db: Session, data: PatientCreate) -> Patient:
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email-ul este deja înregistrat")

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        role=UserRole.PATIENT,
    )
    db.add(user)
    db.flush()

    patient = Patient(
        user_id=user.id,
        first_name=sanitize_string(data.first_name),
        last_name=sanitize_string(data.last_name),
        birth_date=data.birth_date,
        gender=data.gender,
        phone=data.phone,
        address=sanitize_string(data.address) if data.address else None,
        insurance_number=data.insurance_number,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)

    try:
        send_welcome_email(data.email, data.first_name, "pacient")
    except Exception:
        pass

    return patient
