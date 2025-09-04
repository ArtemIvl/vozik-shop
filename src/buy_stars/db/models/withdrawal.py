from enum import Enum as PyEnum
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from db.base import Base


class WithdrawalStatus(PyEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Withdrawal(Base):
    __tablename__ = "withdrawals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ton_amount = Column(Numeric(18, 8), nullable=False)
    ton_address = Column(String, nullable=True, default=None)
    status = Column(
        Enum(WithdrawalStatus), default=WithdrawalStatus.PENDING, nullable=False
    )
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="withdrawals")
