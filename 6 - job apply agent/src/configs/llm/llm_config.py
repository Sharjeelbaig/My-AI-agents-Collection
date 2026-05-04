import os
from dotenv import load_dotenv

load_dotenv()

LLM_CONFIG = {
    "provider": os.getenv("JOB_AGENT_LLM_PROVIDER", "ollama").lower(),
    "model_name": os.getenv("LLM_MODEL", "qwen2.5:3b"),
    "temperature": float(os.getenv("LLM_TEMPERATURE", "0.2")),
    "openai_model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    "anthropic_model": os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-latest"),
}

__all__ = ["LLM_CONFIG"]
