"""Authenticated local JSON-lines bridge to the Blender process."""
import json
import os
import socket
from typing import Any


class BridgeError(RuntimeError):
    """Raised when Blender cannot service an MCP request."""


def request(operation: str, params: dict[str, Any] | None = None) -> Any:
    token = os.environ.get("AGENTIC_BLENDER_TOKEN", "")
    if not token:
        raise BridgeError("Set AGENTIC_BLENDER_TOKEN to the token shown in Blender's Agentic panel")

    host = os.environ.get("AGENTIC_BLENDER_HOST", "127.0.0.1")
    if host != "127.0.0.1":
        raise BridgeError("Only loopback 127.0.0.1 is permitted")
    try:
        port = int(os.environ.get("AGENTIC_BLENDER_PORT", "8765"))
    except ValueError as error:
        raise BridgeError("AGENTIC_BLENDER_PORT must be an integer") from error

    payload = json.dumps({"token": token, "operation": operation, "params": params or {}}, allow_nan=False)
    if len(payload.encode("utf-8")) > 65535:
        raise BridgeError("Request is too large")
    try:
        with socket.create_connection((host, port), timeout=5) as connection:
            connection.settimeout(15)
            connection.sendall(payload.encode("utf-8") + b"\n")
            with connection.makefile("rb") as stream:
                response = stream.readline(65537)
    except (OSError, TimeoutError) as error:
        raise BridgeError(f"Blender bridge unavailable: {error}") from error

    if not response or len(response) > 65536 or not response.endswith(b"\n"):
        raise BridgeError("Invalid or oversized response from Blender")
    try:
        result = json.loads(response)
    except (ValueError, UnicodeError) as error:
        raise BridgeError("Malformed response from Blender") from error
    if not isinstance(result, dict) or not isinstance(result.get("ok"), bool):
        raise BridgeError("Unexpected Blender response")
    if not result["ok"]:
        raise BridgeError(str(result.get("error", "Blender operation failed")))
    return result.get("result")
