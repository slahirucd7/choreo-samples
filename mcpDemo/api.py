from datetime import date
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field

import hotel_service as svc

router = APIRouter(prefix="/api", tags=["Hotel Reservation"])


# ── Request / Response models ────────────────────────────────────────────────

class ReservationRequest(BaseModel):
    room_id: str = Field(example="R002")
    guest_name: str = Field(example="John Doe")
    guest_email: EmailStr = Field(example="john@example.com")
    check_in: date = Field(example="2026-07-01")
    check_out: date = Field(example="2026-07-05")
    guests: int = Field(example=2)

    model_config = {
        "json_schema_extra": {
            "example": {
                "room_id": "R002",
                "guest_name": "John Doe",
                "guest_email": "john@example.com",
                "check_in": "2026-07-01",
                "check_out": "2026-07-05",
                "guests": 2,
            }
        }
    }


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/rooms")
def list_rooms(
    room_type: Optional[str] = Query(default=None, example="double"),
):
    return svc.list_rooms(room_type)


@router.get("/rooms/search")
def search_rooms(
    check_in: date = Query(example="2026-07-01"),
    check_out: date = Query(example="2026-07-05"),
    guests: int = Query(example=2),
    room_type: Optional[str] = Query(default=None, example="double"),
):
    if check_out <= check_in:
        raise HTTPException(status_code=400, detail="check_out must be after check_in")
    return svc.search_rooms(check_in, check_out, guests, room_type)


@router.post("/reservations", status_code=201)
def create_reservation(body: ReservationRequest):
    try:
        return svc.create_reservation(
            body.room_id, body.guest_name, body.guest_email,
            body.check_in, body.check_out, body.guests,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/reservations")
def list_reservations(
    guest_email: Optional[str] = Query(default=None, example="john@example.com"),
):
    return svc.list_reservations(guest_email)


@router.get("/reservations/{reservation_id}")
def get_reservation(reservation_id: str):
    try:
        return svc.get_reservation(reservation_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/reservations/{reservation_id}")
def cancel_reservation(reservation_id: str):
    try:
        return svc.cancel_reservation(reservation_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
