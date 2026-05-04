"""LangChain agent wrapper.

The orchestrator LLM here is intentionally minimal: it routes the user's
natural-language request to the correct tool. All the heavy lifting happens
inside the tools, which are pure deterministic Python except for the two
narrow decision points (job-fit scoring and free-text answers).
"""

from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver

from src.configs.llm.llm_config import LLM_CONFIG
from src.features.agent.prompts.system_prompt import system_prompt
from src.features.agent.tools.registry import tool_names, tools


def _make_chat_model():
    provider = LLM_CONFIG["provider"]
    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=LLM_CONFIG["openai_model"],
            temperature=LLM_CONFIG["temperature"],
        )
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=LLM_CONFIG["anthropic_model"],
            temperature=LLM_CONFIG["temperature"],
        )

    from langchain_ollama import ChatOllama

    return ChatOllama(
        model=LLM_CONFIG["model_name"],
        temperature=LLM_CONFIG["temperature"],
    )


llm = _make_chat_model()

agent = create_agent(
    model=llm,
    tools=tools,
    checkpointer=MemorySaver(),
    system_prompt=system_prompt(tool_names),
)


__all__ = ["agent"]
