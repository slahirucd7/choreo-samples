import uuid
from datetime import date
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class Room:
    id: str
    name: str
    type: str  # single, double, suite
    price_per_night: float
    max_guests: int
    amenities: list[str]


@dataclass
class Reservation:
    id: str
    room_id: str
    guest_name: str
    guest_email: str
    check_in: date
    check_out: date
    guests: int
    total_price: float
    status: str = "confirmed"  # confirmed, cancelled


ROOMS: dict[str, Room] = {
    "R001": Room("R001", "Garden View Single", "single", 89.0, 1, ["WiFi", "TV", "Air Conditioning"]),
    "R002": Room("R002", "City View Double", "double", 139.0, 2, ["WiFi", "TV", "Air Conditioning", "Mini Bar"]),
    "R003": Room("R003", "Deluxe Double", "double", 179.0, 2, ["WiFi", "TV", "Air Conditioning", "Mini Bar", "Balcony"]),
    "R004": Room("R004", "Executive Suite", "suite", 299.0, 4, ["WiFi", "TV", "Air Conditioning", "Mini Bar", "Balcony", "Jacuzzi"]),
    "R005": Room("R005", "Penthouse Suite", "suite", 499.0, 4, ["WiFi", "TV", "Air Conditioning", "Mini Bar", "Terrace", "Jacuzzi", "Butler Service"]),
}

RESERVATIONS: dict[str, Reservation] = {}


def _is_room_available(room_id: str, check_in: date, check_out: date, exclude_reservation_id: Optional[str] = None) -> bool:
    for res in RESERVATIONS.values():
        if res.id == exclude_reservation_id or res.status == "cancelled" or res.room_id != room_id:
            continue
        if not (check_out <= res.check_in or check_in >= res.check_out):
            return False
    return True


def search_rooms(check_in: date, check_out: date, guests: int, room_type: Optional[str] = None) -> list[dict]:
    results = []
    nights = (check_out - check_in).days
    for room in ROOMS.values():
        if room.max_guests < guests:
            continue
        if room_type and room.type != room_type:
            continue
        if not _is_room_available(room.id, check_in, check_out):
            continue
        results.append({
            "room_id": room.id,
            "name": room.name,
            "type": room.type,
            "price_per_night": room.price_per_night,
            "total_price": room.price_per_night * nights,
            "nights": nights,
            "max_guests": room.max_guests,
            "amenities": room.amenities,
            "available": True,
        })
    return sorted(results, key=lambda r: r["price_per_night"])


def create_reservation(room_id: str, guest_name: str, guest_email: str,
                       check_in: date, check_out: date, guests: int) -> dict:
    if room_id not in ROOMS:
        raise ValueError(f"Room {room_id} does not exist")
    room = ROOMS[room_id]
    if guests > room.max_guests:
        raise ValueError(f"Room {room_id} supports max {room.max_guests} guests")
    if check_out <= check_in:
        raise ValueError("Check-out must be after check-in")
    if not _is_room_available(room_id, check_in, check_out):
        raise ValueError(f"Room {room_id} is not available for the selected dates")

    nights = (check_out - check_in).days
    reservation = Reservation(
        id=f"RES-{uuid.uuid4().hex[:8].upper()}",
        room_id=room_id,
        guest_name=guest_name,
        guest_email=guest_email,
        check_in=check_in,
        check_out=check_out,
        guests=guests,
        total_price=room.price_per_night * nights,
    )
    RESERVATIONS[reservation.id] = reservation
    return _reservation_to_dict(reservation)


def get_reservation(reservation_id: str) -> dict:
    if reservation_id not in RESERVATIONS:
        raise ValueError(f"Reservation {reservation_id} not found")
    return _reservation_to_dict(RESERVATIONS[reservation_id])


def list_reservations(guest_email: Optional[str] = None) -> list[dict]:
    reservations = RESERVATIONS.values()
    if guest_email:
        reservations = [r for r in reservations if r.guest_email == guest_email]
    return [_reservation_to_dict(r) for r in reservations]


def cancel_reservation(reservation_id: str) -> dict:
    if reservation_id not in RESERVATIONS:
        raise ValueError(f"Reservation {reservation_id} not found")
    reservation = RESERVATIONS[reservation_id]
    if reservation.status == "cancelled":
        raise ValueError(f"Reservation {reservation_id} is already cancelled")
    reservation.status = "cancelled"
    return _reservation_to_dict(reservation)


def list_rooms(room_type: Optional[str] = None) -> list[dict]:
    rooms = ROOMS.values()
    if room_type:
        rooms = [r for r in rooms if r.type == room_type]
    return [
        {
            "room_id": r.id,
            "name": r.name,
            "type": r.type,
            "price_per_night": r.price_per_night,
            "max_guests": r.max_guests,
            "amenities": r.amenities,
        }
        for r in rooms
    ]


def _reservation_to_dict(r: Reservation) -> dict:
    room = ROOMS.get(r.room_id)
    return {
        "reservation_id": r.id,
        "room_id": r.room_id,
        "room_name": room.name if room else "Unknown",
        "guest_name": r.guest_name,
        "guest_email": r.guest_email,
        "check_in": r.check_in.isoformat(),
        "check_out": r.check_out.isoformat(),
        "guests": r.guests,
        "total_price": r.total_price,
        "status": r.status,
    }
