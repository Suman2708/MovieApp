from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Movie
from Schemas.MovieCreate import MovieCreate, MovieOut

router = APIRouter()

@router.post("/", response_model=MovieOut)
def create_movie(payload: MovieCreate, db: Session = Depends(get_db)):
    m = Movie(**payload.dict())
    db.add(m)
    try:
        db.commit()
    except:
        db.rollback()
        raise HTTPException(409, "Movie with this title already exists")
    db.refresh(m)
    return m

@router.get("/", response_model=List[MovieOut])
def list_movies(db: Session = Depends(get_db)):
    return db.query(Movie).all()

@router.get("/{movie_id}", response_model=MovieOut)
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    m = db.get(Movie, movie_id)
    if not m:
        raise HTTPException(404, "Movie not found")
    return m

@router.delete("/{movie_id}")
def delete_movie(movie_id: int, db: Session = Depends(get_db)):
    m = db.get(Movie, movie_id)
    if not m:
        raise HTTPException(404, "Movie not found")
    db.delete(m)
    db.commit()
    return {"status": "deleted"}
