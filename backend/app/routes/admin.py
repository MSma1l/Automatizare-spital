import os
import uuid
from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.user import User, UserRole
from app.models.doctor import Doctor, DoctorSchedule
from app.models.patient import Patient
from app.models.appointment import Appointment, AppointmentStatus
from app.models.bed import Bed, BedStatus
from app.models.resource import Resource
from app.schemas import (
    DoctorCreate, DoctorUpdate, DoctorOut,
    PatientCreate, PatientOut, PatientUpdate,
    ResourceCreate, ResourceUpdate, ResourceOut,
    BedCreate, BedUpdate, BedOut,
    AdminStats,
)
from app.services.patient_service import create_patient_account
from app.services.auth_service import hash_password, require_role
from app.services.notification_service import create_notification
from app.services.email_service import send_welcome_email
from app.security.sanitizer import sanitize_string, sanitize_filename
from app.security.validators import validate_upload_file
from app.config import settings
from app.models.notification import NotificationType

router = APIRouter(prefix="/api/admin", tags=["admin"])
admin_required = require_role(UserRole.ADMIN)


# ─── Dashboard Stats ──────────────────────────────────────────
@router.get("/stats", response_model=AdminStats)
def get_admin_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    today_start = datetime.combine(date.today(), datetime.min.time())
    today_end = datetime.combine(date.today(), datetime.max.time())

    total_beds = db.query(Bed).count()
    occupied_beds = db.query(Bed).filter(Bed.status == BedStatus.OCCUPIED).count()
    total_doctors = db.query(Doctor).count()
    active_doctors = (
        db.query(Doctor)
        .join(User, Doctor.user_id == User.id)
        .filter(User.is_active == True)
        .count()
    )
    total_patients = db.query(Patient).count()
    appointments_today = (
        db.query(Appointment)
        .filter(Appointment.date_time.between(today_start, today_end))
        .count()
    )
    low_stock = (
        db.query(Resource)
        .filter(Resource.quantity <= Resource.min_quantity, Resource.min_quantity > 0)
        .count()
    )

    return AdminStats(
        total_beds=total_beds,
        occupied_beds=occupied_beds,
        total_doctors=total_doctors,
        active_doctors=active_doctors,
        total_patients=total_patients,
        appointments_today=appointments_today,
        low_stock_resources=low_stock,
    )


# ─── Doctor Management ────────────────────────────────────────
@router.get("/doctors")
def list_doctors(
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
    skip: int = 0,
    limit: int = 50,
    specialty: str | None = None,
):
    query = db.query(Doctor).join(User, Doctor.user_id == User.id)
    if specialty:
        query = query.filter(Doctor.specialty == specialty)
    doctors = query.offset(skip).limit(limit).all()

    result = []
    for d in doctors:
        user = db.query(User).filter(User.id == d.user_id).first()
        result.append({
            **DoctorOut.model_validate(d).model_dump(),
            "is_active": user.is_active if user else False,
            "email": user.email if user else None,
            "schedules": [
                {"id": s.id, "day_of_week": s.day_of_week,
                 "start_time": s.start_time.isoformat(), "end_time": s.end_time.isoformat()}
                for s in d.schedules
            ],
        })
    return result


@router.post("/doctors")
def create_doctor(
    data: DoctorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email-ul există deja")

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        role=UserRole.DOCTOR,
    )
    db.add(user)
    db.flush()

    doctor = Doctor(
        user_id=user.id,
        first_name=sanitize_string(data.first_name),
        last_name=sanitize_string(data.last_name),
        specialty=sanitize_string(data.specialty),
        experience_years=data.experience_years,
        bio=sanitize_string(data.bio) if data.bio else None,
        phone=data.phone,
        cabinet=data.cabinet,
    )
    db.add(doctor)
    db.flush()

    for s in data.schedules:
        schedule = DoctorSchedule(
            doctor_id=doctor.id,
            day_of_week=s.day_of_week,
            start_time=s.start_time,
            end_time=s.end_time,
        )
        db.add(schedule)

    db.commit()
    db.refresh(doctor)
    send_welcome_email(data.email, data.first_name, "medic")

    return {"message": "Medic creat cu succes", "doctor_id": doctor.id}


