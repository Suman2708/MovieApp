from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from database import get_db
from models import Show, Movie, Hall
from Schemas.ShowCreate import ShowCreate, ShowOut

router = APIRouter()

@router.post("/", response_model=ShowOut)
def create_show(payload: ShowCreate, db: Session = Depends(get_db)):
    if not db.get(Movie, payload.movie_id):
        raise HTTPException(404, "Movie not found")
    if not db.get(Hall, payload.hall_id):
        raise HTTPException(404, "Hall not found")
    show = Show(**payload.dict())
    db.add(show)
    try:
        db.commit()
    except:
        db.rollback()
        raise HTTPException(409, "A show already exists in this hall at this time")
    db.refresh(show)
    return show

@router.get("/", response_model=List[ShowOut])
def list_shows(movie_id: Optional[int] = None, hall_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(Show)
    if movie_id:
        query = query.filter(Show.movie_id == movie_id)
    if hall_id:
        query = query.filter(Show.hall_id == hall_id)
    return query.order_by(Show.start_time).all()
