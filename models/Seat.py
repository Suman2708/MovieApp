from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Seat(Base):
    __tablename__ = "seats"
    id = Column(Integer, primary_key=True)
    row_id = Column(Integer, ForeignKey("hall_rows.id", ondelete="CASCADE"), nullable=False)
    seat_number = Column(String, nullable=False)

    row = relationship("HallRow", back_populates="seats")
    booking_seats = relationship("BookingSeat", backref="seat", cascade="all, delete-orphan")
