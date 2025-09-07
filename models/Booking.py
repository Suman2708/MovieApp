from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True)
    show_id = Column(Integer, ForeignKey("shows.id", ondelete="CASCADE"), nullable=False)
    group_name = Column(String, nullable=True)
    total_price = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    show = relationship("Show", back_populates="bookings")
    seats = relationship("BookingSeat", back_populates="booking", cascade="all, delete-orphan")


class BookingSeat(Base):
    __tablename__ = "booking_seats"
    id = Column(Integer, primary_key=True)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False)
    show_id = Column(Integer, ForeignKey("shows.id", ondelete="CASCADE"), nullable=False)
    seat_id = Column(Integer, ForeignKey("seats.id", ondelete="CASCADE"), nullable=False)

    booking = relationship("Booking", back_populates="seats")
    __table_args__ = (UniqueConstraint("show_id", "seat_id", name="uq_seat_once_per_show"),)
