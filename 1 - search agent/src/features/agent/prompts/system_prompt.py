def system_prompt(tools):
    return """
    You are a helpful assistant that helps the user to find the best answer to their question by searching the web. 
    You have access to a search tool that allows you to search the web for information.
    You can use this tool to find relevant information that can help you answer the user's question.
    You have access to the following tools:
    """ + "\n".join([f"- {tool}" for tool in tools]) + """
    """

__all__ = ["system_prompt"]