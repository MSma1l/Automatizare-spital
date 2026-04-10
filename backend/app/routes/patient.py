from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole
from app.models.doctor import Doctor, DoctorSchedule
from app.models.patient import Patient
from app.models.appointment import Appointment, AppointmentStatus
from app.models.message import Message, Conversation
from app.models.review import Review
from app.schemas import (
    PatientStats, PatientUpdate, PatientOut,
    AppointmentCreate, AppointmentOut,
    ReviewCreate, ReviewOut,
)
from app.services.auth_service import require_role
from app.services.notification_service import create_notification
from app.models.notification import NotificationType
from app.security.sanitizer import sanitize_string

router = APIRouter(prefix="/api/patient", tags=["patient"])
patient_required = require_role(UserRole.PATIENT)


def _get_patient(db: Session, user: User) -> Patient:
    patient = db.query(Patient).filter(Patient.user_id == user.id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Profil pacient negăsit")
    return patient


@router.get("/stats")
def get_patient_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(patient_required),
):
    patient = _get_patient(db, current_user)

    next_appt = (
        db.query(Appointment)
        .filter(
            Appointment.patient_id == patient.id,
            Appointment.date_time >= datetime.utcnow(),
            Appointment.status.in_([AppointmentStatus.CONFIRMED, AppointmentStatus.PENDING]),
        )
        .order_by(Appointment.date_time)
        .first()
    )

    unread = (
        db.query(Message)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .filter(
            Conversation.patient_id == patient.id,
            Message.sender_id != current_user.id,
            Message.is_read == False,
        )
        .count()
    )

    total = db.query(Appointment).filter(Appointment.patient_id == patient.id).count()

    next_appt_data = None
    if next_appt:
        next_appt_data = {
            "id": next_appt.id,
            "doctor_id": next_appt.doctor_id,
            "patient_id": next_appt.patient_id,
            "date_time": next_appt.date_time.isoformat(),
            "duration_minutes": next_appt.duration_minutes,
            "status": next_appt.status.value,
            "type": next_appt.type.value,
            "notes": next_appt.notes,
            "created_at": next_appt.created_at.isoformat(),
            "doctor_name": f"Dr. {next_appt.doctor.first_name} {next_appt.doctor.last_name}",
        }

    return {
        "next_appointment": next_appt_data,
        "unread_messages": unread,
        "total_appointments": total,
    }


@router.get("/profile")
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(patient_required),
):
    patient = _get_patient(db, current_user)
    return {
        **PatientOut.model_validate(patient).model_dump(),
        "email": current_user.email,
    }


@router.put("/profile")
def update_my_profile(
    data: PatientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(patient_required),
):
    patient = _get_patient(db, current_user)

    for field, value in data.model_dump(exclude_unset=True).items():
        if isinstance(value, str):
            value = sanitize_string(value)
        setattr(patient, field, value)

    db.commit()
    return {"message": "Profil actualizat"}


# ─── Doctors listing (public for patients) ────────────────────
@router.get("/doctors")
def list_available_doctors(
    db: Session = Depends(get_db),
    current_user: User = Depends(patient_required),
    specialty: str | None = None,
):
    from sqlalchemy import func as sqlfunc
    query = (
        db.query(Doctor)
        .join(User, Doctor.user_id == User.id)
        .filter(User.is_active == True)
    )
    if specialty:
        query = query.filter(Doctor.specialty == specialty)

    doctors = query.all()
    result = []
    for d in doctors:
        from app.models.review import Review as Rev
        avg_r = db.query(sqlfunc.avg(Rev.rating)).filter(Rev.doctor_id == d.id).scalar()
        rev_count = db.query(Rev).filter(Rev.doctor_id == d.id).count()
        result.append({
            "id": d.id,
            "first_name": d.first_name,
            "last_name": d.last_name,
            "specialty": d.specialty,
            "experience_years": d.experience_years,
            "bio": d.bio,
            "photo_url": d.photo_url,
            "cabinet": d.cabinet,
            "avg_rating": round(float(avg_r), 1) if avg_r else None,
            "review_count": rev_count,
            "schedules": [
                {"day_of_week": s.day_of_week,
                 "start_time": s.start_time.isoformat(),
                 "end_time": s.end_time.isoformat()}
                for s in d.schedules
            ],
        })
    return result


@router.get("/doctors/{doctor_id}")
def get_doctor_profile(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(patient_required),
):
    from sqlalchemy import func as sqlfunc
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Medic negăsit")

    user = db.query(User).filter(User.id == doctor.user_id).first()
    if not user.is_active:
        raise HTTPException(status_code=404, detail="Medic indisponibil")

    avg_r = db.query(sqlfunc.avg(Review.rating)).filter(Review.doctor_id == doctor.id).scalar()
    reviews = (
        db.query(Review)
        .filter(Review.doctor_id == doctor.id)
        .order_by(Review.created_at.desc())
        .limit(20)
        .all()
    )

    return {
        "id": doctor.id,
        "first_name": doctor.first_name,
        "last_name": doctor.last_name,
        "specialty": doctor.specialty,
        "experience_years": doctor.experience_years,
        "bio": doctor.bio,
        "photo_url": doctor.photo_url,
        "cabinet": doctor.cabinet,
        "avg_rating": round(float(avg_r), 1) if avg_r else None,
        "schedules": [
            {"day_of_week": s.day_of_week,
             "start_time": s.start_time.isoformat(),
             "end_time": s.end_time.isoformat()}
            for s in doctor.schedules
        ],
        "reviews": [
            {
                "rating": r.rating,
                "comment": r.comment,
                "created_at": r.created_at.isoformat(),
                "patient_name": f"{r.patient.first_name} {r.patient.last_name[0]}.",
            }
            for r in reviews
        ],
    }


