"""Self-service profile routes for any authenticated user.

Allows changing email, password, profile photo, and personal details
regardless of role (admin/doctor/patient).
"""
import os
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User, UserRole
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.security.sanitizer import sanitize_string
from app.security.validators import validate_upload_file
from app.services.auth_service import (
    get_current_user, hash_password, verify_password,
)
from app.services.notification_service import create_notification
from app.models.notification import NotificationType

router = APIRouter(prefix="/api/me", tags=["profile"])


class EmailChange(BaseModel):
    new_email: EmailStr
    current_password: str


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=100)


class ProfileUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    # Patient-only
    birth_date: date | None = None
    gender: str | None = None
    address: str | None = None
    insurance_number: str | None = None
    # Doctor-only
    bio: str | None = None
    specialty: str | None = None
    cabinet: str | None = None
    experience_years: int | None = None


def _profile_payload(user: User, db: Session) -> dict:
    data = {
        "id": user.id,
        "email": user.email,
        "role": user.role.value,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }
    if user.role == UserRole.DOCTOR:
        doctor = db.query(Doctor).filter(Doctor.user_id == user.id).first()
        if doctor:
            data["profile"] = {
                "first_name": doctor.first_name,
                "last_name": doctor.last_name,
                "phone": doctor.phone,
                "specialty": doctor.specialty,
                "experience_years": doctor.experience_years,
                "bio": doctor.bio,
                "cabinet": doctor.cabinet,
                "photo_url": doctor.photo_url,
            }
    elif user.role == UserRole.PATIENT:
        patient = db.query(Patient).filter(Patient.user_id == user.id).first()
        if patient:
            data["profile"] = {
                "first_name": patient.first_name,
                "last_name": patient.last_name,
                "phone": patient.phone,
                "birth_date": patient.birth_date.isoformat() if patient.birth_date else None,
                "gender": patient.gender.value if patient.gender else None,
                "address": patient.address,
                "insurance_number": patient.insurance_number,
                "photo_url": patient.photo_url,
            }
    else:
        data["profile"] = {}
    return data


@router.get("")
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _profile_payload(current_user, db)


@router.put("")
def update_my_profile(
    data: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    values = data.model_dump(exclude_unset=True)

    if current_user.role == UserRole.DOCTOR:
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        if not doctor:
            raise HTTPException(status_code=404, detail="Profil medic negăsit")
        for field in ("first_name", "last_name", "phone", "specialty", "bio", "cabinet", "experience_years"):
            if field in values and values[field] is not None:
                v = values[field]
                if isinstance(v, str):
                    v = sanitize_string(v)
                setattr(doctor, field, v)
    elif current_user.role == UserRole.PATIENT:
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Profil pacient negăsit")
        for field in ("first_name", "last_name", "phone", "birth_date", "gender", "address", "insurance_number"):
            if field in values and values[field] is not None:
                v = values[field]
                if isinstance(v, str):
                    v = sanitize_string(v)
                setattr(patient, field, v)

    db.commit()
    if values:
        create_notification(
            db, current_user.id,
            "Profil actualizat",
            "Datele profilului dvs. au fost salvate.",
            NotificationType.SYSTEM,
        )
    return _profile_payload(current_user, db)


@router.put("/email")
def change_email(
    data: EmailChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Parola curentă este incorectă")

    new_email = data.new_email.lower()
    if new_email == current_user.email:
        raise HTTPException(status_code=400, detail="Acesta este deja emailul curent")

    existing = db.query(User).filter(User.email == new_email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Emailul este deja folosit")

    current_user.email = new_email
    db.commit()
    create_notification(
        db, current_user.id,
        "Email actualizat",
        f"Adresa de email a fost schimbată la {new_email}.",
        NotificationType.SYSTEM,
    )
    return {"message": "Email actualizat", "email": new_email}


@router.put("/password")
def change_password(
    data: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Parola curentă este incorectă")
    if data.new_password == data.current_password:
        raise HTTPException(status_code=400, detail="Parola nouă trebuie să fie diferită")

    current_user.password_hash = hash_password(data.new_password)
    db.commit()
    create_notification(
        db, current_user.id,
        "Parolă schimbată",
        "Parola contului dvs. a fost schimbată cu succes.",
        NotificationType.SYSTEM,
    )
    return {"message": "Parolă actualizată"}


@router.post("/photo")
async def upload_photo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await validate_upload_file(file, settings.ALLOWED_IMAGE_EXTENSIONS)

    ext = file.filename.rsplit('.', 1)[-1].lower()
    filename = f"user_{current_user.id}_{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(settings.UPLOAD_DIR, "photos", filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    photo_url = f"/api/uploads/photos/{filename}"

    if current_user.role == UserRole.DOCTOR:
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        if doctor:
            doctor.photo_url = photo_url
    elif current_user.role == UserRole.PATIENT:
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if patient:
            patient.photo_url = photo_url

    db.commit()
    create_notification(
        db, current_user.id,
        "Fotografie actualizată",
        "Poza de profil a fost încărcată cu succes.",
        NotificationType.SYSTEM,
    )
    return {"photo_url": photo_url}


@router.delete("/photo")
def delete_photo(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.DOCTOR:
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        if doctor:
            doctor.photo_url = None
    elif current_user.role == UserRole.PATIENT:
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if patient:
            patient.photo_url = None
    db.commit()
    create_notification(
        db, current_user.id,
        "Fotografie ștearsă",
        "Poza de profil a fost eliminată.",
        NotificationType.SYSTEM,
    )
    return {"message": "Fotografie ștearsă"}
