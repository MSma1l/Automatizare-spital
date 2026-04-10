from fastapi import APIRouter, Depends
from app.models.user import User
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/video", tags=["video"])


@router.get("/token")
def get_video_token(current_user: User = Depends(get_current_user)):
    """Return user info for WebRTC signaling. Actual video logic is in WebSocket."""
    return {
        "user_id": current_user.id,
        "role": current_user.role.value,
    }
