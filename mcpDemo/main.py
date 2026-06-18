import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import router as api_router
from mcp_server import mcp

# Initialize the session manager (lazy — must call before accessing mcp.session_manager)
mcp_starlette = mcp.streamable_http_app()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # FastAPI does not invoke lifespan of mounted sub-apps, so we start the
    # MCP session manager's task group explicitly here.
    async with mcp.session_manager.run():
        yield


app = FastAPI(
    title="Hotel Reservation Service",
    description="REST API and MCP server for hotel reservations",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# REST API routes
app.include_router(api_router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "hotel-reservation"}


# MCP endpoint at /mcp — mcp_starlette has its route registered at /mcp internally
app.mount("/", mcp_starlette)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=9000, reload=True)
