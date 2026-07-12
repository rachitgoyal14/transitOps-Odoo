import uuid
import enum
from datetime import datetime, date
from sqlalchemy import String, Numeric, Text, Date, Enum as SAEnum, ForeignKey, DateTime, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MaintenanceStatus(str, enum.Enum):
    open = "open"
    closed = "closed"


class MaintenanceLog(Base):
    __tablename__ = "maintenance_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("vehicles.id"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cost: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    odometer_at_service: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    status: Mapped[MaintenanceStatus] = mapped_column(
        SAEnum(MaintenanceStatus, name="maintenance_status", create_constraint=True),
        default=MaintenanceStatus.open,
        nullable=False,
        index=True,
    )
    scheduled_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    completed_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
