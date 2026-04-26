from sqlalchemy.orm import Session
from app.models.notification import Notification, NotificationType
from app.models.user import User, UserRole


def create_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    notif_type: NotificationType = NotificationType.INFO,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=notif_type,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def notify_role(
    db: Session,
    role: UserRole,
    title: str,
    message: str,
    notif_type: NotificationType = NotificationType.INFO,
) -> int:
    """Broadcast a notification to every active user with the given role."""
    targets = db.query(User).filter(User.role == role, User.is_active == True).all()
    for u in targets:
        n = Notification(
            user_id=u.id,
            title=title,
            message=message,
            type=notif_type,
        )
        db.add(n)
    db.commit()
    return len(targets)


def notify_admins(
    db: Session,
    title: str,
    message: str,
    notif_type: NotificationType = NotificationType.INFO,
) -> int:
    return notify_role(db, UserRole.ADMIN, title, message, notif_type)


def get_unread_count(db: Session, user_id: int) -> int:
    return db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == False,
    ).count()


def mark_as_read(db: Session, notification_id: int, user_id: int) -> bool:
    notif = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user_id,
    ).first()
    if notif:
        notif.is_read = True
        db.commit()
        return True
    return False


def mark_all_as_read(db: Session, user_id: int) -> int:
    count = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == False,
    ).update({"is_read": True})
    db.commit()
    return count
