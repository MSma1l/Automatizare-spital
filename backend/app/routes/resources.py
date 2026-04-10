from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.notification import Notification
from app.schemas import NotificationOut
from app.services.auth_service import get_current_user
from app.services.notification_service import mark_as_read, mark_all_as_read

router = APIRouter(prefix="/api", tags=["common"])


@router.get("/notifications")
def get_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    unread_only: bool = False,
):
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    if unread_only:
        query = query.filter(Notification.is_read == False)

    notifications = query.order_by(Notification.created_at.desc()).limit(50).all()
    return [NotificationOut.model_validate(n).model_dump() for n in notifications]


@router.put("/notifications/{notification_id}/read")
def read_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if mark_as_read(db, notification_id, current_user.id):
        return {"message": "Notificare citită"}
    raise HTTPException(status_code=404, detail="Notificarea nu a fost găsită")


@router.put("/notifications/read-all")
def read_all_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count = mark_all_as_read(db, current_user.id)
    return {"message": f"{count} notificări marcate ca citite"}
