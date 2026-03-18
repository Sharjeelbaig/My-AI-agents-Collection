# AI Agents Collection

A comprehensive collection of AI agents built with LangChain, LangGraph, and Ollama, showcasing various functionalities and use cases.

## Overview

This repository contains multiple AI agents that demonstrate different capabilities, from web search to PDF manipulation and voice-controlled interaction. All agents are built using modern AI frameworks and follow best practices for agent development.

## Agents Included

### 1. Search Agent
**Directory**: [`1 - search agent/`](1%20-%20search%20agent/)

A simple yet powerful AI search agent that uses LangChain, LangGraph, and Ollama to answer user questions by searching the web.

#### Features:
- Web search using DuckDuckGo
- LLM integration with Ollama's Qwen2.5:3b model
- Memory capabilities using LangGraph's MemorySaver
- Structured responses with Pydantic schemas

### 2. PDF Agent
**Directory**: [`2 - pdf agent/`](2%20-%20pdf%20agent/)

An AI agent that can read, create, and edit PDF files.

#### Features:
- Read PDF content
- Create new PDF files
- Edit existing PDF files
- LLM integration with Ollama's Qwen2.5:3b model
- Structured responses with Pydantic schemas

### 3. Voice-Controlled Search Agent
**Directory**: [`3 - voice controlled search agent/`](3%20-%20voice%20controlled%20search%20agent/)

A voice-enabled AI search agent that combines speech-to-text with web search capabilities.

#### Features:
- Voice input using Google's Speech Recognition API
- Web search using DuckDuckGo
- LLM integration with Ollama's Qwen2.5:3b model
- Memory capabilities using LangGraph's MemorySaver
- Structured responses with Pydantic schemas

## Core Technologies

All agents are built using the following core technologies:

- **LangChain**: Framework for building AI applications
- **LangGraph**: For building stateful, multi-agent applications
- **Ollama**: Local LLM engine
- **Qwen2.5:3b**: Open-source LLM by Alibaba Cloud
- **uv**: Python package manager and development tool
- **Pydantic**: Data validation and parsing library

## Installation

### Prerequisites

1. Python 3.12 or higher
2. uv (Python package manager)
3. Ollama

### Step-by-Step Installation

1. Install uv:
   ```bash
   pip install uv
   ```

2. Install Ollama:
   - Visit https://ollama.com/
   - Follow the installation instructions for your operating system

3. Pull the Qwen2.5:3b model:
   ```bash
   ollama pull qwen2.5:3b
   ```

4. For each agent, navigate to its directory and install dependencies:
   ```bash
   cd "1 - search agent"
   uv sync
   ```

## Usage

### Search Agent

```bash
cd "1 - search agent"
uv run python main.py
```

### PDF Agent

```bash
cd "2 - pdf agent"
uv run python main.py
```

### Voice-Controlled Search Agent

```bash
cd "3 - voice controlled search agent"
uv run python main.py
```

## Agent Architecture

Each agent follows a similar architecture:

```
agent-folder/
├── main.py                    # Entry point
├── pyproject.toml             # Project metadata and dependencies
├── uv.lock                    # Dependency lock file
├── README.md                  # Agent-specific documentation
└── src/
    ├── configs/
    │   └── llm/
    │       └── llm_config.py  # LLM configuration
    ├── features/
    │   └── agent/
    │       ├── agent.py       # Agent initialization
    │       ├── prompts/
    │       │   └── system_prompt.py  # System prompt
    │       ├── schemas/       # Pydantic schemas for responses
    │       └── tools/         # Agent tools (search, PDF manipulation, etc.)
    └── shared/                # Shared utilities
```

## Customization

### Changing the LLM

Edit `src/configs/llm/llm_config.py` to change the LLM settings:

```python
LLM_CONFIG = {
    "model_name": "qwen2.5:3b",
    "temperature": 0.3,
}
```

### Modifying the System Prompt

Customize the agent's behavior by modifying `src/features/agent/prompts/system_prompt.py`.

### Adding New Tools

Add new tools to `src/features/agent/tools/` and register them in `registry.py`.

## Contributing

Feel free to submit issues or pull requests for improvements.

## License

MIT License
