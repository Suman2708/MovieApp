from sqlalchemy.orm import Session
from models import Show, Seat, HallRow,BookingSeat

def show_layout_status(show_id: int, db: Session):
    """
    Returns seat layout for a specific show.
    Each seat dict contains:
        - seat_id
        - seat_number
        - row_number
        - is_booked
        - is_aisle
    """
    # Join Seat → HallRow
    seats = db.query(Seat).join(HallRow).all()

    # Get booked seat IDs for this show
    booked_seat_ids = set(
        s.seat_id for s in db.query(BookingSeat).filter(BookingSeat.show_id == show_id).all()
    )

    seats_status = []
    for seat in seats:
        seats_status.append({
            "seat_id": seat.id,
            "seat_number": seat.seat_number,
            "row_number": seat.row.row_number if seat.row else None,
            "is_aisle": getattr(seat, "is_aisle", False),
            "is_booked": seat.id in booked_seat_ids,
        })
    return seats_status


def find_contiguous_block(row_seats: list, group_size: int):
    """
    Find a contiguous block of empty seats in a given row.
    `row_seats` is a list of seat dicts (from show_layout_status for one row).
    """
    block = []
    for seat in row_seats:
        if not seat["is_booked"]:
            block.append(seat["seat_id"])
            if len(block) == group_size:
                return block
        else:
            block = []
    return None


def create_or_refresh_seats_for_row(db: Session, row: HallRow):
    """
    Ensure seats exist for a row. If not, create them.
    """
    from models import Seat

    existing_seats = db.query(Seat).filter(Seat.row_id == row.id).all()
    existing_count = len(existing_seats)

    if existing_count < row.seat_count:
        for i in range(existing_count + 1, row.seat_count + 1):
            seat = Seat(row_id=row.id, seat_number=i, is_aisle=False, is_booked=False)
            db.add(seat)
        db.commit()


def get_show_by_keys(db: Session, movie_id: int, hall_id: int, start_time):
    """
    Fetch show by unique keys: movie, hall, and start_time.
    """
    show = (
        db.query(Show)
        .filter(Show.movie_id == movie_id)
        .filter(Show.hall_id == hall_id)
        .filter(Show.start_time == start_time)
        .first()
    )
    if not show:
        from fastapi import HTTPException
        raise HTTPException(404, "Show not found")
    return show
