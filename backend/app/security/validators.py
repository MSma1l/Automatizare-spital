import re
import os
from fastapi import UploadFile, HTTPException, status
from app.config import settings


def validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    pattern = r'^\+?[\d\s\-()]{7,20}$'
    return bool(re.match(pattern, phone))


def validate_password_strength(password: str) -> tuple[bool, str]:
    if len(password) < 6:
        return False, "Parola trebuie să aibă minim 6 caractere"
    return True, ""


async def validate_upload_file(file: UploadFile, allowed_types: set | None = None) -> None:
    if allowed_types is None:
        allowed_types = settings.ALLOWED_EXTENSIONS

    ext = file.filename.rsplit('.', 1)[-1].lower() if file.filename else ''
    if ext not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tip de fișier nepermis: .{ext}"
        )

    content = await file.read()
    await file.seek(0)

    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fișierul depășește dimensiunea maximă permisă (5MB)"
        )

    # Validate image magic bytes
    if ext in settings.ALLOWED_IMAGE_EXTENSIONS:
        image_signatures = {
            b'\xff\xd8\xff': 'jpg',
            b'\x89PNG': 'png',
            b'GIF87a': 'gif',
            b'GIF89a': 'gif',
        }
        is_valid_image = any(content.startswith(sig) for sig in image_signatures)
        if not is_valid_image:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Fișierul nu este o imagine validă"
            )
