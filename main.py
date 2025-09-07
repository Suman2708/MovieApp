# """
# Movie Ticket Booking APIs (Python + FastAPI + SQLAlchemy)
# --------------------------------------------------------
# Features implemented
# - Register theaters, halls, and per-hall seat layouts (rows with variable seat counts, min 6)
# - Register movies
# - Create shows (movie @ hall @ time) with price
# - CRUD for movies, theaters, halls, shows
# - Read hall layout WITH booked/empty status for a specific show
# - Group booking: seats are booked together (contiguous) in a row
# - If contiguous seats unavailable for chosen show, suggest alternate shows (same movie) with a contiguous block
# - Concurrency-safe booking via DB transaction and UNIQUE(seat_id, show_id) constraint
# - Bonus analytics: tickets sold & GMV for a movie in a period

# How to run
# - Install deps:  pip install fastapi uvicorn sqlalchemy pydantic-settings python-multipart
# - Run:          uvicorn app:app --reload
# - Docs:         Open http://127.0.0.1:8000/docs

# Notes
# - Uses SQLite by default (file movie.db). For production, switch to Postgres by setting DATABASE_URL env var.
# - Concurrency: relies on transactions and unique constraints. In high contention scenarios prefer Postgres.
# """

# from __future__ import annotations
# from datetime import datetime, timedelta
# from typing import List, Optional
# import os

# from fastapi import FastAPI, HTTPException, Depends, Body, Query
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel, Field, validator
# from sqlalchemy import (
#     Column, Integer, String, DateTime, ForeignKey, Boolean, UniqueConstraint, create_engine, select, func
# )
# from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session
# from sqlalchemy.exc import IntegrityError

# # -----------------------------
# # Database setup
# # -----------------------------
# # DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///movie.db")
# # connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
# # engine = create_engine(DATABASE_URL, echo=False, future=True, connect_args=connect_args)
# # SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
# # Base = declarative_base()

# # # -----------------------------
# # # Models
# # # -----------------------------
# # class Theater(Base):
# #     __tablename__ = "theaters"
# #     id = Column(Integer, primary_key=True)
# #     name = Column(String, nullable=False, unique=True)
# #     city = Column(String, nullable=True)
# #     address = Column(String, nullable=True)
# #     halls = relationship("Hall", back_populates="theater", cascade="all, delete-orphan")

# # class Hall(Base):
# #     __tablename__ = "halls"
# #     id = Column(Integer, primary_key=True)
# #     name = Column(String, nullable=False)
# #     theater_id = Column(Integer, ForeignKey("theaters.id", ondelete="CASCADE"), nullable=False)
# #     theater = relationship("Theater", back_populates="halls")
# #     rows = relationship("HallRow", back_populates="hall", cascade="all, delete-orphan", order_by="HallRow.row_number")
# #     shows = relationship("Show", back_populates="hall", cascade="all, delete-orphan")
# #     __table_args__ = (UniqueConstraint("theater_id", "name", name="uq_hall_name_per_theater"),)

# # class HallRow(Base):
# #     __tablename__ = "hall_rows"
# #     id = Column(Integer, primary_key=True)
# #     hall_id = Column(Integer, ForeignKey("halls.id", ondelete="CASCADE"), nullable=False)
# #     row_number = Column(Integer, nullable=False)  # 1-based row index
# #     seat_count = Column(Integer, nullable=False)  # >= 6
# #     hall = relationship("Hall", back_populates="rows")
# #     seats = relationship("Seat", back_populates="row", cascade="all, delete-orphan", order_by="Seat.seat_number")
# #     __table_args__ = (UniqueConstraint("hall_id", "row_number", name="uq_row_per_hall"),)

# # class Seat(Base):
# #     __tablename__ = "seats"
# #     id = Column(Integer, primary_key=True)
# #     row_id = Column(Integer, ForeignKey("hall_rows.id", ondelete="CASCADE"), nullable=False)
# #     seat_number = Column(Integer, nullable=False)  # 1..seat_count
# #     is_aisle = Column(Boolean, nullable=False, default=False)
# #     row = relationship("HallRow", back_populates="seats")
# #     __table_args__ = (UniqueConstraint("row_id", "seat_number", name="uq_seat_per_row"),)

