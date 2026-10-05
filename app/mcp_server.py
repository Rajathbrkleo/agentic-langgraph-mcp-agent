from mcp.server.mcpserver import MCPServer

mcp = MCPServer("Billing MCP Server")


@mcp.tool()
def get_customer_bill(customer_id: str) -> dict:
    """Retrieve a customer's current and previous bill."""

    bills = {
        "cust-001": {
            "previous_bill": 3200,
            "current_bill": 7850,
            "currency": "INR",
            "billing_period": "September 2026",
        },
        "cust-002": {
            "previous_bill": 4500,
            "current_bill": 4700,
            "currency": "INR",
            "billing_period": "September 2026",
        },
    }

    bill = bills.get(customer_id)

    if not bill:
        return {
            "found": False,
            "customer_id": customer_id,
        }

    previous = bill["previous_bill"]
    current = bill["current_bill"]

    increase_percentage = (
        ((current - previous) / previous) * 100
        if previous
        else 0
    )

    return {
        "found": True,
        "customer_id": customer_id,
        "previous_bill": previous,
        "current_bill": current,
        "increase_percentage": round(increase_percentage, 2),
        "currency": bill["currency"],
        "billing_period": bill["billing_period"],
    }


@mcp.tool()
def get_bill_breakdown(customer_id: str) -> dict:
    """Retrieve detailed components of a customer's bill."""

    breakdowns = {
        "cust-001": {
            "base_plan": 3200,
            "additional_usage": 2500,
            "premium_services": 1200,
            "taxes": 950,
        },
        "cust-002": {
            "base_plan": 4500,
            "additional_usage": 0,
            "premium_services": 0,
            "taxes": 200,
        },
    }

    breakdown = breakdowns.get(customer_id)

    if not breakdown:
        return {
            "found": False,
            "customer_id": customer_id,
        }

    return {
        "found": True,
        "customer_id": customer_id,
        "breakdown": breakdown,
        "total": sum(breakdown.values()),
    }


if __name__ == "__main__":
    mcp.run()