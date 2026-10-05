import asyncio
import sys

from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters


async def main():
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "app.mcp_server"],
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:

            print("\nInitializing MCP session...")
            await session.initialize()

            print("\nAvailable MCP tools:")
            tools = await session.list_tools()

            for tool in tools.tools:
                print(f"- {tool.name}: {tool.description}")

            print("\nCalling get_customer_bill...")
            result = await session.call_tool(
                "get_customer_bill",
                {"customer_id": "cust-001"},
            )

            print("\nResult:")
            print(result)


if __name__ == "__main__":
    asyncio.run(main())