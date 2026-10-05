from fastapi import FastAPI
from pydantic import BaseModel

from app.graph import graph


app = FastAPI(
    title="Genesys LangGraph Agent",
    version="0.1.0"
)


class AgentRequest(BaseModel):
    conversation_id: str
    customer_id: str = ""
    message: str
    language: str = "en"


class AgentResponse(BaseModel):
    response: str
    intent: str
    confidence: float
    escalate: bool


@app.get("/health")
async def health():
    return {
        "status": "healthy"
    }


@app.post("/agent", response_model=AgentResponse)
async def agent(request: AgentRequest):

    result = await graph.ainvoke({
    "conversation_id": request.conversation_id,
    "customer_id": request.customer_id,
    "message": request.message,
    "language": request.language,
    "intent": "",
    "confidence": 0.0,
    "response": "",
    "escalate": False,
    "plan": "",
    "action": "",
    "tool_result": {}
})

    return {
        "response": result["response"],
        "intent": result["intent"],
        "confidence": result["confidence"],
        "escalate": result["escalate"]
    }