# # class Movie(Base):
# #     __tablename__ = "movies"
# #     id = Column(Integer, primary_key=True)
# #     title = Column(String, nullable=False, unique=True)
# #     language = Column(String, nullable=True)
# #     duration_min = Column(Integer, nullable=True)
# #     shows = relationship("Show", back_populates="movie", cascade="all, delete-orphan")

# # class Show(Base):
# #     __tablename__ = "shows"
# #     id = Column(Integer, primary_key=True)
# #     movie_id = Column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
# #     hall_id = Column(Integer, ForeignKey("halls.id", ondelete="CASCADE"), nullable=False)
# #     start_time = Column(DateTime, nullable=False)
# #     price = Column(Integer, nullable=False)  # price per seat, in smallest currency unit if desired
# #     movie = relationship("Movie", back_populates="shows")
# #     hall = relationship("Hall", back_populates="shows")
# #     bookings = relationship("Booking", back_populates="show", cascade="all, delete-orphan")
# #     __table_args__ = (UniqueConstraint("hall_id", "start_time", name="uq_show_per_hall_time"),)

# # class Booking(Base):
# #     __tablename__ = "bookings"
# #     id = Column(Integer, primary_key=True)
# #     show_id = Column(Integer, ForeignKey("shows.id", ondelete="CASCADE"), nullable=False)
# #     group_name = Column(String, nullable=True)
# #     total_price = Column(Integer, nullable=False, default=0)
# #     created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
# #     show = relationship("Show", back_populates="bookings")
# #     seats = relationship("BookingSeat", back_populates="booking", cascade="all, delete-orphan")

# # class BookingSeat(Base):
# #     __tablename__ = "booking_seats"
# #     id = Column(Integer, primary_key=True)
# #     booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False)
# #     show_id = Column(Integer, ForeignKey("shows.id", ondelete="CASCADE"), nullable=False)
# #     seat_id = Column(Integer, ForeignKey("seats.id", ondelete="CASCADE"), nullable=False)
# #     booking = relationship("Booking", back_populates="seats")
# #     __table_args__ = (UniqueConstraint("show_id", "seat_id", name="uq_seat_once_per_show"),)

# # # -----------------------------
# # Pydantic Schemas
# # -----------------------------
# class TheaterCreate(BaseModel):
#     name: str
#     city: Optional[str] = None
#     address: Optional[str] = None

# class TheaterOut(TheaterCreate):
#     id: int
#     class Config:
#         orm_mode = True

# class HallRowSpec(BaseModel):
#     row_number: int = Field(..., ge=1)
#     seat_count: int = Field(..., ge=6, description="At least 6 seats per row")

# class HallCreate(BaseModel):
#     name: str
#     theater_id: int
#     rows: List[HallRowSpec]

# class HallOut(BaseModel):
#     id: int
#     name: str
#     theater_id: int
#     rows: List[HallRowSpec]
#     class Config:
#         orm_mode = True

# class MovieCreate(BaseModel):
#     title: str
#     language: Optional[str] = None
#     duration_min: Optional[int] = Field(None, gt=0)

# class MovieOut(MovieCreate):
#     id: int
#     class Config:
#         orm_mode = True

# class ShowCreate(BaseModel):
#     movie_id: int
#     hall_id: int
#     start_time: datetime
#     price: int = Field(..., ge=0)

# class ShowOut(ShowCreate):
#     id: int
#     class Config:
#         orm_mode = True

# class SeatStatus(BaseModel):
#     seat_id: int
#     row_number: int
#     seat_number: int
#     is_aisle: bool
#     booked: bool

# class BookingRequest(BaseModel):
#     movie_id: int
#     hall_id: int
#     start_time: datetime
#     group_size: int = Field(..., ge=1)
#     group_name: Optional[str] = None

