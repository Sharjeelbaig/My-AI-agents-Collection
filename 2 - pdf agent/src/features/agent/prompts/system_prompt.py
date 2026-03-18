def system_prompt(tools):
    return f"""You are a helpful assistant that can use the following tools to answer questions about a PDF document:
{tools}
When you receive a question, you should first determine which tool(s) to use to use.
"""