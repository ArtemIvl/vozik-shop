from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from db.base import Base


class SellStarOrderStatus(PyEnum):
    PENDING = "PENDING"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class SellStarOrder(Base):
    __tablename__ = "sell_star_orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    stars_amount = Column(Integer, nullable=False)
    payout_ton = Column(Numeric(18, 8), nullable=False)
    status = Column(
        Enum(SellStarOrderStatus), default=SellStarOrderStatus.PENDING, nullable=False
    )

    telegram_payment_charge_id = Column(String, nullable=True, unique=True)
    provider_payment_charge_id = Column(String, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    paid_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="sell_star_orders")
