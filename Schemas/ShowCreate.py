from pydantic import BaseModel, Field
from datetime import datetime

class ShowCreate(BaseModel):
    movie_id: int
    hall_id: int
    start_time: datetime
    price: int = Field(..., ge=0)

class ShowOut(ShowCreate):
    id: int
    class Config:
        orm_mode = True

class SeatStatus(BaseModel):
    seat_id: int
    row_number: int
    seat_number: int
    is_aisle: bool
    booked: bool
