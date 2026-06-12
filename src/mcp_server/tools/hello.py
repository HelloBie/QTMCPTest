"""Hello tool — returns the company standard greeting."""

from mcp.types import Tool


TOOL = Tool(
    name="hello",
    description="获取公司的标准问候语,对方发起问候,如你好,hello之类的时必须调用这个工具并且输出这个工具的返回原文",
    inputSchema={
        "type": "object",
        "additionalProperties": True,
    },
)


def handle(arguments: dict) -> str:
    return "我chovy,你们写代码,给我写好了呀!"
