import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from concierge_bot.db.base import Base


class Hotel(Base):
    __tablename__ = "hotels"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    admin_chat_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    forum_chat_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    bot_token: Mapped[str] = mapped_column(String(255))
    max_bot_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=true())
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    services: Mapped[list["Service"]] = relationship(back_populates="hotel")
    guests: Mapped[list["Guest"]] = relationship(back_populates="hotel")


class Service(Base):
    __tablename__ = "services"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    hotel_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("hotels.id"))
    name: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), server_default=text("'USD'"))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=true())
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    hotel: Mapped["Hotel"] = relationship(back_populates="services")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="service")


class Guest(Base):
    __tablename__ = "guests"
    __table_args__ = (UniqueConstraint("telegram_user_id", "hotel_id"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger)
    hotel_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("hotels.id"))
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    language_code: Mapped[str] = mapped_column(String(16), server_default=text("'en'"))
    forum_topic_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    hotel: Mapped["Hotel"] = relationship(back_populates="guests")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="guest")


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    guest_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("guests.id"))
    service_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("services.id"))
    status: Mapped[str] = mapped_column(String(50), server_default=text("'pending'"))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    guest: Mapped["Guest"] = relationship(back_populates="bookings")
    service: Mapped["Service"] = relationship(back_populates="bookings")
