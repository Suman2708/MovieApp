from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

class BookingRequest(BaseModel):
    movie_id: int
    hall_id: int
    start_time: datetime
    group_size: int = Field(..., ge=1)
    group_name: Optional[str] = None

class BookingOut(BaseModel):
    booking_id: int
    show_id: int
    seat_ids: List[int]
    total_price: int

class SuggestionOut(BaseModel):
    show_id: int
    start_time: datetime
    hall_id: int
    hall_name: str
    contiguous_block: List[int]  # seat_ids
    class Config:
        from_attributes = True
