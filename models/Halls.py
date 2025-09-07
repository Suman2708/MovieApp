from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base

class Hall(Base):
    __tablename__ = "halls"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    theater_id = Column(Integer, ForeignKey("theaters.id", ondelete="CASCADE"), nullable=False)

    # Relations
    theater = relationship("Theater", back_populates="halls")
    rows = relationship(
        "HallRow",
        back_populates="hall",
        cascade="all, delete-orphan",
        order_by="HallRow.row_number",
    )
    shows = relationship(
        "Show",
        back_populates="hall",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("theater_id", "name", name="uq_hall_name_per_theater"),
    )


class HallRow(Base):
    __tablename__ = "hall_rows"
    id = Column(Integer, primary_key=True)
    hall_id = Column(Integer, ForeignKey("halls.id", ondelete="CASCADE"), nullable=False)
    row_number = Column(Integer, nullable=False)  # 1-based row index
    seat_count = Column(Integer, nullable=False)

    # Relations
    hall = relationship("Hall", back_populates="rows")
    seats = relationship(
        "Seat",
        back_populates="row",
        cascade="all, delete-orphan",
        order_by="Seat.seat_number",
    )

    __table_args__ = (
        UniqueConstraint("hall_id", "row_number", name="uq_row_per_hall"),
    )
