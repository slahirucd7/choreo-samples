import os
import logging
import httpx
from datetime import date, timedelta
from mcp_client import MCPClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

MCP_URL           = os.environ.get("MCP_URL", "")
OAUTH_TOKEN_URL   = os.environ.get("OAUTH_TOKEN_URL", "")
OAUTH_CLIENT_ID   = os.environ.get("OAUTH_CLIENT_ID", "")
OAUTH_CLIENT_SECRET = os.environ.get("OAUTH_CLIENT_SECRET", "")


def get_access_token() -> str:
    """Fetch a fresh OAuth2 token using client credentials."""
    response = httpx.post(
        OAUTH_TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": OAUTH_CLIENT_ID,
            "client_secret": OAUTH_CLIENT_SECRET,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        verify=False,
        timeout=15,
    )
    response.raise_for_status()
    token = response.json()["access_token"]
    log.info("Access token fetched successfully")
    return token


def run():
    log.info("=== Hotel Reservation Scheduled Task Started ===")
    log.info("MCP URL: %s", MCP_URL)

    # ── Get token
    token = get_access_token()

    client = MCPClient(MCP_URL, token)

    # ── Initialize Client
    info = client.initialize()
    server = info.get("result", {}).get("serverInfo", {})
    log.info("Connected to: %s v%s", server.get("name"), server.get("version"))

    # ── 1. List all available rooms via the get_all_rooms tool
    log.info("--- Room Inventory ---")
    rooms = client.call_tool("get_all_rooms", {}, request_id=2)
    if isinstance(rooms, list):
        for room in rooms:
            log.info("  [%s] %s — $%.2f/night (max %d guests)",
                     room.get("room_id"), room.get("name"),
                     room.get("price_per_night", 0), room.get("max_guests", 0))
    else:
        log.info("  Rooms: %s", rooms)

    # ── 2. Search available rooms for next week via the search_available_rooms tool
    check_in  = (date.today() + timedelta(days=7)).isoformat()
    check_out = (date.today() + timedelta(days=10)).isoformat()
    log.info("--- Available Rooms (%s to %s, 2 guests) ---", check_in, check_out)
    available = client.call_tool("search_available_rooms", {
        "check_in": check_in,
        "check_out": check_out,
        "guests": 2,
    }, request_id=3)
    if isinstance(available, list):
        if available:
            for room in available:
                log.info("  [%s] %s — $%.2f total",
                         room.get("room_id"), room.get("name"), room.get("total_price", 0))
        else:
            log.info("  No rooms available for selected dates")
    else:
        log.info("  Available: %s", available)

    # ── 3. List reservations via the list_guest_reservations tool with empty email filter to get all reservations
    log.info("--- All Reservations ---")
    reservations = client.call_tool("list_guest_reservations", {"guest_email": ""}, request_id=4)
    if isinstance(reservations, dict) and reservations.get("error"):
        log.info("  No reservations found (empty email filter)")
    elif isinstance(reservations, list):
        if reservations:
            for res in reservations:
                log.info("  [%s] %s — Room %s, %s to %s (%s)",
                         res.get("reservation_id"), res.get("guest_name"),
                         res.get("room_id"), res.get("check_in"),
                         res.get("check_out"), res.get("status"))
        else:
            log.info("  No reservations found")
    else:
        log.info("  Reservations: %s", reservations)

    log.info("=== Scheduled Task Completed ===")


if __name__ == "__main__":
    run()