# class BookingOut(BaseModel):
#     booking_id: int
#     show_id: int
#     seat_ids: List[int]
#     total_price: int

# class SuggestionOut(BaseModel):
#     show_id: int
#     start_time: datetime
#     hall_id: int
#     hall_name: str
#     contiguous_block: List[int]  # seat_ids

# class AnalyticsRequest(BaseModel):
#     movie_id: int
#     start: datetime
#     end: datetime

# class AnalyticsOut(BaseModel):
#     movie_id: int
#     tickets_sold: int
#     gmv: int

# # -----------------------------
# # Helpers
# # -----------------------------

# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()


# def create_or_refresh_seats_for_row(db: Session, row: HallRow):
#     """(Re)generate Seat entities for a row, marking 6 aisle seats (3 columns) if possible.
#     Aisle rule: we create 2 aisle breaks to form 3 blocks. The 6 aisle seats are:
#       - Left boundary seat (1), right boundary seat (N)
#       - Seats adjacent to the two aisle boundaries on both sides (4 seats)
#     Aisle boundaries are placed to split the row into 3 nearly-equal blocks.
#     """
#     # delete existing
#     db.query(Seat).filter(Seat.row_id == row.id).delete()
#     n = row.seat_count
#     # Compute two cut points roughly splitting into thirds
#     cut1 = max(2, n // 3)
#     cut2 = max(cut1 + 2, 2 * n // 3)
#     aisle_positions = set()
#     for i in (1, n, cut1, cut1 + 1, cut2, cut2 + 1):
#         if 1 <= i <= n:
#             aisle_positions.add(i)
#     for s in range(1, n + 1):
#         seat = Seat(row_id=row.id, seat_number=s, is_aisle=(s in aisle_positions))
#         db.add(seat)


# def find_contiguous_block(seats_status: List[SeatStatus], k: int) -> Optional[List[int]]:
#     """Given seat statuses for a single row, return seat_ids of first contiguous block of size k that are not booked.
#     Seats must be adjacent by seat_number and have no gaps. Aisle seats ARE allowed.
#     """
#     # Sort by seat_number just in case
#     row_sorted = sorted(seats_status, key=lambda x: x.seat_number)
#     window = []
#     last_num = None
#     for st in row_sorted:
#         if st.booked:
#             window = []
#             last_num = None
#             continue
#         if last_num is None or st.seat_number == last_num + 1:
#             window.append(st)
#             last_num = st.seat_number
#             if len(window) == k:
#                 return [x.seat_id for x in window]
#         else:
#             window = [st]
#             last_num = st.seat_number
#     return None


# def get_show_by_keys(db: Session, movie_id: int, hall_id: int, start_time: datetime) -> Show:
#     show = db.execute(
#         select(Show).where(Show.movie_id == movie_id, Show.hall_id == hall_id, Show.start_time == start_time)
#     ).scalar_one_or_none()
#     if not show:
#         raise HTTPException(status_code=404, detail="Show not found for given movie/hall/start_time")
#     return show

# # -----------------------------
# # FastAPI app
# # -----------------------------
# app = FastAPI(title="Movie Ticket Booking APIs", version="1.0")
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
# )

# # Create tables
# Base.metadata.create_all(bind=engine)

# # -----------------------------
# # CRUD: Theaters
# # -----------------------------
# @app.post("/theaters", response_model=TheaterOut)
# def create_theater(payload: TheaterCreate, db: Session = Depends(get_db)):
#     th = Theater(name=payload.name, city=payload.city, address=payload.address)
#     db.add(th)
#     try:
#         db.commit()
#     except IntegrityError:
#         db.rollback()
#         raise HTTPException(status_code=409, detail="Theater with this name already exists")
#     db.refresh(th)
#     return th

# @app.get("/theaters", response_model=List[TheaterOut])
# def list_theaters(db: Session = Depends(get_db)):
#     return db.execute(select(Theater)).scalars().all()

