import httpx
import json
import os
from openai import AsyncAzureOpenAI

AZURE_OPENAI_ENDPOINT   = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_KEY    = os.environ.get("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_DEPLOYMENT = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
AZURE_OPENAI_API_VERSION = os.environ.get("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")


class MCPClient:
    """Lightweight MCP streamable-http client with X-API-KEY auth."""

    def __init__(self, url: str, api_key: str):
        self.url = url
        self.session_id: str | None = None
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "X-API-KEY": api_key,
        }

    def _parse_event(self, response_text: str) -> dict:
        for line in response_text.splitlines():
            if line.startswith("data:"):
                return json.loads(line[5:].strip())
        return {}

    def initialize(self) -> dict:
        payload = {
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "mcp-demo-client", "version": "1.0"},
            },
        }
        response = httpx.post(self.url, headers=self.headers, json=payload, verify=False, timeout=30)
        response.raise_for_status()
        self.session_id = response.headers.get("mcp-session-id")
        return self._parse_event(response.text)

    def _post(self, method: str, params: dict, request_id: int = 2) -> dict:
        if not self.session_id:
            raise RuntimeError("Not initialized. Call initialize() first.")
        headers = {**self.headers, "mcp-session-id": self.session_id}
        payload = {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}
        response = httpx.post(self.url, headers=headers, json=payload, verify=False, timeout=10)
        response.raise_for_status()
        return self._parse_event(response.text)

    def call_tool(self, name: str, arguments: dict, request_id: int = 2) -> dict:
        result = self._post("tools/call", {"name": name, "arguments": arguments}, request_id)
        tool_result = result.get("result", {})
        structured = tool_result.get("structuredContent", {})
        if "result" in structured:
            return structured["result"]
        content = tool_result.get("content", [])
        if content and isinstance(content, list):
            parsed = []
            for item in content:
                text = item.get("text", "")
                try:
                    parsed.append(json.loads(text))
                except (json.JSONDecodeError, TypeError):
                    parsed.append({"raw": text})
            return parsed if len(parsed) > 1 else parsed[0]
        return tool_result

    def list_tools(self) -> list:
        result = self._post("tools/list", {})
        return result.get("result", {}).get("tools", [])

    def to_openai_tools(self) -> list:
        """Convert MCP tool schemas to OpenAI function-calling format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "parameters": t.get("inputSchema", {"type": "object", "properties": {}}),
                },
            }
            for t in self.list_tools()
        ]


async def run_agentic_loop(messages: list[dict], mcp: MCPClient, openai_tools: list) -> str:
    """Run the LLM ↔ MCP tool call loop until the LLM returns a plain text response."""
    az_client = AsyncAzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
    )

    conversation = list(messages)
    MAX_ROUNDS = 5

    for _ in range(MAX_ROUNDS):
        response = await az_client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=conversation,
            tools=openai_tools or None,
            tool_choice="auto" if openai_tools else None,
        )

        msg = response.choices[0].message

        if not msg.tool_calls:
            return msg.content or ""

        conversation.append(msg.model_dump(exclude_unset=True))

        for tc in msg.tool_calls:
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}
            result = mcp.call_tool(tc.function.name, args)
            conversation.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result),
            })

    return "Unable to complete the request after multiple attempts."
