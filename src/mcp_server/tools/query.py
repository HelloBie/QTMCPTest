"""Query tool — knowledge base search."""

from mcp.types import Tool


TOOL = Tool(
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
)


def handle(arguments: dict) -> str:
    return "无相关资料]\n" + arguments.get("keyword", "") + "\n" + arguments.get("queryText", "")
