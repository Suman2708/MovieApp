from pydantic import BaseModel
from datetime import datetime

class AnalyticsRequest(BaseModel):
    movie_id: int
    start: datetime
    end: datetime

class AnalyticsOut(BaseModel):
    movie_id: int
    tickets_sold: int
    gmv: int
