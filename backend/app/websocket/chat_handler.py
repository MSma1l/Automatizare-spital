import socketio
from datetime import datetime
from app.database import SessionLocal
from app.models.message import Message, Conversation
from app.models.user import User
from app.services.auth_service import decode_token
from app.security.sanitizer import sanitize_html

# Connected users: {user_id: sid}
connected_users: dict[int, str] = {}


def register_chat_handlers(sio: socketio.AsyncServer):

    @sio.event
    async def connect(sid, environ, auth):
        if auth and auth.get("token"):
            payload = decode_token(auth["token"])
            if payload:
                user_id = int(payload["sub"])
                connected_users[user_id] = sid
                await sio.save_session(sid, {"user_id": user_id})
                await sio.emit("user_online", {"user_id": user_id})
                return True
        return False

    @sio.event
    async def disconnect(sid):
        session = await sio.get_session(sid)
        if session:
            user_id = session.get("user_id")
            if user_id and user_id in connected_users:
                del connected_users[user_id]
                await sio.emit("user_offline", {"user_id": user_id})

    @sio.event
    async def send_message(sid, data):
        session = await sio.get_session(sid)
        if not session:
            return

        user_id = session["user_id"]
        conversation_id = data.get("conversation_id")
        content = data.get("content", "")

        if not conversation_id or not content.strip():
            return

        content = sanitize_html(content)

        db = SessionLocal()
        try:
            convo = db.query(Conversation).filter(Conversation.id == conversation_id).first()
            if not convo:
                return

            msg = Message(
                conversation_id=conversation_id,
                sender_id=user_id,
                content=content,
            )
            db.add(msg)
            convo.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(msg)

            message_data = {
                "id": msg.id,
                "conversation_id": msg.conversation_id,
                "sender_id": msg.sender_id,
                "content": msg.content,
                "file_url": None,
                "file_type": None,
                "is_read": False,
                "created_at": msg.created_at.isoformat(),
            }

            # Send to both participants
            from app.models.doctor import Doctor
            from app.models.patient import Patient
            doctor = db.query(Doctor).filter(Doctor.id == convo.doctor_id).first()
            patient = db.query(Patient).filter(Patient.id == convo.patient_id).first()

            if doctor and doctor.user_id in connected_users:
                await sio.emit("new_message", message_data, to=connected_users[doctor.user_id])
            if patient and patient.user_id in connected_users:
                await sio.emit("new_message", message_data, to=connected_users[patient.user_id])
        finally:
            db.close()

    @sio.event
    async def typing(sid, data):
        session = await sio.get_session(sid)
        if not session:
            return

        conversation_id = data.get("conversation_id")
        db = SessionLocal()
        try:
            convo = db.query(Conversation).filter(Conversation.id == conversation_id).first()
            if not convo:
                return

            from app.models.doctor import Doctor
            from app.models.patient import Patient
            user_id = session["user_id"]
            doctor = db.query(Doctor).filter(Doctor.id == convo.doctor_id).first()
            patient = db.query(Patient).filter(Patient.id == convo.patient_id).first()

            target_user_id = None
            if doctor and doctor.user_id == user_id and patient:
                target_user_id = patient.user_id
            elif patient and patient.user_id == user_id and doctor:
                target_user_id = doctor.user_id

            if target_user_id and target_user_id in connected_users:
                await sio.emit(
                    "user_typing",
                    {"conversation_id": conversation_id, "user_id": user_id},
                    to=connected_users[target_user_id],
                )
        finally:
            db.close()
