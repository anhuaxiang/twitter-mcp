import os
import sys
import json
import httpx
import asyncio
from composio import Composio

from typing import Any
from mcp.types import Tool
from mcp import ClientSession
from mcp.server.lowlevel.server import Server
from mcp.server.stdio import stdio_server
from mcp.client.streamable_http import streamable_http_client


def get_env_var(name: str) -> str:
    """获取环境变量，如果不存在则提供友好的错误提示"""
    value = os.environ.get(name)
    if value is None:
        print(f"Error: Required environment variable '{name}' is not set.", file=sys.stderr)
        print(f"Please set it by running: export {name}=<your-value>", file=sys.stderr)
        sys.exit(1)
    return value


COMPOSIO_API_KEY = get_env_var('COMPOSIO_API_KEY')
COMPOSIO_MCP_URL = get_env_var('COMPOSIO_MCP_URL')


composio = Composio(api_key=COMPOSIO_API_KEY)
mcp = Server("search-mcp")


class MCPSessionManager:
    def __init__(self):
        self.http_client = httpx.AsyncClient(
            headers={"x-api-key": COMPOSIO_API_KEY},
            timeout=httpx.Timeout(
                connect=10.0,   # 连接超时：10秒
                read=None,      # 读取超时：无限制（适用于 SSE/长连接）
                write=30.0,     # 写入超时：30秒
                pool=None       # 连接池超时：无限制
            ),
        )
        self.url = COMPOSIO_MCP_URL
        self._client_cm = None
        self.session: ClientSession | None = None

    async def start(self):
        self._client_cm = streamable_http_client(self.url, http_client=self.http_client)
        read, write, _ = await self._client_cm.__aenter__()

        self.session = ClientSession(read, write)
        await self.session.__aenter__()
        await self.session.initialize()

    async def stop(self):
        if self.session:
            await self.session.__aexit__(None, None, None)
        if self._client_cm:
            await self._client_cm.__aexit__(None, None, None)
        if self.http_client:
            await self.http_client.aclose()


mcp_manager = MCPSessionManager()


# Load tool schemas
tool_schema_path = os.path.join(os.path.dirname(__file__), "tool_schema.json")
try:
    with open(tool_schema_path) as f:
        tool_schemas = json.load(f)
except FileNotFoundError:
    print(f"Error: Tool schema file not found at {tool_schema_path}", file=sys.stderr)
    sys.exit(1)
except json.JSONDecodeError as e:
    print(f"Error: Failed to parse tool schema JSON: {e}", file=sys.stderr)
    sys.exit(1)


@mcp.list_tools()
async def list_tools() -> Any:
    return [
        Tool(
            name=name,
            description=tool["description"],
            inputSchema=tool["input_schema"],
        )
        for name, tool in tool_schemas.items()
    ]


@mcp.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]):
    if name not in tool_schemas:
        raise ValueError(f"Unknown tool: {name}")

    if mcp_manager.session is None:
        raise RuntimeError("MCP session is not initialized. Please ensure the server is started properly.")

    res = await mcp_manager.session.call_tool(
        name="COMPOSIO_MULTI_EXECUTE_TOOL",
        arguments={
            "tools": [
                {
                    "tool_slug": name,
                    "arguments": arguments
                }
            ]
        },
    )
    return res



async def run_server():
    try:
        await mcp_manager.start()
        async with stdio_server() as (read_stream, write_stream):
            await mcp.run(
                read_stream=read_stream,
                write_stream=write_stream,
                initialization_options=mcp.create_initialization_options()
            )
    finally:
        await mcp_manager.stop()


def main():
    asyncio.run(run_server())


if __name__ == '__main__':
    main()
