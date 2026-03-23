from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    DateTime,
    ForeignKey,
    Numeric,
    Boolean,
    Enum,
)
from sqlalchemy.orm import relationship
from db.base import Base
from enum import Enum as PyEnum


class Language(PyEnum):
    EN = "EN"
    RU = "RU"
    UA = "UA"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, index=True)
    username = Column(String, nullable=True)
    reg_date = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    is_admin = Column(Boolean, default=False, nullable=False)
    is_banned = Column(Boolean, default=False, nullable=False)

    referred_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    referral_count = Column(Integer, default=0)
    active_referral_count = Column(Integer, default=0)
    balance = Column(Numeric(18, 8), default=0)
    total_earned = Column(Numeric(18, 8), default=0)
    referral_commission = Column(Numeric(10, 2), default=0.1)
    default_ton_wallet = Column(String, nullable=True)

    language = Column(Enum(Language), default=Language.EN)

    orders = relationship("Order", back_populates="user")
    sell_star_orders = relationship("SellStarOrder", back_populates="user")
    referrals = relationship("User", backref="referrer", remote_side=[id])
    withdrawals = relationship("Withdrawal", back_populates="user")
