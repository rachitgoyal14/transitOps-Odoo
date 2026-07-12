import uuid
import enum
from datetime import datetime, date
from sqlalchemy import String, Numeric, Date, Enum as SAEnum, DateTime, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DriverStatus(str, enum.Enum):
    available = "available"
    on_trip = "on_trip"
    off_duty = "off_duty"
    suspended = "suspended"


class Driver(Base):
    __tablename__ = "drivers"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    license_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    license_category: Mapped[str] = mapped_column(String(10), nullable=False)
    license_expiry: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    contact_number: Mapped[str] = mapped_column(String(20), nullable=False)
    safety_score: Mapped[float] = mapped_column(Numeric(3, 1), default=10.0)
    status: Mapped[DriverStatus] = mapped_column(
        SAEnum(DriverStatus, name="driver_status", create_constraint=True),
        default=DriverStatus.available,
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
