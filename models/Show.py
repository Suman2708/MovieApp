from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base

class Show(Base):
    __tablename__ = "shows"
    id = Column(Integer, primary_key=True)
    movie_id = Column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
    hall_id = Column(Integer, ForeignKey("halls.id", ondelete="CASCADE"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    price = Column(Integer, nullable=False)

    # Relations
    movie = relationship("Movie", back_populates="shows")
    hall = relationship("Hall", back_populates="shows")
    bookings = relationship("Booking", back_populates="show", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("hall_id", "start_time", name="uq_show_per_hall_time"),)