# @app.get("/theaters/{theater_id}", response_model=TheaterOut)
# def get_theater(theater_id: int, db: Session = Depends(get_db)):
#     th = db.get(Theater, theater_id)
#     if not th:
#         raise HTTPException(404, "Theater not found")
#     return th

# @app.delete("/theaters/{theater_id}")
# def delete_theater(theater_id: int, db: Session = Depends(get_db)):
#     th = db.get(Theater, theater_id)
#     if not th:
#         raise HTTPException(404, "Theater not found")
#     db.delete(th)
#     db.commit()
#     return {"status": "deleted"}

# # -----------------------------
# # CRUD: Halls + Layout
# # -----------------------------
# @app.post("/halls", response_model=HallOut)
# def create_hall(payload: HallCreate, db: Session = Depends(get_db)):
#     theater = db.get(Theater, payload.theater_id)
#     if not theater:
#         raise HTTPException(404, "Theater not found")

#     hall = Hall(name=payload.name, theater_id=payload.theater_id)
#     db.add(hall)
#     db.flush()  # to get hall.id

#     # Create rows and seats
#     for r in payload.rows:
#         row = HallRow(hall_id=hall.id, row_number=r.row_number, seat_count=r.seat_count)
#         db.add(row)
#         db.flush()
#         create_or_refresh_seats_for_row(db, row)
#     try:
#         db.commit()
#     except IntegrityError as e:
#         db.rollback()
#         raise HTTPException(status_code=409, detail=f"Hall/Row conflict: {str(e)}")
#     db.refresh(hall)
#     # Build response rows
#     out_rows = [HallRowSpec(row_number=rw.row_number, seat_count=rw.seat_count) for rw in hall.rows]
#     return HallOut(id=hall.id, name=hall.name, theater_id=hall.theater_id, rows=out_rows)

# @app.get("/halls/{hall_id}", response_model=HallOut)
# def get_hall(hall_id: int, db: Session = Depends(get_db)):
#     hall = db.get(Hall, hall_id)
#     if not hall:
#         raise HTTPException(404, "Hall not found")
#     out_rows = [HallRowSpec(row_number=rw.row_number, seat_count=rw.seat_count) for rw in hall.rows]
#     return HallOut(id=hall.id, name=hall.name, theater_id=hall.theater_id, rows=out_rows)

# @app.put("/halls/{hall_id}", response_model=HallOut)
# def update_hall_layout(hall_id: int, payload: HallCreate, db: Session = Depends(get_db)):
#     hall = db.get(Hall, hall_id)
#     if not hall:
#         raise HTTPException(404, "Hall not found")
#     if hall.theater_id != payload.theater_id:
#         raise HTTPException(400, "Cannot move hall to a different theater via this endpoint")

#     hall.name = payload.name
#     # Replace all rows
#     db.query(HallRow).filter(HallRow.hall_id == hall.id).delete()
#     db.flush()
#     for r in payload.rows:
#         row = HallRow(hall_id=hall.id, row_number=r.row_number, seat_count=r.seat_count)
#         db.add(row)
#         db.flush()
#         create_or_refresh_seats_for_row(db, row)
#     try:
#         db.commit()
#     except IntegrityError as e:
#         db.rollback()
#         raise HTTPException(409, f"Layout conflict: {str(e)}")

#     out_rows = [HallRowSpec(row_number=rw.row_number, seat_count=rw.seat_count) for rw in hall.rows]
#     return HallOut(id=hall.id, name=hall.name, theater_id=hall.theater_id, rows=out_rows)

# @app.delete("/halls/{hall_id}")
# def delete_hall(hall_id: int, db: Session = Depends(get_db)):
#     hall = db.get(Hall, hall_id)
#     if not hall:
#         raise HTTPException(404, "Hall not found")
#     db.delete(hall)
#     db.commit()
#     return {"status": "deleted"}

