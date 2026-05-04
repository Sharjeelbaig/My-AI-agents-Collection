"""The 1% AI surface.

Exactly two narrow decision functions are exposed here. Everything else in
the agent is deterministic Python.

Both functions take a small, fully-formed prompt and return a string. The
provider is selected by env var ``JOB_AGENT_LLM_PROVIDER`` (ollama | openai |
anthropic). Ollama is the default to match the rest of the repo.
"""

from __future__ import annotations

from src.configs.llm.llm_config import LLM_CONFIG


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


def chat(system: str, user: str) -> str:
    """One-shot chat. Used by score_match and answer_open_question."""
    model = _make_chat_model()
    response = model.invoke(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
    )
    content = getattr(response, "content", response)
    if isinstance(content, list):
        return "".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in content
        ).strip()
    return str(content).strip()


__all__ = ["chat"]
