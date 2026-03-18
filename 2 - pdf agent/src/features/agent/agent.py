from langchain.agents import create_agent
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver
from src.features.agent.tools.registry import create_pdf_tool, read_pdf_tool, edit_pdf_tool
from src.config.llm_config import llm_config
from src.features.agent.prompts.system_prompt import system_prompt

llm = ChatOllama(model=llm_config["model_name"], temperature=llm_config["temperature"])
tools_names =[create_pdf_tool.name, read_pdf_tool.name, edit_pdf_tool.name]

agent = create_agent(model=llm,
                     tools=[create_pdf_tool, read_pdf_tool, edit_pdf_tool],
                     checkpointer=MemorySaver(),
                     system_prompt=system_prompt(tools_names)
                     )

__all__ = ["agent"]