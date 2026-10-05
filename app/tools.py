from typing import Dict, Any

from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool


CUSTOMER_BILLS = {
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


BILL_BREAKDOWN = {
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


# =========================================================
# INPUT SCHEMAS
# =========================================================

class CustomerBillInput(BaseModel):
    customer_id: str = Field(
        description="Unique customer identifier"
    )


class BillBreakdownInput(BaseModel):
    customer_id: str = Field(
        description="Unique customer identifier"
    )


# =========================================================
# TOOL IMPLEMENTATIONS
# =========================================================

def get_customer_bill(customer_id: str) -> Dict[str, Any]:

    bill = CUSTOMER_BILLS.get(customer_id)

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


def get_bill_breakdown(customer_id: str) -> Dict[str, Any]:

    breakdown = BILL_BREAKDOWN.get(customer_id)

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


# =========================================================
# STRUCTURED TOOLS
# =========================================================

customer_bill_tool = StructuredTool.from_function(
    func=get_customer_bill,
    name="get_customer_bill",
    description=(
        "Retrieve a customer's current and previous bill, "
        "including the percentage increase and billing period."
    ),
    args_schema=CustomerBillInput,
)


bill_breakdown_tool = StructuredTool.from_function(
    func=get_bill_breakdown,
    name="get_bill_breakdown",
    description=(
        "Retrieve detailed charge components of a customer's "
        "bill, including base plan, additional usage, "
        "premium services, and taxes."
    ),
    args_schema=BillBreakdownInput,
)


# =========================================================
# TOOL REGISTRY
# =========================================================

TOOL_REGISTRY = {
    "get_customer_bill": customer_bill_tool,
    "get_bill_breakdown": bill_breakdown_tool,
}


def execute_registered_tool(
    tool_name: str,
    customer_id: str,
) -> Dict[str, Any]:

    tool = TOOL_REGISTRY.get(tool_name)

    if not tool:
        return {
            "found": False,
            "error": f"Unknown tool: {tool_name}",
        }

    return tool.invoke({
        "customer_id": customer_id
    })