"""MCP stdio server. Run with python -m agentic_blender.server."""
from mcp.server.fastmcp import FastMCP

from .bridge import request

mcp = FastMCP("Agentic Blender")


@mcp.tool()
def scene_info() -> dict:
    """Inspect objects, selection and transforms in the active Blender scene."""
    return request("scene_info")


@mcp.tool()
def create_primitive(
    primitive: str,
    name: str = "",
    location: list[float] | None = None,
) -> dict:
    """Create a Blender primitive: CUBE, UV_SPHERE, CYLINDER, CONE, TORUS, PLANE."""
    return request("create_primitive", {"primitive": primitive, "name": name, "location": location})


@mcp.tool()
def set_transform(
    name: str,
    location: list[float] | None = None,
    rotation: list[float] | None = None,
    scale: list[float] | None = None,
) -> dict:
    """Set object transform by name. Rotation is in Euler radians."""
    return request("set_transform", {"name": name, "location": location, "rotation": rotation, "scale": scale})


@mcp.tool()
def delete_object(name: str) -> dict:
    """Remove a named object from the scene."""
    return request("delete_object", {"name": name})


@mcp.tool()
def set_material_color(name: str, rgba: list[float]) -> dict:
    """Assign an opaque/transparent RGBA Principled BSDF material to a mesh object."""
    return request("set_material_color", {"name": name, "rgba": rgba})


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