# # -----------------------------
# # CRUD: Movies
# # -----------------------------
# @app.post("/movies", response_model=MovieOut)
# def create_movie(payload: MovieCreate, db: Session = Depends(get_db)):
#     m = Movie(**payload.dict())
#     db.add(m)
#     try:
#         db.commit()
#     except IntegrityError:
#         db.rollback()
#         raise HTTPException(409, "Movie with this title already exists")
#     db.refresh(m)
#     return m

# @app.get("/movies", response_model=List[MovieOut])
# def list_movies(db: Session = Depends(get_db)):
#     return db.execute(select(Movie)).scalars().all()

# @app.get("/movies/{movie_id}", response_model=MovieOut)
# def get_movie(movie_id: int, db: Session = Depends(get_db)):
#     m = db.get(Movie, movie_id)
#     if not m:
#         raise HTTPException(404, "Movie not found")
#     return m

# @app.put("/movies/{movie_id}", response_model=MovieOut)
# def update_movie(movie_id: int, payload: MovieCreate, db: Session = Depends(get_db)):
#     m = db.get(Movie, movie_id)
#     if not m:
#         raise HTTPException(404, "Movie not found")
#     m.title = payload.title
#     m.language = payload.language
#     m.duration_min = payload.duration_min
#     try:
#         db.commit()
#     except IntegrityError:
#         db.rollback()
#         raise HTTPException(409, "Duplicate movie title")
#     db.refresh(m)
#     return m

# @app.delete("/movies/{movie_id}")
# def delete_movie(movie_id: int, db: Session = Depends(get_db)):
#     m = db.get(Movie, movie_id)
#     if not m:
#         raise HTTPException(404, "Movie not found")
#     db.delete(m)
#     db.commit()
#     return {"status": "deleted"}

# # -----------------------------
# # CRUD: Shows (movie @ hall @ time, with price)
# # -----------------------------
# @app.post("/shows", response_model=ShowOut)
# def create_show(payload: ShowCreate, db: Session = Depends(get_db)):
#     if not db.get(Movie, payload.movie_id):
#         raise HTTPException(404, "Movie not found")
#     if not db.get(Hall, payload.hall_id):
#         raise HTTPException(404, "Hall not found")
#     show = Show(**payload.dict())
#     db.add(show)
#     try:
#         db.commit()
#     except IntegrityError:
#         db.rollback()
#         raise HTTPException(409, "A show already exists in this hall at this time")
#     db.refresh(show)
#     return show

# @app.get("/shows", response_model=List[ShowOut])
# def list_shows(movie_id: Optional[int] = None, hall_id: Optional[int] = None, db: Session = Depends(get_db)):
#     stmt = select(Show)
#     if movie_id is not None:
#         stmt = stmt.where(Show.movie_id == movie_id)
#     if hall_id is not None:
#         stmt = stmt.where(Show.hall_id == hall_id)
#     return db.execute(stmt.order_by(Show.start_time)).scalars().all()

# @app.get("/shows/{show_id}", response_model=ShowOut)
# def get_show(show_id: int, db: Session = Depends(get_db)):
#     sh = db.get(Show, show_id)
#     if not sh:
#         raise HTTPException(404, "Show not found")
#     return sh

# @app.delete("/shows/{show_id}")
# def delete_show(show_id: int, db: Session = Depends(get_db)):
#     sh = db.get(Show, show_id)
#     if not sh:
#         raise HTTPException(404, "Show not found")
#     db.delete(sh)
#     db.commit()
#     return {"status": "deleted"}

