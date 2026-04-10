import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.message import Conversation, Message
from app.schemas import ConversationOut, MessageOut
from app.services.auth_service import get_current_user
from app.security.sanitizer import sanitize_html
from app.security.validators import validate_upload_file
from app.config import settings

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.get("/conversations")
def get_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.DOCTOR:
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        convos = db.query(Conversation).filter(Conversation.doctor_id == doctor.id).all()
    elif current_user.role == UserRole.PATIENT:
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        convos = db.query(Conversation).filter(Conversation.patient_id == patient.id).all()
    else:
        return []

    result = []
    for c in convos:
        last_msg = (
            db.query(Message)
            .filter(Message.conversation_id == c.id)
            .order_by(Message.created_at.desc())
            .first()
        )
        unread = (
            db.query(Message)
            .filter(
                Message.conversation_id == c.id,
                Message.sender_id != current_user.id,
                Message.is_read == False,
            )
            .count()
        )
        doctor = db.query(Doctor).filter(Doctor.id == c.doctor_id).first()
        patient = db.query(Patient).filter(Patient.id == c.patient_id).first()

        result.append({
            "id": c.id,
            "doctor_id": c.doctor_id,
            "patient_id": c.patient_id,
            "doctor_name": f"Dr. {doctor.first_name} {doctor.last_name}" if doctor else None,
            "patient_name": f"{patient.first_name} {patient.last_name}" if patient else None,
            "last_message": last_msg.content if last_msg else None,
            "unread_count": unread,
            "updated_at": c.updated_at.isoformat(),
        })

    result.sort(key=lambda x: x["updated_at"], reverse=True)
    return result


@router.post("/conversations")
def create_or_get_conversation(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.PATIENT:
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Profil pacient negăsit")

        existing = (
            db.query(Conversation)
            .filter(Conversation.doctor_id == doctor_id, Conversation.patient_id == patient.id)
            .first()
        )
        if existing:
            return {"conversation_id": existing.id}

        convo = Conversation(doctor_id=doctor_id, patient_id=patient.id)
        db.add(convo)
        db.commit()
        db.refresh(convo)
        return {"conversation_id": convo.id}
    elif current_user.role == UserRole.DOCTOR:
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        if not doctor:
            raise HTTPException(status_code=404, detail="Profil medic negăsit")

        patient = db.query(Patient).filter(Patient.id == doctor_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Pacient negăsit")

        existing = (
            db.query(Conversation)
            .filter(Conversation.doctor_id == doctor.id, Conversation.patient_id == patient.id)
            .first()
        )
        if existing:
            return {"conversation_id": existing.id}

        convo = Conversation(doctor_id=doctor.id, patient_id=patient.id)
        db.add(convo)
        db.commit()
        db.refresh(convo)
        return {"conversation_id": convo.id}
    else:
        raise HTTPException(status_code=403, detail="Acces interzis")


@router.get("/conversations/{conversation_id}/messages")
def get_messages(
    conversation_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    convo = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not convo:
        raise HTTPException(status_code=404, detail="Conversație negăsită")

    # Verify user is part of conversation
    if current_user.role == UserRole.DOCTOR:
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        if not doctor or convo.doctor_id != doctor.id:
            raise HTTPException(status_code=403, detail="Acces interzis")
    elif current_user.role == UserRole.PATIENT:
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not patient or convo.patient_id != patient.id:
            raise HTTPException(status_code=403, detail="Acces interzis")

    # Mark messages as read
    db.query(Message).filter(
        Message.conversation_id == conversation_id,
        Message.sender_id != current_user.id,
        Message.is_read == False,
    ).update({"is_read": True})
    db.commit()

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    messages.reverse()

    return [MessageOut.model_validate(m).model_dump() for m in messages]


@router.post("/conversations/{conversation_id}/upload")
async def upload_file_to_chat(
    conversation_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    convo = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not convo:
        raise HTTPException(status_code=404, detail="Conversație negăsită")

    await validate_upload_file(file)

    ext = file.filename.rsplit('.', 1)[-1].lower()
    filename = f"chat_{conversation_id}_{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(settings.UPLOAD_DIR, "chat", filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    file_url = f"/api/uploads/chat/{filename}"
    file_type = "image" if ext in settings.ALLOWED_IMAGE_EXTENSIONS else "document"

    msg = Message(
        conversation_id=conversation_id,
        sender_id=current_user.id,
        file_url=file_url,
        file_type=file_type,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    return MessageOut.model_validate(msg).model_dump()
