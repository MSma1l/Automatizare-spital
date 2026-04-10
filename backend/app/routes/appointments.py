from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/appointments", tags=["appointments"])


@router.get("/specialties")
def get_specialties(db: Session = Depends(get_db)):
    from app.models.doctor import Doctor
    specialties = db.query(Doctor.specialty).distinct().all()
    return [s[0] for s in specialties]
