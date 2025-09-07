from pydantic import BaseModel, Field
from typing import List

class HallRowSpec(BaseModel):
    row_number: int = Field(..., ge=1)
    seat_count: int = Field(..., ge=6, description="At least 6 seats per row")

class HallCreate(BaseModel):
    name: str
    theater_id: int
    rows: List[HallRowSpec]

class HallOut(BaseModel):
    id: int
    name: str
    theater_id: int
    rows: List[HallRowSpec]
    empty_seats: int
    booked_seats: int
    class Config:
        orm_mode = True
