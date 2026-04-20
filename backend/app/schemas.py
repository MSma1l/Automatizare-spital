from datetime import datetime, date, time
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# ─── Auth ────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str
    user_id: int


class RefreshRequest(BaseModel):
    refresh_token: str


# ─── User ────────────────────────────────────────────────────────────
class UserOut(BaseModel):
    id: int
    email: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Doctor ──────────────────────────────────────────────────────────
class DoctorScheduleIn(BaseModel):
    day_of_week: int = Field(ge=0, le=6)
    start_time: time
    end_time: time


class DoctorScheduleOut(BaseModel):
    id: int
    day_of_week: int
    start_time: time
    end_time: time

    class Config:
        from_attributes = True


class DoctorCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    specialty: str = Field(min_length=1, max_length=100)
    experience_years: int = Field(ge=0, default=0)
    bio: Optional[str] = None
    phone: Optional[str] = None
    cabinet: Optional[str] = None
    schedules: list[DoctorScheduleIn] = []


class DoctorUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    specialty: Optional[str] = None
    experience_years: Optional[int] = None
    bio: Optional[str] = None
    phone: Optional[str] = None
    cabinet: Optional[str] = None
    schedules: Optional[list[DoctorScheduleIn]] = None


class DoctorOut(BaseModel):
    id: int
    user_id: int
    first_name: str
    last_name: str
    specialty: str
    experience_years: int
    bio: Optional[str]
    photo_url: Optional[str]
    phone: Optional[str]
    cabinet: Optional[str]
    schedules: list[DoctorScheduleOut] = []
    avg_rating: Optional[float] = None
    review_count: int = 0
    is_active: bool = True

    class Config:
        from_attributes = True


# ─── Patient ─────────────────────────────────────────────────────────
class PatientCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    birth_date: Optional[date] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    insurance_number: Optional[str] = None


class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    birth_date: Optional[date] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    insurance_number: Optional[str] = None


class PatientOut(BaseModel):
    id: int
    user_id: int
    first_name: str
    last_name: str
    birth_date: Optional[date]
    gender: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    insurance_number: Optional[str]
    photo_url: Optional[str] = None
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Appointment ─────────────────────────────────────────────────────
class AppointmentCreate(BaseModel):
    doctor_id: int
    date_time: datetime
    type: str = "consultation"
    notes: Optional[str] = None
    duration_minutes: int = Field(default=30, ge=15, le=120)


class AppointmentUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    date_time: Optional[datetime] = None


class AppointmentOut(BaseModel):
    id: int
    doctor_id: int
    patient_id: int
    date_time: datetime
    duration_minutes: int
    status: str
    type: str
    notes: Optional[str]
    created_at: datetime
    doctor_name: Optional[str] = None
    patient_name: Optional[str] = None

    class Config:
        from_attributes = True


# ─── Resource ────────────────────────────────────────────────────────
class ResourceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    type: str
    quantity: int = Field(ge=0, default=0)
    min_quantity: int = Field(ge=0, default=0)
    location: Optional[str] = None
    status: str = "available"
    description: Optional[str] = None


class ResourceUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    quantity: Optional[int] = None
    min_quantity: Optional[int] = None
    location: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None


class ResourceOut(BaseModel):
    id: int
    name: str
    type: str
    quantity: int
    min_quantity: int
    location: Optional[str]
    status: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Bed ─────────────────────────────────────────────────────────────
class BedCreate(BaseModel):
    room_number: str = Field(min_length=1, max_length=20)
    ward: str = Field(min_length=1, max_length=100)
    status: str = "free"


class BedUpdate(BaseModel):
    room_number: Optional[str] = None
    ward: Optional[str] = None
    status: Optional[str] = None
    patient_id: Optional[int] = None


class BedOut(BaseModel):
    id: int
    room_number: str
    ward: str
    status: str
    patient_id: Optional[int]
    admitted_at: Optional[datetime]
    patient_name: Optional[str] = None

    class Config:
        from_attributes = True


# ─── Message / Chat ──────────────────────────────────────────────────
class MessageOut(BaseModel):
    id: int
    conversation_id: int
    sender_id: int
    content: Optional[str]
    file_url: Optional[str]
    file_type: Optional[str]
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationOut(BaseModel):
    id: int
    doctor_id: int
    patient_id: int
    doctor_name: Optional[str] = None
    patient_name: Optional[str] = None
    last_message: Optional[str] = None
    unread_count: int = 0
    updated_at: datetime

    class Config:
        from_attributes = True


# ─── Notification ────────────────────────────────────────────────────
class NotificationOut(BaseModel):
    id: int
    title: str
    message: str
    type: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Review ──────────────────────────────────────────────────────────
class ReviewCreate(BaseModel):
    doctor_id: int
    appointment_id: Optional[int] = None
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None


class ReviewOut(BaseModel):
    id: int
    doctor_id: int
    patient_id: int
    rating: int
    comment: Optional[str]
    created_at: datetime
    patient_name: Optional[str] = None

    class Config:
        from_attributes = True


# ─── Dashboard Stats ─────────────────────────────────────────────────
class AdminStats(BaseModel):
    total_beds: int
    occupied_beds: int
    total_doctors: int
    active_doctors: int
    total_patients: int
    appointments_today: int
    low_stock_resources: int


class DoctorStats(BaseModel):
    appointments_today: int
    total_patients: int
    unread_messages: int
    pending_appointments: int


class PatientStats(BaseModel):
    next_appointment: Optional[AppointmentOut] = None
    unread_messages: int
    total_appointments: int