@router.put("/doctors/{doctor_id}")
def update_doctor(
    doctor_id: int,
    data: DoctorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Medicul nu a fost găsit")

    update_data = data.model_dump(exclude_unset=True, exclude={"schedules"})
    schedules_pydantic = data.schedules  # keep as Pydantic objects

    for field, value in update_data.items():
        if isinstance(value, str):
            value = sanitize_string(value)
        setattr(doctor, field, value)

    if schedules_pydantic is not None:
        db.query(DoctorSchedule).filter(DoctorSchedule.doctor_id == doctor.id).delete()
        for s in schedules_pydantic:
            schedule = DoctorSchedule(
                doctor_id=doctor.id,
                day_of_week=s.day_of_week,
                start_time=s.start_time,
                end_time=s.end_time,
            )
            db.add(schedule)

    db.commit()
    return {"message": "Medic actualizat"}


@router.post("/doctors/{doctor_id}/photo")
async def upload_doctor_photo(
    doctor_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Medicul nu a fost găsit")

    await validate_upload_file(file, settings.ALLOWED_IMAGE_EXTENSIONS)

    ext = file.filename.rsplit('.', 1)[-1].lower()
    filename = f"doctor_{doctor_id}_{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(settings.UPLOAD_DIR, "photos", filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    doctor.photo_url = f"/api/uploads/photos/{filename}"
    db.commit()

    return {"photo_url": doctor.photo_url}


@router.put("/doctors/{doctor_id}/toggle-active")
def toggle_doctor_active(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Medicul nu a fost găsit")

    user = db.query(User).filter(User.id == doctor.user_id).first()
    user.is_active = not user.is_active
    db.commit()

    status_text = "activat" if user.is_active else "dezactivat"
    return {"message": f"Contul medicului a fost {status_text}", "is_active": user.is_active}


# ─── Patient Management ───────────────────────────────────────
@router.get("/patients")
def list_patients(
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
    skip: int = 0,
    limit: int = 50,
):
    patients = db.query(Patient).offset(skip).limit(limit).all()
    result = []
    for p in patients:
        user = db.query(User).filter(User.id == p.user_id).first()
        result.append({
            **PatientOut.model_validate(p).model_dump(),
            "is_active": user.is_active if user else False,
            "email": user.email if user else None,
        })
    return result


@router.post("/patients")
def create_patient(
    data: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    patient = create_patient_account(db, data)
    return {"message": "Pacient creat cu succes", "patient_id": patient.id}


@router.get("/patients/{patient_id}")
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Pacientul nu a fost găsit")

    user = db.query(User).filter(User.id == patient.user_id).first()
    appointments = (
        db.query(Appointment)
        .filter(Appointment.patient_id == patient.id)
        .order_by(Appointment.date_time.desc())
        .all()
    )

    return {
        **PatientOut.model_validate(patient).model_dump(),
        "is_active": user.is_active,
        "email": user.email,
        "appointments": [
            {
                "id": a.id,
                "date_time": a.date_time.isoformat(),
                "status": a.status.value,
                "type": a.type.value,
                "notes": a.notes,
                "doctor_name": f"{a.doctor.first_name} {a.doctor.last_name}",
            }
            for a in appointments
        ],
    }


@router.put("/patients/{patient_id}")
def update_patient(
    patient_id: int,
    data: PatientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Pacientul nu a fost găsit")

    for field, value in data.model_dump(exclude_unset=True).items():
        if isinstance(value, str):
            value = sanitize_string(value)
        setattr(patient, field, value)

    db.commit()
    return {"message": "Pacient actualizat"}


@router.put("/patients/{patient_id}/toggle-active")
def toggle_patient_active(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Pacientul nu a fost găsit")

    user = db.query(User).filter(User.id == patient.user_id).first()
    user.is_active = not user.is_active
    db.commit()

    status_text = "activat" if user.is_active else "dezactivat"
    return {"message": f"Contul pacientului a fost {status_text}", "is_active": user.is_active}


# ─── Resource Management ──────────────────────────────────────
@router.get("/resources")
def list_resources(
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
    resource_type: str | None = None,
):
    query = db.query(Resource)
    if resource_type:
        query = query.filter(Resource.type == resource_type)
    return [ResourceOut.model_validate(r).model_dump() for r in query.all()]


@router.post("/resources")
def create_resource(
    data: ResourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    resource = Resource(
        name=sanitize_string(data.name),
        type=data.type,
        quantity=data.quantity,
        min_quantity=data.min_quantity,
        location=sanitize_string(data.location) if data.location else None,
        status=data.status,
        description=sanitize_string(data.description) if data.description else None,
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return {"message": "Resursă creată", "id": resource.id}


@router.put("/resources/{resource_id}")
def update_resource(
    resource_id: int,
    data: ResourceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resursa nu a fost găsită")

    for field, value in data.model_dump(exclude_unset=True).items():
        if isinstance(value, str):
            value = sanitize_string(value)
        setattr(resource, field, value)

    db.commit()
    return {"message": "Resursă actualizată"}


@router.delete("/resources/{resource_id}")
def delete_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resursa nu a fost găsită")

    db.delete(resource)
    db.commit()
    return {"message": "Resursă ștearsă"}


# ─── Bed Management ───────────────────────────────────────────
@router.get("/beds")
def list_beds(
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
    ward: str | None = None,
):
    query = db.query(Bed)
    if ward:
        query = query.filter(Bed.ward == ward)
    beds = query.all()

    result = []
    for b in beds:
        bed_data = BedOut.model_validate(b).model_dump()
        if b.patient_id:
            patient = db.query(Patient).filter(Patient.id == b.patient_id).first()
            bed_data["patient_name"] = f"{patient.first_name} {patient.last_name}" if patient else None
        result.append(bed_data)
    return result


@router.post("/beds")
def create_bed(
    data: BedCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    bed = Bed(
        room_number=data.room_number,
        ward=sanitize_string(data.ward),
        status=data.status,
    )
    db.add(bed)
    db.commit()
    db.refresh(bed)
    return {"message": "Pat creat", "id": bed.id}


@router.put("/beds/{bed_id}")
def update_bed(
    bed_id: int,
    data: BedUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    bed = db.query(Bed).filter(Bed.id == bed_id).first()
    if not bed:
        raise HTTPException(status_code=404, detail="Patul nu a fost găsit")

    update_data = data.model_dump(exclude_unset=True)

    if "patient_id" in update_data:
        update_data.pop("status", None)  # Don't override auto-set status
        if update_data["patient_id"]:
            bed.status = BedStatus.OCCUPIED
            bed.admitted_at = datetime.utcnow()
        else:
            bed.status = BedStatus.FREE
            bed.admitted_at = None

    for field, value in update_data.items():
        setattr(bed, field, value)

    db.commit()
    return {"message": "Pat actualizat"}


# ─── Reports ─────────────────────────────────────────────────
@router.get("/reports/occupancy")
def bed_occupancy_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    wards = db.query(Bed.ward, func.count(Bed.id)).group_by(Bed.ward).all()
    occupied = (
        db.query(Bed.ward, func.count(Bed.id))
        .filter(Bed.status == BedStatus.OCCUPIED)
        .group_by(Bed.ward)
        .all()
    )
    occupied_map = dict(occupied)

    return [
        {
            "ward": ward,
            "total": total,
            "occupied": occupied_map.get(ward, 0),
            "occupancy_rate": round(occupied_map.get(ward, 0) / total * 100, 1) if total > 0 else 0,
        }
        for ward, total in wards
    ]


@router.get("/reports/appointments")
def appointments_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
    start_date: str | None = None,
    end_date: str | None = None,
):
    query = db.query(Appointment)
    if start_date:
        query = query.filter(Appointment.date_time >= datetime.strptime(start_date, "%Y-%m-%d"))
    if end_date:
        query = query.filter(Appointment.date_time <= datetime.strptime(end_date, "%Y-%m-%d"))

    appointments = query.all()
    by_status = {}
    by_type = {}
    for a in appointments:
        by_status[a.status.value] = by_status.get(a.status.value, 0) + 1
        by_type[a.type.value] = by_type.get(a.type.value, 0) + 1

    return {
        "total": len(appointments),
        "by_status": by_status,
        "by_type": by_type,
    }


@router.get("/reports/doctors-performance")
def doctors_performance_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    doctors = db.query(Doctor).all()
    result = []
    for d in doctors:
        total_appts = db.query(Appointment).filter(Appointment.doctor_id == d.id).count()
        completed = (
            db.query(Appointment)
            .filter(Appointment.doctor_id == d.id, Appointment.status == AppointmentStatus.COMPLETED)
            .count()
        )
        cancelled = (
            db.query(Appointment)
            .filter(Appointment.doctor_id == d.id, Appointment.status == AppointmentStatus.CANCELLED)
            .count()
        )
        from app.models.review import Review
        avg_rating = db.query(func.avg(Review.rating)).filter(Review.doctor_id == d.id).scalar()

        result.append({
            "doctor_id": d.id,
            "name": f"Dr. {d.first_name} {d.last_name}",
            "specialty": d.specialty,
            "total_appointments": total_appts,
            "completed": completed,
            "cancelled": cancelled,
            "completion_rate": round(completed / total_appts * 100, 1) if total_appts > 0 else 0,
            "avg_rating": round(float(avg_rating), 1) if avg_rating else None,
        })

    return result
