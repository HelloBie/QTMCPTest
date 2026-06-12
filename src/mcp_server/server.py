"""An MCP server with HTTP+SSE transport (spec 2024-11-05)."""

import argparse
import json
import logging
import socket
import sys
import traceback
from pathlib import Path

import uvicorn

from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import Tool, TextContent

LOG_FILE = Path(__file__).resolve().parent.parent.parent / "server_debug.log"

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stderr),
        logging.FileHandler(LOG_FILE, mode="w", encoding="utf-8"),
    ],
)
logger = logging.getLogger("mcptest")
logger.info("日志文件: %s", LOG_FILE)

server = Server("mcptest")
PROJECT = Path(__file__).resolve().parents[1]


def mcp_config(host: str, port: int) -> dict:
    return {
        "mcpServers": {
            "mcptest": {
                "type": "sse",
                "url": f"http://{host}:{port}",
            },
        },
    }


def _indent(text: str, prefix: str = "  ") -> str:
    return "\n".join(prefix + line for line in text.splitlines())


def get_local_ips() -> list[str]:
    """Return all non-loopback IPv4 addresses on this machine."""
    ips = []
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            addr = info[4][0]
            if not addr.startswith("127.") and addr not in ips:
                ips.append(addr)
    except Exception:
        pass

    if not ips:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ips.append(s.getsockname()[0])
            s.close()
        except Exception:
            pass

    return ips


def setup_guide(host: str, port: int, local_ips: list[str]) -> str:
    ip_urls = [f"http://{ip}:{port}" for ip in local_ips]
    any_url = ip_urls[0] if ip_urls else f"http://{host}:{port}"

    ip_lines = "\n".join(
        f"║     → {url}" + " " * max(0, 43 - len(url)) + "║"
        for url in ip_urls
    ) if ip_urls else "║     (未检测到局域网 IP)                              ║"

    return f"""
╔══════════════════════════════════════════════════════╗
║     MCP 集成配置 & 使用教程 (HTTP+SSE 模式)         ║
╠══════════════════════════════════════════════════════╣
║                                                      ║
║  本机局域网 IP:                                       ║
{ip_lines}
║                                                      ║
║  1. 将下面的 JSON 复制到客户端的 MCP 配置文件         ║
║                                                      ║
║  2. 各客户端配置文件路径:                             ║
║     Claude Code   → .claude/mcp.json (项目级)         ║
║     Claude Desktop → ~/Library/Application Support/  ║
║                      Claude/claude_desktop_config.json║
║                                                      ║
║  3. 本服务器正在监听: {any_url}                  ║
║     配置完成后无需重启本服务，重启客户端即可          ║
║                                                      ║
║  4. 验证: 在客户端里说"你好"或"hello"                ║
║     若收到回复说明 MCP 已成功集成                     ║
║                                                      ║
╚══════════════════════════════════════════════════════╝
"""  # noqa: E501


def print_mcp_config(host: str, port: int, local_ips: list[str]) -> None:
    """Print copyable MCP config JSON to stderr."""
    addr = local_ips[0] if local_ips else host
    cfg = mcp_config(addr, port)
    print("━" * 54, file=sys.stderr)
    print("MCP 配置 JSON（可直接复制）:", file=sys.stderr)
    print(json.dumps(cfg, indent=2, ensure_ascii=False), file=sys.stderr)
    print("━" * 54, file=sys.stderr)


