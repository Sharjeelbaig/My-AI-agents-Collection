from langchain.agents import create_agent
from src.features.agent.prompts.system_prompt import system_prompt
from src.features.agent.tools.registry import search_tool
from src.configs.llm.llm_config import LLM_CONFIG
from langgraph.checkpoint.memory import MemorySaver
from langchain_ollama import ChatOllama

checkpoint = MemorySaver()

llm = ChatOllama(model=LLM_CONFIG["model_name"], temperature=LLM_CONFIG["temperature"])
tool_names = [search_tool.name]
agent = create_agent(
    tools=[search_tool],
    model=llm,
    system_prompt=system_prompt([search_tool.name]),
    checkpointer=checkpoint
)

__all__ = ["agent"]