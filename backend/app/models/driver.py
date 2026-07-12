import uuid
from decimal import Decimal
from datetime import date, datetime
from sqlalchemy import String, Numeric, Date, DateTime, func, Enum as PgEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.models.enums import DriverStatus

class Driver(Base):
    __tablename__ = "drivers"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    license_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    license_category: Mapped[str] = mapped_column(String(10), nullable=False)
    license_expiry: Mapped[date] = mapped_column(Date, nullable=False)
    contact_number: Mapped[str] = mapped_column(String(20), nullable=False)
    safety_score: Mapped[Decimal] = mapped_column(Numeric(3, 1), default=Decimal("10.0"), nullable=False)
    status: Mapped[DriverStatus] = mapped_column(
        PgEnum(DriverStatus, name="driver_status", create_type=False),
        nullable=False,
        default=DriverStatus.available
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )
