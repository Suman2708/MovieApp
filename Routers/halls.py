from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Hall, HallRow, Theater, Show
from Schemas.HallCreate import HallCreate, HallOut, HallRowSpec
from utils.utils import create_or_refresh_seats_for_row, show_layout_status

router = APIRouter()

def calculate_seat_stats_for_show(show: Show, db: Session):
    """
    Returns empty and booked seats for a given show
    """
    seats_status = show_layout_status(show.id, db)
    total_seats = len(seats_status)
    booked = sum(1 for s in seats_status if s["is_booked"])
    empty = total_seats - booked
    return empty, booked


def calculate_seat_stats_for_hall(hall: Hall, db: Session):
    """
    Returns total empty and booked seats across all shows in the hall
    """
    total_empty = 0
    total_booked = 0
    for show in hall.shows:
        empty, booked = calculate_seat_stats_for_show(show, db)
        total_empty += empty
        total_booked += booked
    return total_empty, total_booked


# @router.post("/", response_model=HallOut)
# def create_hall(payload: HallCreate, db: Session = Depends(get_db)):
#     theater = db.get(Theater, payload.theater_id)
#     if not theater:
#         raise HTTPException(404, "Theater not found")

#     hall = Hall(name=payload.name, theater_id=payload.theater_id)
#     db.add(hall)
#     db.flush()

#     for r in payload.rows:
#         row = HallRow(hall_id=hall.id, row_number=r.row_number, seat_count=r.seat_count)
#         db.add(row)
#         db.flush()
#         create_or_refresh_seats_for_row(db, row)

#     db.commit()
#     db.refresh(hall)
#     out_rows = [HallRowSpec(row_number=r.row_number, seat_count=r.seat_count) for r in hall.rows]
#     empty, booked = calculate_seat_stats(hall, db)
#     return HallOut(
#         id=hall.id,
#         name=hall.name,
#         theater_id=hall.theater_id,
#         rows=out_rows,
#         empty_seats=empty,
#         booked_seats=booked,
#     )


@router.get("/")
def list_halls(db: Session = Depends(get_db)):
    halls = db.query(Hall).all()
    result = []
    for hall in halls:
        hall_data = {
            "id": hall.id,
            "name": hall.name,
            "theater_id": hall.theater_id,
            "shows": []
        }
        for sh in hall.shows:
            empty, booked = calculate_seat_stats_for_show(sh, db)
            hall_data["shows"].append({
                "show_id": sh.id,
                "movie_id": sh.movie_id,
                "start_time": sh.start_time,
                "price": sh.price,
                "empty_seats": empty,
                "booked_seats": booked
            })

        result.append(hall_data)
    return result


# @router.get("/{hall_id}", response_model=HallOut)
# def get_hall(hall_id: int, db: Session = Depends(get_db)):
#     hall = db.get(Hall, hall_id)
#     if not hall:
#         raise HTTPException(404, "Hall not found")
#     out_rows = [HallRowSpec(row_number=r.row_number, seat_count=r.seat_count) for r in hall.rows]
#     empty, booked = calculate_seat_stats(hall, db)
#     return HallOut(
#         id=hall.id,
#         name=hall.name,
#         theater_id=hall.theater_id,
#         rows=out_rows,
#         empty_seats=empty,
#         booked_seats=booked,
#     )


@router.delete("/{hall_id}")
def delete_hall(hall_id: int, db: Session = Depends(get_db)):
    hall = db.get(Hall, hall_id)
    if not hall:
        raise HTTPException(404, "Hall not found")
    db.delete(hall)
    db.commit()
    return {"status": "deleted"}





@router.post("/", response_model=HallOut)
def create_hall(payload: HallCreate, db: Session = Depends(get_db)):
    theater = db.get(Theater, payload.theater_id)
    if not theater:
        raise HTTPException(404, "Theater not found")

    hall = Hall(name=payload.name, theater_id=payload.theater_id)
    db.add(hall)
    db.flush()

    for r in payload.rows:
        row = HallRow(hall_id=hall.id, row_number=r.row_number, seat_count=r.seat_count)
        db.add(row)
        db.flush()
        create_or_refresh_seats_for_row(db, row)

    db.commit()
    db.refresh(hall)
    out_rows = [HallRowSpec(row_number=r.row_number, seat_count=r.seat_count) for r in hall.rows]

    # Calculate hall-level seat stats (sum of all shows)
    empty, booked = calculate_seat_stats_for_hall(hall, db)

    return HallOut(
        id=hall.id,
        name=hall.name,
        theater_id=hall.theater_id,
        rows=out_rows,
        empty_seats=empty,
        booked_seats=booked,
    )


@router.get("/{hall_id}", response_model=HallOut)
def get_hall(hall_id: int, db: Session = Depends(get_db)):
    hall = db.get(Hall, hall_id)
    if not hall:
        raise HTTPException(404, "Hall not found")
    out_rows = [HallRowSpec(row_number=r.row_number, seat_count=r.seat_count) for r in hall.rows]

    empty, booked = calculate_seat_stats_for_hall(hall, db)

    return HallOut(
        id=hall.id,
        name=hall.name,
        theater_id=hall.theater_id,
        rows=out_rows,
        empty_seats=empty,
        booked_seats=booked,
    )
