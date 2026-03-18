from langchain_core.tools import Tool
from .web_search import search_web

search_tool = Tool(
    name="web_search",
    func=search_web,
    description="A tool to search the web for information."
)

__all__ = ["search_tool"]