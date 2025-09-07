# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session
# from typing import List
# from datetime import datetime

# from database import get_db
# from models import Booking, BookingSeat, Show
# from Schemas.BookingRequest import BookingRequest, BookingOut
# from utils.utils import get_show_by_keys, show_layout_status, find_contiguous_block

# router = APIRouter()

# @router.post("/", response_model=BookingOut)
# def create_booking(req: BookingRequest, db: Session = Depends(get_db)):
#     show = get_show_by_keys(db, req.movie_id, req.hall_id, req.start_time)

#     seats_status = show_layout_status(show.id, db)
#     by_row = {}
#     for st in seats_status:
#         by_row.setdefault(st['row_number'], []).append(st)

#     chosen_block = None
#     for row_number in sorted(by_row.keys()):
#         block = find_contiguous_block(by_row[row_number], req.group_size)
#         if block:
#             chosen_block = block
#             break

#     if not chosen_block:
#         raise HTTPException(409, "Contiguous seats not available")

#     booking = Booking(show_id=show.id, group_name=req.group_name or "group")
#     db.add(booking)
#     db.flush()
#     for seat_id in chosen_block:
#         bs = BookingSeat(booking_id=booking.id, show_id=show.id, seat_id=seat_id)
#         db.add(bs)

#     booking.total_price = show.price * len(chosen_block)
#     db.commit()
#     db.refresh(booking)

#     return BookingOut(booking_id=booking.id, show_id=show.id, seat_ids=chosen_block, total_price=booking.total_price)



from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from models import Booking, BookingSeat, Show, Hall
from Schemas.BookingRequest import BookingRequest, BookingOut, SuggestionOut
from database import get_db
from utils.utils import show_layout_status, find_contiguous_block, get_show_by_keys

router = APIRouter()

@router.post("/", response_model=dict)
def create_booking(req: BookingRequest, db: Session = Depends(get_db)):
    show = get_show_by_keys(db, req.movie_id, req.hall_id, req.start_time)

    # check contiguous block
    seats_status = show_layout_status(show.id, db)


    by_row = {}
    for st in seats_status:
        by_row.setdefault(st["row_number"], []).append(st)

    chosen_block = None
    for row_number in sorted(by_row.keys()):
        block = find_contiguous_block(by_row[row_number], req.group_size)
        if block:
            chosen_block = block
            break

    if chosen_block:
        # create booking
        booking = Booking(show_id=show.id, group_name=req.group_name or "group")
        db.add(booking)
        db.flush()

        for seat_id in chosen_block:
            db.add(BookingSeat(booking_id=booking.id, show_id=show.id, seat_id=seat_id))

        booking.total_price = show.price * len(chosen_block)
        db.commit()
        db.refresh(booking)

        # updated stats after booking
        # After committing the booking
        updated_stats = show_layout_status(show.id, db)

    # Count empty and booked seats
        empty = sum(1 for s in updated_stats if not s["is_booked"])
        booked = sum(1 for s in updated_stats if s["is_booked"])

    # Return response
        return {
        "status": "success",
        "booking": BookingOut(
            booking_id=booking.id,
            show_id=show.id,
            seat_ids=chosen_block,
            total_price=booking.total_price,
        ),
        "seat_stats": {  # Correct dictionary syntax
            "empty": empty,
            "booked": booked
        }
    }


    # ... rest of your alternative shows logic unchanged ...


    # no contiguous block → look for alternative shows
    alternatives = (
        db.query(Show)
        .filter(Show.movie_id == req.movie_id)
        .filter(Show.id != show.id)
        .order_by(Show.start_time)
        .all()
    )

    suggestions: List[SuggestionOut] = []
    for alt in alternatives:
        seats_status = show_layout_status(alt.id, db)
        by_row = {}
        for st in seats_status:
            by_row.setdefault(st["row_number"], []).append(st)

        alt_block = None
        for row_number in sorted(by_row.keys()):
            block = find_contiguous_block(by_row[row_number], req.group_size)
            if block:
                alt_block = block
                break

        if alt_block:
            hall = db.get(Hall, alt.hall_id)
            suggestions.append(
                SuggestionOut(
                    show_id=alt.id,
                    hall_id=alt.hall_id,
                    hall_name=hall.name if hall else "Unknown Hall",
                    start_time=alt.start_time,
                    contiguous_block=alt_block,
                )
            )

    if not suggestions:
        raise HTTPException(409, "No contiguous seats available in any show")

    return {
        "status": "failed",
        "reason": "No contiguous seats in selected show",
        "alternatives": suggestions,
    }


@router.get("/shows/{show_id}/layout")
def get_show_layout(show_id: int, db: Session = Depends(get_db)):
    return show_layout_status(show_id, db)
