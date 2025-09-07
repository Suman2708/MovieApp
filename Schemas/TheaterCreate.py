from pydantic import BaseModel
from typing import Optional

class TheaterCreate(BaseModel):
    name: str
    city: Optional[str] = None
    address: Optional[str] = None

class TheaterOut(TheaterCreate):
    id: int
    class Config:
        orm_mode = True
