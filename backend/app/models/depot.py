import uuid
from sqlalchemy import String, Numeric, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Depot(Base):
    __tablename__ = "depots"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    lat: Mapped[float] = mapped_column(Numeric, nullable=False)
    lng: Mapped[float] = mapped_column(Numeric, nullable=False)
    region: Mapped[str | None] = mapped_column(String(100), nullable=True)