@server.list_tools()
async def list_tools() -> list[Tool]:
    logger.info("[list_tools] 客户端请求工具列表")
    tools = [
        Tool(
            name="hello",
            description="获取公司的标准问候语,对方发起问候,如你好,hello之类的时必须调用这个工具并且输出这个工具的返回原文",
            inputSchema={
                "type": "object",
                "additionalProperties": True,
            },
        ),
        Tool(
            name="query",
            description="知识库检索工具,用户发起的任何提问性内容都要走这个工具查询,无论查询结果如何,把本工具返回的结果原文放置到你的回答正文开头",
            inputSchema={
                "type": "object",
                "properties": {
                    "queryText": {"type": "string", "description": "用户询问的原文"},
                    "keyword": {"type": "string", "description": "用户询问的相关关键词尽可能多的提取出来,以便于后续检索使用"},
                },
                "required": ["queryText", "keyword"],
                "additionalProperties": False,
            },
        ),
    ]
    logger.info("[list_tools] 返回 %d 个工具: %s", len(tools), [t.name for t in tools])
    return tools


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    logger.info("[call_tool] 工具调用 name=%r arguments=%s", name, json.dumps(arguments, ensure_ascii=False))
    if name == "hello":
        text = "我chovy,你们写代码,给我写好了呀!"
        logger.info("[call_tool] hello → %s", text)
        return [TextContent(type="text", text=text)]
    if name == "query":
        text = "无相关资料]\n" + arguments.get("keyword", "") + "\n" + arguments.get("queryText", "")
        logger.info("[call_tool] query → %s", text[:80])
        return [TextContent(type="text", text=text)]
    logger.error("[call_tool] 未知工具: %s", name)
    raise ValueError(f"Unknown tool: {name}")


def create_app(host: str, port: int):
    # endpoint 参数是相对路径，客户端会 POST 到这个路径
    transport = SseServerTransport("/messages")

    async def handle_sse(scope, receive, send):
        logger.info("[SSE] 客户端连接 headers=%s client=%s",
                     {k.decode(): v.decode() for k, v in scope.get("headers", [])},
                     scope.get("client"))
        try:
            async with transport.connect_sse(scope, receive, send) as (read, write):
                logger.info("[SSE] 会话建立，开始 server.run()")
                await server.run(read, write, server.create_initialization_options())
                logger.info("[SSE] server.run() 结束")
        except Exception:
            logger.error("[SSE] 异常断开:\n%s", traceback.format_exc())

    async def handle_messages(scope, receive, send):
        logger.info("[POST] 收到消息 query=%s headers=%s client=%s",
                     scope.get("query_string", b"").decode(),
                     {k.decode(): v.decode() for k, v in scope.get("headers", [])},
                     scope.get("client"))
        try:
            await transport.handle_post_message(scope, receive, send)
            logger.info("[POST] 处理完毕")
        except Exception:
            logger.error("[POST] 处理失败:\n%s", traceback.format_exc())

    async def asgi(scope, receive, send):
        if scope["type"] == "lifespan":
            return

        path = scope["path"]
        method = scope["method"]
        headers = {k.decode(): v.decode() for k, v in scope.get("headers", [])}
        logger.info("[ASGI] %s %s headers=%s client=%s", method, path, headers, scope.get("client"))

        if method == "GET" and (path == "/" or path == "/sse"):
            # HTTP+SSE: 客户端通过 GET 建立 SSE 长连接
            # 服务端返回 endpoint 事件，告诉客户端 POST 地址
            await handle_sse(scope, receive, send)
        elif path == "/messages" and method == "POST":
            # HTTP+SSE: 客户端 POST JSON-RPC 消息到这里
            await handle_messages(scope, receive, send)
        elif path == "/health" and method == "GET":
            await send({
                "type": "http.response.start",
                "status": 200,
                "headers": [[b"content-type", b"text/plain"]],
            })
            await send({"type": "http.response.body", "body": b"ok"})
        else:
            logger.warning("[ASGI] 未匹配路由: %s %s", method, path)
            await send({
                "type": "http.response.start",
                "status": 404,
                "headers": [[b"content-type", b"text/plain"]],
            })
            await send({"type": "http.response.body", "body": b"Not Found"})

    local_ips = get_local_ips()
    print_mcp_config(host, port, local_ips)
    print(setup_guide(host, port, local_ips), file=sys.stderr)
    for ip in local_ips:
        logger.info("局域网可访问: http://%s:%d", ip, port)
    logger.info("MCP 服务器 '%s' 启动完成 http://%s:%d (HTTP+SSE)", server.name, host, port)

    return asgi


def main() -> None:
    parser = argparse.ArgumentParser(description="MCP server (HTTP+SSE mode)")
    parser.add_argument("--host", default="0.0.0.0", help="Listen host (default: 0.0.0.0, LAN accessible)")
    parser.add_argument("--port", type=int, default=9020, help="Listen port (default: 9020)")
    args = parser.parse_args()

    app = create_app(args.host, args.port)
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
