import uuid
import enum
from datetime import datetime
from sqlalchemy import String, Numeric, Enum as SAEnum, DateTime, ForeignKey, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class VehicleStatus(str, enum.Enum):
    available = "available"
    on_trip = "on_trip"
    in_shop = "in_shop"
    retired = "retired"


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    registration_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    max_load_kg: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    odometer_km: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0)
    acquisition_cost: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    status: Mapped[VehicleStatus] = mapped_column(
        SAEnum(VehicleStatus, name="vehicle_status", create_constraint=True),
        default=VehicleStatus.available,
        nullable=False,
        index=True,
    )
    region: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    lat: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    lng: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    depot_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("depots.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
