"""MCP tools collection — one tool per file."""

from mcp.types import Tool, TextContent

from . import hello, query

TOOLS: list[Tool] = [hello.TOOL, query.TOOL]

_HANDLERS: dict[str, callable] = {
    "hello": hello.handle,
    "query": query.handle,
}


def execute(name: str, arguments: dict) -> list[TextContent]:
    handler = _HANDLERS.get(name)
    if handler is None:
        raise ValueError(f"Unknown tool: {name}")
    text = handler(arguments)
    return [TextContent(type="text", text=text)]
