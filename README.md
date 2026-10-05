uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

ngrok http 8000 --domain=abc.com

$env:ANTHROPIC_API_KEY = "sk-ant-3333333"


                    ┌──────────────────┐
                    │   Genesys Cloud  │
                    │    Architect     │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │     FastAPI      │
                    │   /agent         │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │    LangGraph     │
                    │ Agentic Reasoning│
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │   MCP Client     │
                    └────────┬─────────┘
                             │ MCP
                             ▼
              ┌────────────────────────────┐
              │    Billing MCP Server      │
              ├────────────────────────────┤
              │ get_customer_bill          │
              │ get_bill_breakdown         │
              └────────────────────────────┘
			        ↓
                     Generate Response
                             ↓
                         Genesys TTS
                             ↓
                          Customer