@router.get("/doctors/{doctor_id}/available-slots")
def get_available_slots(
    doctor_id: int,
    date_str: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(patient_required),
):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Medic negăsit")

    target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    day_of_week = target_date.weekday()

    schedule = (
        db.query(DoctorSchedule)
        .filter(DoctorSchedule.doctor_id == doctor.id, DoctorSchedule.day_of_week == day_of_week)
        .first()
    )
    if not schedule:
        return []

    existing = (
        db.query(Appointment)
        .filter(
            Appointment.doctor_id == doctor.id,
            Appointment.date_time >= datetime.combine(target_date, schedule.start_time),
            Appointment.date_time < datetime.combine(target_date, schedule.end_time),
            Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED]),
        )
        .all()
    )
    booked_times = {a.date_time.strftime("%H:%M") for a in existing}

    slots = []
    from datetime import timedelta
    current = datetime.combine(target_date, schedule.start_time)
    end = datetime.combine(target_date, schedule.end_time)

    while current + timedelta(minutes=30) <= end:
        time_str = current.strftime("%H:%M")
        slots.append({
            "time": time_str,
            "available": time_str not in booked_times,
        })
        current += timedelta(minutes=30)

    return slots


# ─── Appointments ──────────────────────────────────────────────
@router.post("/appointments")
def create_appointment(
    data: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(patient_required),
):
    patient = _get_patient(db, current_user)

    doctor = db.query(Doctor).filter(Doctor.id == data.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Medic negăsit")

    # Check for conflicts
    existing = (
        db.query(Appointment)
        .filter(
            Appointment.doctor_id == data.doctor_id,
            Appointment.date_time == data.date_time,
            Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED]),
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Slotul este deja ocupat")

    appointment = Appointment(
        doctor_id=data.doctor_id,
        patient_id=patient.id,
        date_time=data.date_time,
        type=data.type,
        duration_minutes=data.duration_minutes,
        notes=sanitize_string(data.notes) if data.notes else None,
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    create_notification(
        db, doctor.user_id,
        "Programare nouă",
        f"Pacientul {patient.first_name} {patient.last_name} a solicitat o programare pe {data.date_time.strftime('%d.%m.%Y %H:%M')}.",
        NotificationType.APPOINTMENT,
    )

    return {"message": "Programare creată", "id": appointment.id}


@router.get("/appointments")
def get_my_appointments(
    db: Session = Depends(get_db),
    current_user: User = Depends(patient_required),
):
    patient = _get_patient(db, current_user)
    appointments = (
        db.query(Appointment)
        .filter(Appointment.patient_id == patient.id)
        .order_by(Appointment.date_time.desc())
        .all()
    )

    return [
        {
            "id": a.id,
            "doctor_id": a.doctor_id,
            "doctor_name": f"Dr. {a.doctor.first_name} {a.doctor.last_name}",
            "doctor_specialty": a.doctor.specialty,
            "date_time": a.date_time.isoformat(),
            "duration_minutes": a.duration_minutes,
            "status": a.status.value,
            "type": a.type.value,
            "notes": a.notes,
            "created_at": a.created_at.isoformat(),
        }
        for a in appointments
    ]


@router.put("/appointments/{appointment_id}/cancel")
def cancel_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(patient_required),
):
    patient = _get_patient(db, current_user)
    appointment = (
        db.query(Appointment)
        .filter(Appointment.id == appointment_id, Appointment.patient_id == patient.id)
        .first()
    )
    if not appointment:
        raise HTTPException(status_code=404, detail="Programare negăsită")

    if appointment.status in [AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED]:
        raise HTTPException(status_code=400, detail="Programarea nu poate fi anulată")

    appointment.status = AppointmentStatus.CANCELLED
    db.commit()

    create_notification(
        db, appointment.doctor.user_id,
        "Programare anulată",
        f"Pacientul {patient.first_name} {patient.last_name} a anulat programarea din {appointment.date_time.strftime('%d.%m.%Y %H:%M')}.",
        NotificationType.APPOINTMENT,
    )

    return {"message": "Programare anulată"}


# ─── Reviews ──────────────────────────────────────────────────
@router.post("/reviews")
def create_review(
    data: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(patient_required),
):
    patient = _get_patient(db, current_user)

    has_appointment = (
        db.query(Appointment)
        .filter(
            Appointment.doctor_id == data.doctor_id,
            Appointment.patient_id == patient.id,
            Appointment.status == AppointmentStatus.COMPLETED,
        )
        .first()
    )
    if not has_appointment:
        raise HTTPException(
            status_code=400,
            detail="Puteți recenza doar medicii la care ați avut consultații finalizate",
        )

    review = Review(
        doctor_id=data.doctor_id,
        patient_id=patient.id,
        appointment_id=data.appointment_id,
        rating=data.rating,
        comment=sanitize_string(data.comment) if data.comment else None,
    )
    db.add(review)
    db.commit()

    return {"message": "Recenzie adăugată"}


@router.get("/history")
def get_medical_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(patient_required),
):
    patient = _get_patient(db, current_user)
    completed = (
        db.query(Appointment)
        .filter(
            Appointment.patient_id == patient.id,
            Appointment.status == AppointmentStatus.COMPLETED,
        )
        .order_by(Appointment.date_time.desc())
        .all()
    )

    return [
        {
            "id": a.id,
            "doctor_name": f"Dr. {a.doctor.first_name} {a.doctor.last_name}",
            "doctor_specialty": a.doctor.specialty,
            "date_time": a.date_time.isoformat(),
            "type": a.type.value,
            "notes": a.notes,
        }
        for a in completed
    ]
