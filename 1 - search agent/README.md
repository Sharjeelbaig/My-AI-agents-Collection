# Search Agent Project

A simple yet powerful AI search agent that uses LangChain, LangGraph, and Ollama to answer user questions by searching the web.

## Features

- **Web Search**: Uses DuckDuckGo to search for relevant information
- **LLM Integration**: Powered by Ollama's Qwen2.5:3b model
- **Memory Capabilities**: Maintains conversation context using LangGraph's MemorySaver
- **Agent Architecture**: Built with LangChain's agent framework
- **Structured Responses**: Defines schemas for web search results

## Project Structure

```
1-search-agent/
├── main.py                    # Entry point for testing the agent
├── pyproject.toml             # Project metadata and dependencies
├── uv.lock                    # Dependency lock file
├── README.md                  # This file
└── src/
    ├── configs/
    │   └── llm/
    │       └── llm_config.py  # LLM configuration
    ├── features/
    │   └── agent/
    │       ├── agent.py       # Agent initialization
    │       ├── prompts/
    │       │   └── system_prompt.py  # System prompt for the agent
    │       ├── schemas/
    │       │   └── web_result_list.py  # Pydantic schemas for search results
    │       └── tools/
    │           ├── registry.py       # Tool registry
    │           └── web_search.py     # Web search tool implementation
    └── shared/                # Shared utilities (not implemented yet)
```

## Installation

1. Make sure you have Python 3.12 or higher installed
2. Install uv (a Python package manager):
   ```bash
   pip install uv
   ```
3. Install project dependencies:
   ```bash
   uv sync
   ```
4. Install Ollama:
   - Visit https://ollama.com/
   - Follow the installation instructions for your operating system
5. Pull the Qwen2.5:3b model:
   ```bash
   ollama pull qwen2.5:3b
   ```

## Usage

### Running the Agent

To test the agent, run:

```bash
uv run python main.py
```

This will ask the question: "Who is the latest supreme leader of Iran? (one word answer only)" and print the response.

### Customizing the Query

Edit `main.py` to change the query:

```python
result = agent.invoke({
    "messages": [{"role": "user", "content": "Your custom question here"}]
}, config={"configurable": {"thread_id": "thread1"}})
print(result["messages"][-1].content)
```

## Configuration

### LLM Settings

Edit `src/configs/llm/llm_config.py` to change the LLM settings:

```python
LLM_CONFIG = {
    "model_name": "qwen2.5:3b",
    "temperature": 0.3,
}
```

### System Prompt

Customize the agent's behavior by modifying `src/features/agent/prompts/system_prompt.py`.

## Architecture

### Agent Initialization

The agent is created in `src/features/agent/agent.py` using LangChain's `create_agent` function. It combines:
- The Qwen2.5:3b LLM from Ollama
- The web search tool
- A system prompt
- Memory management

### Web Search Tool

The search functionality is implemented in `src/features/agent/tools/web_search.py` using DuckDuckGoSearchRun from LangChain Community.

## Technologies Used

- **LangChain**: Framework for building AI applications
- **LangGraph**: For building stateful, multi-agent applications
- **Ollama**: Local LLM engine
- **Qwen2.5:3b**: Open-source LLM by Alibaba Cloud
- **DuckDuckGo**: Privacy-focused search engine
- **uv**: Python package manager and development tool
- **Pydantic**: Data validation and parsing library

## Contributing

Feel free to submit issues or pull requests for improvements.

## License

MIT License (or specify your license here)