import uuid
import enum
from datetime import datetime
from sqlalchemy import String, Numeric, Text, Enum as SAEnum, ForeignKey, DateTime, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TripStatus(str, enum.Enum):
    draft = "draft"
    dispatched = "dispatched"
    completed = "completed"
    cancelled = "cancelled"


class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("vehicles.id"), nullable=False, index=True)
    driver_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("drivers.id"), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(200), nullable=False)
    destination: Mapped[str] = mapped_column(String(200), nullable=False)
    planned_distance_km: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    actual_distance_km: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    cargo_weight_kg: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    revenue: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    status: Mapped[TripStatus] = mapped_column(
        SAEnum(TripStatus, name="trip_status", create_constraint=True),
        default=TripStatus.draft,
        nullable=False,
        index=True,
    )
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
