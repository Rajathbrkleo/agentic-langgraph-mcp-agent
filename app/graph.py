from typing import TypedDict, Literal
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from app.models import get_llm
from app.tools import get_customer_bill, get_bill_breakdown
from app.tools import execute_registered_tool

class AgentState(TypedDict):
    conversation_id: str
    customer_id: str
    message: str
    language: str

    intent: str
    confidence: float
    response: str
    escalate: bool

    plan: str
    action: str
    tool_name: str
    tool_result: dict

class AgentDecision(TypedDict):
    intent: Literal[
        "billing_inquiry",
        "payment",
        "bill_delivery",
        "service_issue",
        "complaint",
        "general_inquiry",
        "unknown"
    ]
    plan: str

    action: Literal[
        "answer",
        "retrieve_knowledge",
        "call_tool",
        "escalate"
    ]

    tool_name: Literal[
    "get_customer_bill",
    "get_bill_breakdown",
    "none"
    ]


class ToolDecision(TypedDict):
    next_action: Literal[
        "answer",
        "get_bill_breakdown",
        "escalate"
    ]
    reason: str



llm = get_llm()


planner_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are the planning component of an enterprise
customer-service AI agent.

Classify the customer's request.

You MUST choose exactly one intent from:

- billing_inquiry
- payment
- bill_delivery
- service_issue
- complaint
- general_inquiry
- unknown

You MUST choose exactly one action from:

- answer
- retrieve_knowledge
- call_tool
- escalate

Decision rules:

1. billing_inquiry:
   Questions about the customer's bill, bill amount,
   unexpected charges, or bill increase.

2. payment:
   Questions about paying a bill or payment status.

3. bill_delivery:
   Questions about receiving or downloading a bill.

4. service_issue:
   Problems with the actual service.

5. complaint:
   Customer dissatisfaction or formal complaint.

6. general_inquiry:
   General questions that don't require customer-specific data.

7. unknown:
   The request cannot be understood.

Action rules:

- answer:
  Use when the question can be answered directly.

- retrieve_knowledge:
  Use when company policy or knowledge-base information
  is required.

- call_tool:
  Use when customer-specific information is required.

- escalate:
  Use when human intervention is appropriate.

IMPORTANT:

If the customer asks why THEIR bill increased, this requires
customer-specific billing information.

Therefore choose:

intent = billing_inquiry
action = call_tool

Never invent customer-specific information.

Create a short plan describing what the agent should do.

Tool selection rules:

If action = call_tool, you MUST select exactly one tool.

Available tools:

1. get_customer_bill
   Use this to retrieve the customer's previous bill,
   current bill, billing period, and percentage increase.

2. get_bill_breakdown
   Use this when the customer wants to understand
   what charges or components caused the bill increase.

3. none
   Use when no tool is required.

Examples:

"My bill suddenly doubled"
→ intent = billing_inquiry
→ action = call_tool
→ tool_name = get_customer_bill

"Why did my bill increase?"
→ intent = billing_inquiry
→ action = call_tool
→ tool_name = get_customer_bill

"What caused the extra charges on my bill?"
→ intent = billing_inquiry
→ action = call_tool
→ tool_name = get_bill_breakdown

"Show me the breakdown of my bill"
→ intent = billing_inquiry
→ action = call_tool
→ tool_name = get_bill_breakdown

If action is not call_tool:
→ tool_name = none

"""

    ),
    (
        "human",
        """
Customer ID:
{customer_id}

Customer message:
{message}

Customer language:
{language}
"""
    )
])

tool_decision_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are the decision component of an enterprise
customer-service AI agent.

You have just received the result of a tool call.

Your job is to determine whether the available information
is sufficient to answer the customer's original question.

You MUST choose exactly one next action:

- answer
- get_bill_breakdown
- escalate

Rules:

1. Choose "answer" when the available tool result contains
   enough information to answer the customer's question.

2. Choose "get_bill_breakdown" when the customer is asking
   why their bill increased, what caused extra charges,
   or what charges contributed to the increase, but the
   current tool result does not contain charge-level details.

3. Choose "escalate" only when the customer issue genuinely
   requires human intervention and the Agent plan requires
   escalation.

4. Never invent information.

5. Do not ask the customer whether they want another tool
   to be called when their original request already requires
   that information.

6. If get_customer_bill shows that a bill increased but does
   not explain the cause of the increase, choose:
   get_bill_breakdown

7. If get_bill_breakdown contains the charge components,
   choose:
   answer

Customer message:
{message}

Agent plan:
{plan}

Tool that was executed:
{tool_name}

Tool result:
{tool_result}
"""
        ),
        ("human", "{message}"),
    ]
)

tool_decision = tool_decision_prompt | llm.with_structured_output(
    ToolDecision
)

planner = planner_prompt | llm.with_structured_output(
    AgentDecision
)


