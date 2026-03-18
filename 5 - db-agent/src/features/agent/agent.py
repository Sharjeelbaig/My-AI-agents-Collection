from langchain.agents import create_agent
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver

from src.features.agent.tools.registry import tools, tool_names
from src.features.agent.prompts.system_prompt import system_prompt
from src.configs.llm.llm_config import LLM_CONFIG

llm = ChatOllama(
    model=LLM_CONFIG["model_name"],
    temperature=LLM_CONFIG["temperature"],
)

agent = create_agent(
    model=llm,
    tools=tools,
    checkpointer=MemorySaver(),
    system_prompt=system_prompt(tool_names),
)

__all__ = ["agent"]
