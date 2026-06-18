from datetime import date
from typing import Optional
from mcp.server.fastmcp import FastMCP

import hotel_service as svc

mcp = FastMCP("Hotel Reservation Service", host="0.0.0.0")


@mcp.tool()
def search_available_rooms(check_in: str, check_out: str, guests: int, room_type: Optional[str] = None) -> list[dict]:
    """Search for available hotel rooms.

    Args:
        check_in: Check-in date in YYYY-MM-DD format
        check_out: Check-out date in YYYY-MM-DD format
        guests: Number of guests
        room_type: Optional filter - 'single', 'double', or 'suite'
    """
    return svc.search_rooms(
        date.fromisoformat(check_in),
        date.fromisoformat(check_out),
        guests,
        room_type,
    )


@mcp.tool()
def get_all_rooms(room_type: Optional[str] = None) -> list[dict]:
    """List all available room types in the hotel.

    Args:
        room_type: Optional filter - 'single', 'double', or 'suite'
    """
    return svc.list_rooms(room_type)


@mcp.tool()
def make_reservation(
    room_id: str,
    guest_name: str,
    guest_email: str,
    check_in: str,
    check_out: str,
    guests: int,
) -> dict:
    """Create a new hotel reservation.

    Args:
        room_id: Room ID (e.g. R001, R002)
        guest_name: Full name of the guest
        guest_email: Email address of the guest
        check_in: Check-in date in YYYY-MM-DD format
        check_out: Check-out date in YYYY-MM-DD format
        guests: Number of guests
    """
    try:
        return svc.create_reservation(
            room_id, guest_name, guest_email,
            date.fromisoformat(check_in),
            date.fromisoformat(check_out),
            guests,
        )
    except ValueError as e:
        return {"error": str(e)}


@mcp.tool()
def get_reservation_details(reservation_id: str) -> dict:
    """Get details of a specific reservation.

    Args:
        reservation_id: Reservation ID (e.g. RES-XXXXXXXX)
    """
    try:
        return svc.get_reservation(reservation_id)
    except ValueError as e:
        return {"error": str(e)}


@mcp.tool()
def list_guest_reservations(guest_email: str) -> list[dict]:
    """List all reservations for a guest by email.

    Args:
        guest_email: Email address of the guest
    """
    return svc.list_reservations(guest_email)


@mcp.tool()
def cancel_reservation(reservation_id: str) -> dict:
    """Cancel an existing reservation.

    Args:
        reservation_id: Reservation ID to cancel (e.g. RES-XXXXXXXX)
    """
    try:
        return svc.cancel_reservation(reservation_id)
    except ValueError as e:
        return {"error": str(e)}
