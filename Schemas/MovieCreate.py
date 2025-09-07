from pydantic import BaseModel, Field
from typing import Optional

class MovieCreate(BaseModel):
    title: str
    language: Optional[str] = None
    duration_min: Optional[int] = Field(None, gt=0)

class MovieOut(MovieCreate):
    id: int
    class Config:
        orm_mode = True
