from app.mcp_client import call_mcp_tool


result = call_mcp_tool(
    tool_name="get_customer_bill",
    customer_id="cust-001",
)

print("\n========== MCP CLIENT TEST ==========")
print(result)
print("=====================================\n")