import asyncio
import json
import sys

from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters


async def _call_mcp_tool(
    tool_name: str,
    customer_id: str,
) -> dict:

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "app.mcp_server"],
    )

    async with stdio_client(server_params) as (read_stream, write_stream):

        async with ClientSession(
            read_stream,
            write_stream,
        ) as session:

            await session.initialize()

            result = await session.call_tool(
                tool_name,
                {
                    "customer_id": customer_id,
                },
            )

            if result.is_error:
                return {
                    "found": False,
                    "error": f"MCP tool failed: {tool_name}",
                }

            for content in result.content:
                if hasattr(content, "text"):
                    try:
                        return json.loads(content.text)
                    except json.JSONDecodeError:
                        return {
                            "found": False,
                            "error": "Invalid JSON returned by MCP server",
                            "raw_response": content.text,
                        }

            return {
                "found": False,
                "error": "No content returned by MCP server",
            }


def call_mcp_tool(
    tool_name: str,
    customer_id: str,
) -> dict:

    return asyncio.run(
        _call_mcp_tool(
            tool_name=tool_name,
            customer_id=customer_id,
        )
    )