# # -----------------------------
# # Read: Hall layout with booked status for a show
# # -----------------------------
# @app.get("/shows/{show_id}/layout", response_model=List[SeatStatus])
# def show_layout_status(show_id: int, db: Session = Depends(get_db)):
#     show = db.get(Show, show_id)
#     if not show:
#         raise HTTPException(404, "Show not found")
#     # seats in hall
#     seats = db.execute(
#         select(Seat, HallRow.row_number).join(HallRow, Seat.row_id == HallRow.id).where(HallRow.hall_id == show.hall_id)
#     ).all()
#     # booked seat ids for this show
#     booked_ids = set(
#         db.execute(select(BookingSeat.seat_id).where(BookingSeat.show_id == show_id)).scalars().all()
#     )
#     out = []
#     for seat, row_number in seats:
#         out.append(SeatStatus(
#             seat_id=seat.id,
#             row_number=row_number,
#             seat_number=seat.seat_number,
#             is_aisle=seat.is_aisle,
#             booked=(seat.id in booked_ids)
#         ))
#     # order primarily by row_number then seat_number
#     out.sort(key=lambda x: (x.row_number, x.seat_number))
#     return out

# # -----------------------------
# # Booking (group seats together)
# # -----------------------------
# @app.post("/bookings", response_model=BookingOut)
# def create_booking(req: BookingRequest, db: Session = Depends(get_db)):
#     # Get the show
#     show = get_show_by_keys(db, req.movie_id, req.hall_id, req.start_time)

#     # Build seat status per row
#     seats_status = show_layout_status(show.id, db)
#     by_row = {}
#     for st in seats_status:
#         by_row.setdefault(st.row_number, []).append(st)

#     chosen_block = None
#     for row_number in sorted(by_row.keys()):
#         block = find_contiguous_block(by_row[row_number], req.group_size)
#         if block:
#             chosen_block = block
#             break

#     if not chosen_block:
#         # No contiguous seats -> suggest alternatives
#         suggestions = suggest_alternatives_internal(db, req.movie_id, req.hall_id, req.start_time, req.group_size)
#         raise HTTPException(
#             status_code=409,
#             detail={
#                 "message": "Contiguous seats not available for this show",
#                 "suggestions": [s.dict() for s in suggestions]
#             }
#         )

#     # Concurrency-safe commit of the booking
#     try:
#         with db.begin():
#             booking = Booking(show_id=show.id, group_name=req.group_name or "group")
#             db.add(booking)
#             db.flush()

#             # Attempt to reserve each seat; UNIQUE constraint will protect against races
#             for seat_id in chosen_block:
#                 bs = BookingSeat(booking_id=booking.id, show_id=show.id, seat_id=seat_id)
#                 db.add(bs)
#             # compute total
#             booking.total_price = show.price * len(chosen_block)
#         db.refresh(booking)
#         return BookingOut(booking_id=booking.id, show_id=show.id, seat_ids=[s for s in chosen_block], total_price=booking.total_price)
#     except IntegrityError:
#         db.rollback()
#         # Some seat got taken concurrently — advise retry or show suggestions
#         suggestions = suggest_alternatives_internal(db, req.movie_id, req.hall_id, req.start_time, req.group_size)
#         raise HTTPException(status_code=409, detail={
#             "message": "Seats just got booked by another request. Please try again.",
#             "suggestions": [s.dict() for s in suggestions]
#         })

# # -----------------------------
# # Suggest alternatives when contiguous block not available
# # -----------------------------
# @app.get("/suggestions", response_model=List[SuggestionOut])
# def suggest_alternatives(movie_id: int, hall_id: int, start_time: datetime, group_size: int, db: Session = Depends(get_db)):
#     return suggest_alternatives_internal(db, movie_id, hall_id, start_time, group_size)


# def suggest_alternatives_internal(db: Session, movie_id: int, hall_id: int, start_time: datetime, group_size: int) -> List[SuggestionOut]:
#     # Consider other shows for the same movie on the same day (+/- 12h window)
#     start_day = datetime(start_time.year, start_time.month, start_time.day)
#     end_day = start_day + timedelta(days=1)
#     shows = db.execute(
#         select(Show, Hall.name)
#         .join(Hall, Hall.id == Show.hall_id)
#         .where(Show.movie_id == movie_id)
#         .where(Show.start_time >= start_day, Show.start_time < end_day)
#         .order_by(Show.start_time)
#     ).all()
#     suggestions: List[SuggestionOut] = []
#     for show, hall_name in shows:
#         seats_status = show_layout_status(show.id, db)
#         by_row = {}
#         for st in seats_status:
#             by_row.setdefault(st.row_number, []).append(st)
#         found = None
#         for row_number in sorted(by_row.keys()):
#             block = find_contiguous_block(by_row[row_number], group_size)
#             if block:
#                 found = block
#                 break
#         if found:
#             suggestions.append(SuggestionOut(
#                 show_id=show.id,
#                 start_time=show.start_time,
#                 hall_id=show.hall_id,
#                 hall_name=hall_name,
#                 contiguous_block=found
#             ))
#     return suggestions

