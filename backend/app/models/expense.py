import uuid
import enum
from datetime import datetime, date
from sqlalchemy import String, Numeric, Text, Date, Enum as SAEnum, ForeignKey, DateTime, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ExpenseCategory(str, enum.Enum):
    toll = "toll"
    parking = "parking"
    repair = "repair"
    insurance = "insurance"
    other = "other"


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("vehicles.id"), nullable=False, index=True)
    trip_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("trips.id"), nullable=True)
    category: Mapped[ExpenseCategory] = mapped_column(
        SAEnum(ExpenseCategory, name="expense_category", create_constraint=True),
        nullable=False,
    )
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False, server_default=func.now())
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
