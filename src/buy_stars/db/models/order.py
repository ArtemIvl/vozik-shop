from datetime import datetime, timezone
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Enum, Numeric, String
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from db.base import Base

class OrderType(PyEnum):
    STARS = "stars"
    PREMIUM = "premium"

class PaymentType(PyEnum):
    TON = "TON"
    USDT = "USDT"

class OrderStatus(PyEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    PAID = "PAID"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    to_username = Column(String, nullable=False)

    stars_amount = Column(Integer, nullable=True)
    premium_months = Column(Integer, nullable=True)

    price_ton = Column(Numeric(18, 8), nullable=True)
    price_usdt = Column(Numeric(18, 8), nullable=True)

    payment_type = Column(Enum(PaymentType), nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    order_type = Column(Enum(OrderType), default=OrderType.STARS)

    memo = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="orders")