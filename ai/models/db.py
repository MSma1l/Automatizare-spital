"""Simplified DB models for the AI service (read-only access to main DB)."""
import os
import enum
from datetime import datetime

from sqlalchemy import (
    create_engine, Column, Integer, String, Text, Boolean,
    DateTime, Date, Time, ForeignKey, Enum, JSON, Float,
)
from sqlalchemy.orm import sessionmaker, DeclarativeBase, relationship

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://hospital_user:hospital_pass@localhost:5432/hospital_db",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    DOCTOR = "doctor"
    PATIENT = "patient"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255))
    role = Column(Enum(UserRole))
    is_active = Column(Boolean, default=True)


class Doctor(Base):
    __tablename__ = "doctors"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    first_name = Column(String(100))
    last_name = Column(String(100))
    specialty = Column(String(100))


class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    first_name = Column(String(100))
    last_name = Column(String(100))
    birth_date = Column(Date)


class AppointmentStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    patient_id = Column(Integer, ForeignKey("patients.id"))
    date_time = Column(DateTime)
    duration_minutes = Column(Integer, default=30)
    status = Column(Enum(AppointmentStatus))
    type = Column(String(50))
    notes = Column(Text)
    created_at = Column(DateTime)


class BedStatus(str, enum.Enum):
    FREE = "free"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"
    RESERVED = "reserved"


class Bed(Base):
    __tablename__ = "beds"
    id = Column(Integer, primary_key=True)
    room_number = Column(String(20))
    ward = Column(String(100))
    status = Column(Enum(BedStatus))
    patient_id = Column(Integer)
    admitted_at = Column(DateTime)


class Resource(Base):
    __tablename__ = "resources"
    id = Column(Integer, primary_key=True)
    name = Column(String(200))
    type = Column(String(50))
    quantity = Column(Integer)
    min_quantity = Column(Integer)
    location = Column(String(200))
    status = Column(String(50))


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(200))
    message = Column(Text)
    type = Column(String(50))
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class AgentLog(Base):
    __tablename__ = "agent_logs"
    id = Column(Integer, primary_key=True)
    agent_name = Column(String(100))
    action = Column(String(200))
    data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


class AgentRecommendation(Base):
    __tablename__ = "agent_recommendations"
    id = Column(Integer, primary_key=True)
    agent_name = Column(String(100))
    target_user_id = Column(Integer, ForeignKey("users.id"))
    recommendation = Column(Text)
    priority = Column(String(20))
    is_read = Column(Boolean, default=False)
    data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
