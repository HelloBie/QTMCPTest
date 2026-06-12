# MCPTest

基于 Python 的 MCP (Model Context Protocol) 测试服务器，HTTP+SSE 传输模式，局域网内多台机器可共享使用。

## 快速启动

### 1. 创建虚拟环境

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动服务

```bash
PYTHONPATH=src python -m mcp_server.server
```

默认监听 `0.0.0.0:9020`，局域网内其他机器均可访问。启动后 stderr 会打印配置教程和检测到的本机局域网 IP。

自定义参数：

```bash
PYTHONPATH=src python -m mcp_server.server --host 192.168.1.100 --port 8080
```

### 4. 配置客户端

将启动日志中打印的 JSON 复制到对应客户端的 MCP 配置文件：

| 客户端 | 配置文件路径 |
|--------|-------------|
| Claude Code | `.claude/mcp.json`（项目级） |
| Claude Desktop | `~/Library/Application Support/Claude/claude_desktop_config.json` |

配置示例：

```json
{
  "mcpServers": {
    "mcptest": {
      "type": "sse",
      "url": "http://192.168.1.100:9020"
    }
  }
}
```

### 5. 验证

重启客户端，在对话中输入"你好"或"hello"，若收到 `hello` 工具返回的问候语则集成成功。

### 6. 运行测试

```bash
python tests/test_server.py
```

## 项目结构

```
QTMCPTest/
├── pyproject.toml
├── src/mcp_server/
│   ├── __init__.py
│   └── server.py          # 主服务器，190 行
└── tests/
    ├── __init__.py
    └── test_server.py      # 单元测试，90 行
```

## 代码说明

### 服务器核心 ─ `server.py`

**初始化**：创建 `Server("mcptest")` 实例，配置 DEBUG 级别日志输出到 stderr。

**路由（ASGI 协议）**：

| 方法 | 路径 | 用途 |
|------|------|------|
| GET | `/` 或 `/sse` | 建立 SSE 长连接，服务端推送 endpoint 事件告知 POST 地址 |
| POST | `/messages` | 客户端通过此路径发送 JSON-RPC 消息 |
| GET | `/health` | 健康检查，返回 `ok` |

**注册的 MCP 工具**：

| 工具名 | 参数 | 说明 |
|--------|------|------|
| `hello` | 无 | 返回固定问候语，用于验证 MCP 连接是否正常 |
| `query` | `queryText`（用户原文）、`keyword`（提取的关键词） | 模拟知识库检索，将输入拼接后返回 |

**辅助函数**：

- `get_local_ips()` ─ 通过 `socket.getifaddrs()` 检测本机所有非 loopback 的 IPv4 地址，启动时打印到教程中，方便局域网内其他机器配置
- `setup_guide()` ─ 生成带框线的 MCP 集成配置教程，包含本机 IP、JSON 配置、客户端路径说明
- `mcp_config()` ─ 生成 MCP 客户端配置 JSON

### 测试 ─ `test_server.py`

直接调用 handler 函数，不启动 HTTP 服务：

| 用例 | 验证内容 |
|------|---------|
| `test_list_tools` | 工具列表包含 `hello` 和 `query` |
| `test_hello` | `hello` 工具返回内容含 "chovy" |
| `test_query` | `query` 工具返回格式正确 |
| `test_unknown_tool` | 未知工具名抛出 `ValueError` |
