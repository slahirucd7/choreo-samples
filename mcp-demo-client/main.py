import os
import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from mcp_client import MCPClient, run_agentic_loop

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
)
logger = logging.getLogger(__name__)

MCP_PROXY_URL     = os.environ.get("MCP_PROXY_URL", "")
MCP_PROXY_API_KEY = os.environ.get("MCP_PROXY_API_KEY", "")

mcp_client: MCPClient | None = None
openai_tools: list = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    global mcp_client, openai_tools
    logger.info("Initializing MCP client — %s", MCP_PROXY_URL)
    mcp_client = MCPClient(MCP_PROXY_URL, MCP_PROXY_API_KEY)
    mcp_client.initialize()
    openai_tools = mcp_client.to_openai_tools()
    logger.info("MCP client ready — %d tools discovered", len(openai_tools))
    yield
    logger.info("MCP client shutting down")


app = FastAPI(title="MCP Demo Client", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




class McpChatRequest(BaseModel):
    messages: list[dict]


@app.get("/api/health")
async def health():
    return {"status": "ok", "tools_loaded": len(openai_tools)}


@app.post("/api/mcp-chat")
async def mcp_chat(req: McpChatRequest, request: Request):
    if not mcp_client:
        raise HTTPException(status_code=503, detail="MCP client not initialized")

    logger.info("mcp-chat: %s", req.messages[-1].get("content", "")[:120])

    try:
        content, tools_used = await run_agentic_loop(req.messages, mcp_client, openai_tools)
        return {"error": False, "content": content, "tools_used": tools_used}
    except Exception as e:
        logger.error("Agentic loop error: %s", e)
        raise HTTPException(status_code=502, detail=str(e))
