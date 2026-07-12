import uuid
from decimal import Decimal
from datetime import datetime
from sqlalchemy import String, Numeric, DateTime, Text, ForeignKey, func, Enum as PgEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.enums import TripStatus

class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=False, index=True)
    driver_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("drivers.id"), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(200), nullable=False)
    destination: Mapped[str] = mapped_column(String(200), nullable=False)
    planned_distance_km: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    actual_distance_km: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    cargo_weight_kg: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    revenue: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.0"), nullable=False)
    status: Mapped[TripStatus] = mapped_column(
        PgEnum(TripStatus, name="trip_status", create_type=False),
        nullable=False,
        default=TripStatus.draft
    )
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )

    vehicle = relationship("Vehicle")
    driver = relationship("Driver")
    creator = relationship("User")
