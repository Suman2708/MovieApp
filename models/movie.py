from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from database import Base

class Movie(Base):
    __tablename__ = "movies"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False, unique=True)
    language = Column(String, nullable=True)
    duration_min = Column(Integer, nullable=True)

    shows = relationship("Show", back_populates="movie", cascade="all, delete-orphan")
