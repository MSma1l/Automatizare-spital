"""AI Service API - FastAPI endpoints for all agents."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Query, UploadFile, File, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from models.db import get_db, SessionLocal
from agents.resource_agent import ResourceAllocationAgent
from agents.scheduling_agent import SchedulingAgent
from agents.monitoring_agent import MonitoringAgent
from agents.predictive_agent import PredictiveAgent
from agents.recommendation_agent import RecommendationAgent
from agents.notification_agent import NotificationAgent
from agents.help_agent import HelpAgent
from agents.registration_agent import RegistrationAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def run_monitoring():
    """Scheduled: monitoring every 10 minutes."""
    db = SessionLocal()
    try:
        agent = MonitoringAgent(db)
        agent.run()
    except Exception as e:
        logger.error(f"Monitoring error: {e}")
    finally:
        db.close()


def run_notifications():
    """Scheduled: notification checks every 15 minutes."""
    db = SessionLocal()
    try:
        agent = NotificationAgent(db)
        agent.run()
    except Exception as e:
        logger.error(f"Notification error: {e}")
    finally:
        db.close()


def run_predictions():
    """Scheduled: predictions every hour."""
    db = SessionLocal()
    try:
        agent = PredictiveAgent(db)
        agent.run()
    except Exception as e:
        logger.error(f"Prediction error: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start scheduled jobs
    scheduler.add_job(run_monitoring, 'interval', minutes=10, id='monitoring')
    scheduler.add_job(run_notifications, 'interval', minutes=15, id='notifications')
    scheduler.add_job(run_predictions, 'interval', hours=1, id='predictions')
    scheduler.start()
    logger.info("AI Service started with scheduled agents")
    yield
    scheduler.shutdown()


app = FastAPI(
    title="Hospital DSS AI Service",
    description="AI Agents for Hospital Decision Support",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
def health():
    return {"status": "healthy", "service": "hospital-dss-ai"}


# ─── Resource Agent ──────────────────────────────────────────
@app.get("/agents/resources")
def run_resource_agent(db: Session = Depends(get_db)):
    agent = ResourceAllocationAgent(db)
    agent.train()
    return agent.run()


@app.get("/agents/resources/suggest-bed")
def suggest_bed(ward: str = None, db: Session = Depends(get_db)):
    agent = ResourceAllocationAgent(db)
    result = agent.suggest_bed(ward)
    return result or {"message": "Nu sunt paturi disponibile"}


# ─── Scheduling Agent ────────────────────────────────────────
@app.get("/agents/scheduling")
def run_scheduling_agent(db: Session = Depends(get_db)):
    agent = SchedulingAgent(db)
    return agent.run()


@app.get("/agents/scheduling/suggest-slots")
def suggest_slots(
    doctor_id: int,
    date: str,
    db: Session = Depends(get_db),
):
    from datetime import datetime
    agent = SchedulingAgent(db)
    target = datetime.strptime(date, "%Y-%m-%d")
    return {"slots": agent.suggest_best_slot(doctor_id, target)}


# ─── Monitoring Agent ────────────────────────────────────────
@app.get("/agents/monitoring")
def run_monitoring_agent(db: Session = Depends(get_db)):
    agent = MonitoringAgent(db)
    return agent.run()


# ─── Predictive Agent ────────────────────────────────────────
@app.get("/agents/predictions")
def run_predictive_agent(db: Session = Depends(get_db)):
    agent = PredictiveAgent(db)
    return agent.run()


# ─── Recommendation Agent ────────────────────────────────────
@app.get("/agents/recommendations")
def run_recommendation_agent(db: Session = Depends(get_db)):
    agent = RecommendationAgent(db)
    return agent.run()


@app.get("/agents/recommendations/{doctor_id}")
def get_doctor_recommendations(doctor_id: int, db: Session = Depends(get_db)):
    agent = RecommendationAgent(db)
    return agent.get_doctor_recommendations(doctor_id)


# ─── Notification Agent ──────────────────────────────────────
@app.get("/agents/notifications")
def run_notification_agent(db: Session = Depends(get_db)):
    agent = NotificationAgent(db)
    return agent.run()


# ─── Help Agent ──────────────────────────────────────────────
class QuestionRequest(BaseModel):
    question: str


@app.post("/agents/help/ask")
def ask_help_agent(req: QuestionRequest, db: Session = Depends(get_db)):
    agent = HelpAgent(db)
    return agent.answer(req.question)


@app.get("/agents/help/faq")
def get_faq(db: Session = Depends(get_db)):
    agent = HelpAgent(db)
    return agent.run()


# ─── Registration Agent ──────────────────────────────────────
class ParseTextRequest(BaseModel):
    text: str


@app.post("/agents/registration/parse")
def registration_parse(req: ParseTextRequest, db: Session = Depends(get_db)):
    agent = RegistrationAgent(db)
    return agent.parse(req.text)


@app.get("/agents/registration/info")
def registration_info(db: Session = Depends(get_db)):
    agent = RegistrationAgent(db)
    return agent.run()


@app.post("/agents/registration/parse-image")
async def registration_parse_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """OCR a photo of an ID card / insurance card and extract patient fields."""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Fișierul nu este o imagine")
    data = await file.read()
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Imagine prea mare (max 10MB)")
    if len(data) < 100:
        raise HTTPException(status_code=400, detail="Imagine invalidă")
    agent = RegistrationAgent(db)
    return agent.parse_image(data)


# ─── Run all agents ──────────────────────────────────────────
@app.post("/agents/run-all")
def run_all_agents(db: Session = Depends(get_db)):
    results = {}
    agents = [
        ("resources", ResourceAllocationAgent),
        ("scheduling", SchedulingAgent),
        ("monitoring", MonitoringAgent),
        ("predictive", PredictiveAgent),
        ("recommendations", RecommendationAgent),
        ("notifications", NotificationAgent),
    ]
    for name, AgentClass in agents:
        try:
            agent = AgentClass(db)
            if name == "resources":
                agent.train()
            results[name] = agent.run()
        except Exception as e:
            results[name] = {"error": str(e)}
            logger.error(f"Agent {name} failed: {e}")

    return results
