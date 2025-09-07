from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from database import Base

class Theater(Base):
    __tablename__ = "theaters"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    city = Column(String, nullable=True)
    address = Column(String, nullable=True)

    halls = relationship("Hall", back_populates="theater", cascade="all, delete-orphan")
