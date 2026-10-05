import os

from langchain_anthropic import ChatAnthropic


def get_llm():
    provider = os.getenv("LLM_PROVIDER", "anthropic")

    if provider == "anthropic":
        return ChatAnthropic(
            model=os.getenv(
                "LLM_MODEL",
                "claude-sonnet-4-5"
            ),
            temperature=0
        )

    raise ValueError(
        f"Unsupported LLM provider: {provider}"
    )