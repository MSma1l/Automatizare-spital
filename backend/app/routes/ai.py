"""AI proxy routes - bridge between frontend and AI service.

All AI agents live in the `ai` container (port 8001).
This router proxies authenticated requests to it.
"""
import logging
import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.models.user import User, UserRole
from app.services.auth_service import get_current_user, require_role

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["ai"])

AI_BASE = settings.AI_SERVICE_URL.rstrip("/")
TIMEOUT = httpx.Timeout(15.0, connect=5.0)


class AskRequest(BaseModel):
    question: str


class ParseTextRequest(BaseModel):
    text: str


async def _get(path: str, params: dict | None = None):
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.get(f"{AI_BASE}{path}", params=params)
            r.raise_for_status()
            return r.json()
    except httpx.HTTPError as e:
        logger.error(f"AI service GET {path} failed: {e}")
        raise HTTPException(status_code=503, detail="Serviciul AI este indisponibil")


async def _post(path: str, json: dict | None = None):
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.post(f"{AI_BASE}{path}", json=json)
            r.raise_for_status()
            return r.json()
    except httpx.HTTPError as e:
        logger.error(f"AI service POST {path} failed: {e}")
        raise HTTPException(status_code=503, detail="Serviciul AI este indisponibil")


# ─── Help Agent (medical FAQ) — available to ALL authenticated users ─
@router.post("/help/ask")
async def ask_medical_question(
    req: AskRequest,
    current_user: User = Depends(get_current_user),
):
    """Ask a medical question to the trained AI assistant (TF-IDF, RO+RU)."""
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="Întrebare goală")
    return await _post("/agents/help/ask", {"question": req.question.strip()})


@router.get("/help/faq")
async def get_faq_topics(current_user: User = Depends(get_current_user)):
    """List FAQ categories and example questions."""
    return await _get("/agents/help/faq")


# ─── Registration Agent (admin + doctor only) ────────────────────────
def _admin_or_doctor(user: User = Depends(get_current_user)) -> User:
    if user.role not in (UserRole.ADMIN, UserRole.DOCTOR):
        raise HTTPException(status_code=403, detail="Doar admin sau medic")
    return user


@router.post("/registration/parse")
async def registration_parse(
    req: ParseTextRequest,
    current_user: User = Depends(_admin_or_doctor),
):
    """Parse patient registration text (ID card / insurance card / intake form)
    and return structured fields ready to populate the create-patient form."""
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Text gol")
    return await _post("/agents/registration/parse", {"text": req.text.strip()})


@router.get("/registration/info")
async def registration_info(current_user: User = Depends(_admin_or_doctor)):
    return await _get("/agents/registration/info")


# ─── Doctor-only: AI recommendations ─────────────────────────────────
@router.get("/recommendations")
async def get_my_recommendations(
    current_user: User = Depends(require_role(UserRole.DOCTOR)),
):
    """Doctor: get personalized AI follow-up recommendations."""
    from app.database import SessionLocal
    from app.models.doctor import Doctor

    db = SessionLocal()
    try:
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        if not doctor:
            raise HTTPException(status_code=404, detail="Profil medic negăsit")
        doctor_id = doctor.id
    finally:
        db.close()

    return await _get(f"/agents/recommendations/{doctor_id}")


@router.get("/scheduling/suggest-slots")
async def suggest_slots(
    doctor_id: int,
    date: str,
    current_user: User = Depends(get_current_user),
):
    """AI suggests best appointment slots for a doctor on a given date."""
    return await _get("/agents/scheduling/suggest-slots", {"doctor_id": doctor_id, "date": date})


# ─── Admin-only: monitoring + predictions + resources ────────────────
admin_required = require_role(UserRole.ADMIN)


@router.get("/monitoring")
async def admin_monitoring(current_user: User = Depends(admin_required)):
    """Admin: live resource & operational status from MonitoringAgent."""
    return await _get("/agents/monitoring")


@router.get("/predictions")
async def admin_predictions(current_user: User = Depends(admin_required)):
    """Admin: PredictiveAgent forecasts (patient volume, etc)."""
    return await _get("/agents/predictions")


@router.get("/resources")
async def admin_resources(current_user: User = Depends(admin_required)):
    """Admin: ResourceAllocationAgent recommendations (beds/equipment)."""
    return await _get("/agents/resources")


@router.get("/resources/suggest-bed")
async def admin_suggest_bed(
    ward: str | None = None,
    current_user: User = Depends(admin_required),
):
    return await _get("/agents/resources/suggest-bed", {"ward": ward} if ward else None)


@router.get("/scheduling")
async def admin_scheduling(current_user: User = Depends(admin_required)):
    """Admin: SchedulingAgent global view (conflicts + optimization)."""
    return await _get("/agents/scheduling")


@router.get("/recommendations-all")
async def admin_recommendations(current_user: User = Depends(admin_required)):
    return await _get("/agents/recommendations")


@router.get("/notifications-status")
async def admin_notifications(current_user: User = Depends(admin_required)):
    return await _get("/agents/notifications")


@router.get("/health")
async def ai_health(current_user: User = Depends(get_current_user)):
    return await _get("/health")


@router.get("/agents")
async def list_ai_agents(current_user: User = Depends(get_current_user)):
    """Return metadata about all AI agents available in the system."""
    return {
        "agents": [
            {"key": "help", "name": "Asistent Medical AI", "description": "Răspunde la întrebări medicale (RO+RU) folosind 220+ Q&A antrenate.", "users": ["patient", "doctor", "admin"]},
            {"key": "scheduling", "name": "Programări Inteligente", "description": "Sugerează cele mai bune sloturi disponibile, detectează conflicte.", "users": ["doctor", "admin"]},
            {"key": "recommendation", "name": "Recomandări Follow-up", "description": "Propune doctorului acțiuni de follow-up pentru pacienți.", "users": ["doctor"]},
            {"key": "resource", "name": "Alocare Resurse", "description": "ML model pentru optimizare paturi/echipamente.", "users": ["admin"]},
            {"key": "monitoring", "name": "Monitorizare Spital", "description": "Status resurse și alerte la 10 min.", "users": ["admin"]},
            {"key": "predictive", "name": "Predicții Volum Pacienți", "description": "Forecast time-series pentru fluxul de pacienți.", "users": ["admin"]},
            {"key": "notification", "name": "Notificări Automate", "description": "Reminder programări cu 24h înainte.", "users": ["admin"]},
            {"key": "registration", "name": "Înregistrare Pacient AI", "description": "Extrage datele pacientului din acte (buletin, card asigurare) și completează formularul automat.", "users": ["admin", "doctor"]},
        ]
    }