def plan_request(state: AgentState):

    decision = planner.invoke({
        "customer_id": state["customer_id"],
        "message": state["message"],
        "language": state["language"]
    })

    print("\n========== PLANNER ==========")
    print("Intent:", decision["intent"])
    print("Action:", decision["action"])
    print("Tool:", decision["tool_name"])
    print("Plan:", decision["plan"])
    print("=============================\n")

    return {
        "intent": decision["intent"],
        "plan": decision["plan"],
        "action": decision["action"],
        "tool_name": decision["tool_name"]
    }


def generate_response(state: AgentState):
    response_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
You are a customer service voice assistant.

Generate ONLY the final response that should be spoken to the customer.

IMPORTANT RULES:

1. Use the Tool result as the source of truth.

2. Never invent information that is not present in the Tool result.

3. Never ask the customer for information that is already present
   in the Tool result.

4. Do not say that you are going to retrieve information if the
   information has already been retrieved.

5. Return plain text only.

6. Never use Markdown.

7. Never use headings, bullet points, numbered lists, asterisks,
   hashtags, backticks, stage directions, or special formatting.

8. Do not insert Markdown separators or formatting symbols.

9. Give a concise, natural response suitable for telephone
   text-to-speech.

10. If the Tool result contains previous_bill and current_bill,
    explicitly explain the change.

11. If the Tool result contains a billing breakdown, explain the
    important charge components clearly.

12. Never change, convert, reinterpret, or assume the currency.

13. Use the currency exactly as provided by the Tool result.

14. If the Tool result says currency is INR, express the amounts
    in Indian rupees.

15. Never convert INR into dollars, euros, pounds, or any other currency.

16. If the Tool result does not contain the reason for a bill increase,
    do not invent a reason.

17. If the Tool provides enough information to answer the question,
    answer the customer directly.

18. Do not escalate the customer unless the Agent plan explicitly
    requires escalation.

19. Do not promise a callback, transfer, specialist, representative,
    or human assistance unless the Agent plan explicitly requires it.

20. Do not invent departments, employees, specialists, policies,
    procedures, or available services.

21. If the Tool result does not contain enough information to answer
    the question, clearly state what information is available and
    what information is missing.

22. Keep the response concise and natural for a voice conversation.

23. The final response should normally be one or two short spoken
    paragraphs.

Customer message:
{message}

Intent:
{intent}

Agent plan:
{plan}

Tool result:
{tool_result}
"""
            ),
            ("human", "{message}"),
        ]
    )
    response_chain = response_prompt | llm

    print("\n========== RESPONSE ==========")
    print("Customer message:", state["message"])
    print("Tool result:", state["tool_result"])

    result = response_chain.invoke(
        {
            "message": state["message"],
            "intent": state["intent"],
            "plan": state["plan"],
            "tool_result": state["tool_result"],
        }
    )

    print("Generated response:", result.content)
    print("==============================\n")

    return {
        "response": result.content,
        "escalate": False,
    }


def escalate_request(state: AgentState):

    return {
        "response": (
            "I understand. I'll connect you with "
            "a customer service representative."
        ),
        "escalate": True
    }

def execute_tool(state: AgentState):

    tool_name = state["tool_name"]
    customer_id = state["customer_id"]

    result = execute_registered_tool(
        tool_name=tool_name,
        customer_id=customer_id,
    )

    print("\n========== TOOL ==========")
    print("Tool:", tool_name)
    print("Customer:", customer_id)
    print("Result:", result)
    print("==========================\n")

    return {
        "tool_result": result
    }

def analyze_tool_result(state: AgentState):

    decision = tool_decision.invoke(
        {
            "message": state["message"],
            "plan": state["plan"],
            "tool_name": state["tool_name"],
            "tool_result": state["tool_result"],
        }
    )

    print("\n========== TOOL DECISION ==========")
    print("Next action:", decision["next_action"])
    print("Reason:", decision["reason"])
    print("===================================\n")

    result = {
        "action": decision["next_action"],
        "plan": decision["reason"],
    }

    if decision["next_action"] == "get_bill_breakdown":
        result["tool_name"] = "get_bill_breakdown"

    return result

def route_after_planner(state: AgentState):

    if state["action"] == "call_tool":
        return "execute_tool"

    if state["action"] == "escalate":
        return "escalate_request"

    return "generate_response"

def route_after_tool_analysis(state: AgentState):

    if state["action"] == "get_bill_breakdown":
        return "execute_tool"

    if state["action"] == "escalate":
        return "escalate_request"

    return "generate_response"

builder = StateGraph(AgentState)

builder.add_node("execute_tool", execute_tool)
builder.add_node("planner", plan_request)
builder.add_node("analyze_tool_result", analyze_tool_result)
builder.add_node("generate_response", generate_response)
builder.add_node("escalate_request", escalate_request)

builder.add_edge(START, "planner")

builder.add_conditional_edges(
    "planner",
    route_after_planner
)

builder.add_edge(
    "execute_tool",
    "analyze_tool_result"
)

builder.add_conditional_edges(
    "analyze_tool_result",
    route_after_tool_analysis
)

builder.add_edge(
    "generate_response",
    END
)

builder.add_edge(
    "escalate_request",
    END
)

graph = builder.compile()