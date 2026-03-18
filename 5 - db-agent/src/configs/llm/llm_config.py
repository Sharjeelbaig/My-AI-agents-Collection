import os
from dotenv import load_dotenv

load_dotenv()

LLM_CONFIG = {
    "model_name": os.getenv("LLM_MODEL", "qwen2.5:3b"),
    "temperature": float(os.getenv("LLM_TEMPERATURE", "0.3")),
}

__all__ = ["LLM_CONFIG"]
