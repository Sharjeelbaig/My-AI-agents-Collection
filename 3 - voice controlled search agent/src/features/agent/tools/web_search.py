from langchain_community.tools import DuckDuckGoSearchRun
def search_web(query: str) -> str:
    # code to search the web and return the results
    search = DuckDuckGoSearchRun()
    results = search.run(query)
    return results
    

__all__ = ["search_web"]