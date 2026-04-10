import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, Enum, DateTime
from app.database import Base


class ResourceType(str, enum.Enum):
    EQUIPMENT = "equipment"
    MEDICATION = "medication"
    ROOM = "room"
    SUPPLY = "supply"


class ResourceStatus(str, enum.Enum):
    AVAILABLE = "available"
    IN_USE = "in_use"
    MAINTENANCE = "maintenance"
    OUT_OF_STOCK = "out_of_stock"


class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    type = Column(Enum(ResourceType), nullable=False)
    quantity = Column(Integer, default=0)
    min_quantity = Column(Integer, default=0)
    location = Column(String(200), nullable=True)
    status = Column(Enum(ResourceStatus), default=ResourceStatus.AVAILABLE)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
