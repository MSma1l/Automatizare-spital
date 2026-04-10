from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.user import User, UserRole
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.appointment import Appointment, AppointmentStatus
from app.models.message import Message, Conversation
from app.models.review import Review
from app.schemas import DoctorStats, AppointmentUpdate, DoctorOut
from app.services.auth_service import require_role, get_current_user
from app.services.notification_service import create_notification
from app.models.notification import NotificationType
from app.security.sanitizer import sanitize_string

router = APIRouter(prefix="/api/doctor", tags=["doctor"])
doctor_required = require_role(UserRole.DOCTOR)


def _get_doctor(db: Session, user: User) -> Doctor:
    doctor = db.query(Doctor).filter(Doctor.user_id == user.id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Profil medic negăsit")
    return doctor


@router.get("/stats", response_model=DoctorStats)
def get_doctor_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(doctor_required),
):
    doctor = _get_doctor(db, current_user)
    today_start = datetime.combine(date.today(), datetime.min.time())
    today_end = datetime.combine(date.today(), datetime.max.time())

    appointments_today = (
        db.query(Appointment)
        .filter(
            Appointment.doctor_id == doctor.id,
            Appointment.date_time.between(today_start, today_end),
            Appointment.status.in_([AppointmentStatus.CONFIRMED, AppointmentStatus.PENDING]),
        )
        .count()
    )

    total_patients = (
        db.query(Appointment.patient_id)
        .filter(Appointment.doctor_id == doctor.id)
        .distinct()
        .count()
    )

    unread_messages = (
        db.query(Message)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .filter(
            Conversation.doctor_id == doctor.id,
            Message.sender_id != current_user.id,
            Message.is_read == False,
        )
        .count()
    )

    pending = (
        db.query(Appointment)
        .filter(Appointment.doctor_id == doctor.id, Appointment.status == AppointmentStatus.PENDING)
        .count()
    )

    return DoctorStats(
        appointments_today=appointments_today,
        total_patients=total_patients,
        unread_messages=unread_messages,
        pending_appointments=pending,
    )


@router.get("/profile")
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(doctor_required),
):
    doctor = _get_doctor(db, current_user)
    avg_rating = db.query(func.avg(Review.rating)).filter(Review.doctor_id == doctor.id).scalar()
    review_count = db.query(Review).filter(Review.doctor_id == doctor.id).count()

    return {
        **DoctorOut.model_validate(doctor).model_dump(),
        "email": current_user.email,
        "avg_rating": round(float(avg_rating), 1) if avg_rating else None,
        "review_count": review_count,
        "schedules": [
            {"id": s.id, "day_of_week": s.day_of_week,
             "start_time": s.start_time.isoformat(), "end_time": s.end_time.isoformat()}
            for s in doctor.schedules
        ],
    }


@router.get("/appointments")
def get_appointments(
    db: Session = Depends(get_db),
    current_user: User = Depends(doctor_required),
    status_filter: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
):
    doctor = _get_doctor(db, current_user)
    query = db.query(Appointment).filter(Appointment.doctor_id == doctor.id)

    if status_filter:
        query = query.filter(Appointment.status == status_filter)
    if date_from:
        query = query.filter(Appointment.date_time >= date_from)
    if date_to:
        query = query.filter(Appointment.date_time <= date_to)

    appointments = query.order_by(Appointment.date_time).all()

    return [
        {
            "id": a.id,
            "patient_id": a.patient_id,
            "patient_name": f"{a.patient.first_name} {a.patient.last_name}",
            "date_time": a.date_time.isoformat(),
            "duration_minutes": a.duration_minutes,
            "status": a.status.value,
            "type": a.type.value,
            "notes": a.notes,
        }
        for a in appointments
    ]


@router.put("/appointments/{appointment_id}")
def update_appointment(
    appointment_id: int,
    data: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(doctor_required),
):
    doctor = _get_doctor(db, current_user)
    appointment = (
        db.query(Appointment)
        .filter(Appointment.id == appointment_id, Appointment.doctor_id == doctor.id)
        .first()
    )
    if not appointment:
        raise HTTPException(status_code=404, detail="Programare negăsită")

    if data.status:
        appointment.status = data.status
        # Notify patient
        patient = db.query(Patient).filter(Patient.id == appointment.patient_id).first()
        if patient and data.status in ["confirmed", "rejected"]:
            status_text = "confirmată" if data.status == "confirmed" else "refuzată"
            create_notification(
                db, patient.user_id,
                "Actualizare programare",
                f"Programarea cu Dr. {doctor.first_name} {doctor.last_name} a fost {status_text}.",
                NotificationType.APPOINTMENT,
            )

    if data.notes:
        appointment.notes = sanitize_string(data.notes)

    db.commit()
    return {"message": "Programare actualizată"}


@router.get("/patients")
def get_my_patients(
    db: Session = Depends(get_db),
    current_user: User = Depends(doctor_required),
):
    doctor = _get_doctor(db, current_user)
    patient_ids = (
        db.query(Appointment.patient_id)
        .filter(Appointment.doctor_id == doctor.id)
        .distinct()
        .all()
    )
    patient_ids = [pid for (pid,) in patient_ids]

    patients = db.query(Patient).filter(Patient.id.in_(patient_ids)).all()
    result = []
    for p in patients:
        last_appt = (
            db.query(Appointment)
            .filter(Appointment.patient_id == p.id, Appointment.doctor_id == doctor.id)
            .order_by(Appointment.date_time.desc())
            .first()
        )
        result.append({
            "id": p.id,
            "first_name": p.first_name,
            "last_name": p.last_name,
            "phone": p.phone,
            "birth_date": p.birth_date.isoformat() if p.birth_date else None,
            "gender": p.gender.value if p.gender else None,
            "last_appointment": last_appt.date_time.isoformat() if last_appt else None,
            "last_status": last_appt.status.value if last_appt else None,
        })
    return result
