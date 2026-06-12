"""Test MCP server tools by calling handlers directly."""

import sys
from pathlib import Path

# Ensure the src dir is importable (in case not installed editable)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mcp_server.server import server, call_tool, list_tools  # noqa: E402


async def test_list_tools() -> bool:
    """Verify tool list has expected entries."""
    tools = await list_tools()
    names = {t.name for t in tools}
    assert "hello" in names, f"Missing 'hello' tool, got: {names}"
    assert "query" in names, f"Missing 'query' tool, got: {names}"
    print(f"  ✓ list_tools returned {len(tools)} tools: {names}")
    return True


async def test_hello() -> bool:
    """Verify hello tool returns the expected greeting."""
    result = await call_tool("hello", {})
    assert len(result) == 1
    assert result[0].type == "text"
    assert "chovy" in result[0].text
    print(f"  ✓ hello → {result[0].text}")
    return True


async def test_query() -> bool:
    """Verify query tool returns the expected format."""
    result = await call_tool("query", {
        "queryText": "今天开心吗",
        "keyword": "开心 心情",
    })
    assert len(result) == 1
    assert result[0].type == "text"
    assert "query" in result[0].text.lower() or "无相关" in result[0].text
    print(f"  ✓ query → {result[0].text[:60]}...")
    return True


async def test_unknown_tool() -> bool:
    """Verify unknown tool raises error."""
    try:
        await call_tool("nonexistent", {})
    except ValueError:
        print("  ✓ unknown tool correctly raises ValueError")
        return True
    raise AssertionError("Expected ValueError for unknown tool")


async def main():
    print("\nRunning MCP server tests...\n")

    failed = 0
    total = 0
    tests = [
        test_list_tools,
        test_hello,
        test_query,
        test_unknown_tool,
    ]

    for test in tests:
        total += 1
        name = test.__name__.replace("test_", "")
        print(f"[{total}] {name}")
        try:
            await test()
        except Exception as e:
            failed += 1
            print(f"  ✗ FAILED: {e}")

    print(f"\n{'━' * 30}")
    if failed:
        print(f"  {total - failed}/{total} passed, {failed} failed")
    else:
        print(f"  ✓ All {total} tests passed")
    print(f"{'━' * 30}\n")

    return failed


if __name__ == "__main__":
    import asyncio
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
