from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Theater
from Schemas.TheaterCreate import TheaterCreate, TheaterOut

router = APIRouter()

@router.post("/", response_model=TheaterOut)
def create_theater(payload: TheaterCreate, db: Session = Depends(get_db)):
    th = Theater(name=payload.name, city=payload.city, address=payload.address)
    db.add(th)
    try:
        db.commit()
    except:
        db.rollback()
        raise HTTPException(409, "Theater with this name already exists")
    db.refresh(th)
    return th

@router.get("/", response_model=List[TheaterOut])
def list_theaters(db: Session = Depends(get_db)):
    return db.query(Theater).all()

@router.get("/{theater_id}", response_model=TheaterOut)
def get_theater(theater_id: int, db: Session = Depends(get_db)):
    th = db.get(Theater, theater_id)
    if not th:
        raise HTTPException(404, "Theater not found")
    return th

@router.delete("/{theater_id}")
def delete_theater(theater_id: int, db: Session = Depends(get_db)):
    th = db.get(Theater, theater_id)
    if not th:
        raise HTTPException(404, "Theater not found")
    db.delete(th)
    db.commit()
    return {"status": "deleted"}
