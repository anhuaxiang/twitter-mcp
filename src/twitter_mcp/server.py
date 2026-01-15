import os
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



COMPOSIO_API_KEY = os.environ['COMPOSIO_API_KEY']
COMPOSIO_MCP_URl = os.environ['COMPOSIO_MCP_URL']


composio = Composio(api_key=COMPOSIO_API_KEY)
mcp = Server("search-mcp")


class MCPSessionManager:
    def __init__(self):
        self.http_client = httpx.AsyncClient(
            headers={"x-api-key": COMPOSIO_API_KEY},
            timeout=httpx.Timeout(180),
        )
        self.url = COMPOSIO_MCP_URl
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


mcp_manager = MCPSessionManager()



with open(os.path.join(os.path.dirname(__file__), "tool_schema.json")) as f:
    tool_schemas = json.load(f)


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
    await mcp_manager.start()
    async with stdio_server() as (read_stream, write_stream):
        await mcp.run(
            read_stream=read_stream,
            write_stream=write_stream,
            initialization_options=mcp.create_initialization_options()
        )
    await mcp_manager.stop()


def main():
    asyncio.run(run_server())


if __name__ == '__main__':
    main()
