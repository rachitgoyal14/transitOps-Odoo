import uuid
from datetime import datetime
from sqlalchemy import Boolean, Text, ForeignKey, DateTime, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DispatchSuggestion(Base):
    __tablename__ = "dispatch_suggestions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trip_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("trips.id"), nullable=True)
    suggested_vehicle_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("vehicles.id"), nullable=True)
    suggested_driver_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("drivers.id"), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    accepted: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
