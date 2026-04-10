import os
import logging
import socketio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database import engine, Base
from app.security.rate_limiter import limiter
from app.models import *  # noqa: F401,F403

# ─── Create tables ────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ─── FastAPI app ──────────────────────────────────────────────
app = FastAPI(
    title="Hospital DSS API",
    description="Sistem Inteligent de Sprijin Decizional pentru Instituții Spitalicești",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Socket.IO ────────────────────────────────────────────────
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    logger=False,
)

from app.websocket.chat_handler import register_chat_handlers
from app.websocket.video_handler import register_video_handlers

register_chat_handlers(sio)
register_video_handlers(sio)

socket_app = socketio.ASGIApp(sio, other_app=app)

# ─── Routes ───────────────────────────────────────────────────
from app.routes.auth import router as auth_router
from app.routes.admin import router as admin_router
from app.routes.doctor import router as doctor_router
from app.routes.patient import router as patient_router
from app.routes.chat import router as chat_router
from app.routes.video import router as video_router
from app.routes.appointments import router as appointments_router
from app.routes.resources import router as resources_router

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(doctor_router)
app.include_router(patient_router)
app.include_router(chat_router)
app.include_router(video_router)
app.include_router(appointments_router)
app.include_router(resources_router)


# ─── File serving ─────────────────────────────────────────────
@app.get("/api/uploads/{path:path}")
async def serve_upload(path: str):
    file_path = os.path.join(settings.UPLOAD_DIR, path)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return JSONResponse(status_code=404, content={"detail": "Fișier negăsit"})


# ─── Health check ─────────────────────────────────────────────
@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": "hospital-dss-backend"}


# ─── Seed data on first run ──────────────────────────────────
@app.on_event("startup")
async def startup_event():
    from app.database import SessionLocal
    from app.models.user import User, UserRole
    from app.services.auth_service import hash_password

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
        if not admin:
            admin_user = User(
                email="admin@spital.ro",
                password_hash=hash_password("admin123"),
                role=UserRole.ADMIN,
            )
            db.add(admin_user)
            db.commit()
            logging.info("Admin default creat: admin@spital.ro / admin123")
    finally:
        db.close()

    os.makedirs(os.path.join(settings.UPLOAD_DIR, "photos"), exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "chat"), exist_ok=True)


# ─── Replace app with socket_app for uvicorn ─────────────────
app = socket_app
