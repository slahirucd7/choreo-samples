import httpx
import json


class MCPClient:
    """Lightweight MCP streamable-http client."""

    def __init__(self, url: str, auth_token: str | None = None):
        self.url = url
        self.session_id: str | None = None
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if auth_token:
            self.headers["Authorization"] = f"Bearer {auth_token}"

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
                "clientInfo": {"name": "choreo-scheduled-task", "version": "1.0"},
            },
        }
        response = httpx.post(self.url, headers=self.headers, json=payload, verify=False, timeout=120)
        response.raise_for_status()
        self.session_id = response.headers.get("mcp-session-id")
        return self._parse_event(response.text)

    def _post(self, method: str, params: dict, request_id: int = 2) -> dict:
        if not self.session_id:
            raise RuntimeError("Not initialized. Call initialize() first.")
        headers = {**self.headers, "mcp-session-id": self.session_id}
        payload = {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}
        response = httpx.post(self.url, headers=headers, json=payload, verify=False, timeout=120)
        response.raise_for_status()
        return self._parse_event(response.text)

    def call_tool(self, name: str, arguments: dict, request_id: int = 2) -> dict:
        result = self._post("tools/call", {"name": name, "arguments": arguments}, request_id)
        tool_result = result.get("result", {})
        # Prefer structuredContent.result (full typed result)
        structured = tool_result.get("structuredContent", {})
        if "result" in structured:
            return structured["result"]
        # Fall back to parsing all content items
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