# # -----------------------------
# # Analytics (BONUS)
# # -----------------------------
# @app.post("/analytics/movie", response_model=AnalyticsOut)
# def analytics_movie(req: AnalyticsRequest, db: Session = Depends(get_db)):
#     # Tickets and GMV for all shows of the movie in period
#     shows_subq = select(Show.id).where(
#         Show.movie_id == req.movie_id,
#         Show.start_time >= req.start,
#         Show.start_time <= req.end
#     ).subquery()
#     tickets = db.execute(select(func.count(BookingSeat.id)).where(BookingSeat.show_id.in_(shows_subq))).scalar_one()
#     # price per seat from show * seats — compute from bookings to avoid rounding
#     gmv = db.execute(
#         select(func.coalesce(func.sum(Booking.total_price), 0)).join(Show, Show.id == Booking.show_id)
#         .where(Show.id.in_(shows_subq))
#     ).scalar_one()
#     return AnalyticsOut(movie_id=req.movie_id, tickets_sold=tickets or 0, gmv=gmv or 0)

# # -----------------------------
# # Convenience seed endpoint (optional; remove in production)
# # -----------------------------
# @app.post("/dev/seed")
# def dev_seed(db: Session = Depends(get_db)):
#     """Quickly seed sample data for testing."""
#     # Clear all
#     Base.metadata.drop_all(bind=engine)
#     Base.metadata.create_all(bind=engine)

#     th = Theater(name="Galaxy Cinema", city="Jabalpur", address="Main Road")
#     db.add(th)
#     db.flush()

#     hall = Hall(name="Hall 1", theater_id=th.id)
#     db.add(hall)
#     db.flush()

#     # Rows with mixed seat counts
#     for rn, sc in [(1, 10), (2, 8), (3, 12)]:
#         row = HallRow(hall_id=hall.id, row_number=rn, seat_count=sc)
#         db.add(row)
#         db.flush()
#         create_or_refresh_seats_for_row(db, row)

#     m = Movie(title="Interstellar", language="English", duration_min=169)
#     db.add(m)
#     db.flush()

#     now = datetime.utcnow()
#     sh1 = Show(movie_id=m.id, hall_id=hall.id, start_time=now + timedelta(hours=3), price=250)
#     sh2 = Show(movie_id=m.id, hall_id=hall.id, start_time=now + timedelta(hours=6), price=250)
#     db.add_all([sh1, sh2])
#     db.commit()
#     return {"status": "seeded", "theater_id": th.id, "hall_id": hall.id, "movie_id": m.id, "show_ids": [sh1.id, sh2.id]}



from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from Routers import booking, movies, theaters, halls, shows  # make sure folder name is exact case
import models  # ensures models are registered with Base

# Create all database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Movie Ticket Booking System",
    description="API for managing theaters, halls, movies, shows, and bookings",
    version="1.0.0"
)

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(booking.router, prefix="/bookings", tags=["Bookings"])
app.include_router(movies.router, prefix="/movies", tags=["Movies"])
app.include_router(halls.router, prefix="/halls", tags=["Halls"])
app.include_router(theaters.router, prefix="/theaters", tags=["Theaters"])
app.include_router(shows.router, prefix="/shows", tags=["Shows"])

# Root endpoint
@app.get("/")
def root():
    return {"message": "Welcome to the Movie Ticket Booking API"}
