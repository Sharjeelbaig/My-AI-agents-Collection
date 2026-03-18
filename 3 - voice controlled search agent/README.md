# Voice-Controlled Search Agent Project

A simple yet powerful AI search agent that uses LangChain, LangGraph, and Ollama to answer user questions by searching the web, with support for voice input via speech-to-text.

## Features

- **Voice Input**: Converts spoken language to text using Google's Speech Recognition API
- **Web Search**: Uses DuckDuckGo to search for relevant information
- **LLM Integration**: Powered by Ollama's Qwen2.5:3b model
- **Memory Capabilities**: Maintains conversation context using LangGraph's MemorySaver
- **Agent Architecture**: Built with LangChain's agent framework
- **Structured Responses**: Defines schemas for web search results

## Project Structure

```
1-search-agent/
├── main.py                    # Entry point with voice input support
├── pyproject.toml             # Project metadata and dependencies
├── uv.lock                    # Dependency lock file
├── README.md                  # This file
└── src/
    ├── configs/
    │   └── llm/
    │       └── llm_config.py  # LLM configuration
    ├── features/
    │   ├── agent/
    │   │   ├── agent.py       # Agent initialization
    │   │   ├── prompts/
    │   │   │   └── system_prompt.py  # System prompt for the agent
    │   │   ├── schemas/
    │   │   │   └── web_result_list.py  # Pydantic schemas for search results
    │   │   └── tools/
    │   │       ├── registry.py       # Tool registry
    │   │       └── web_search.py     # Web search tool implementation
    │   └── speech_to_text/
    │       └── speech_to_text.py  # Speech-to-text functionality
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
6. **Speech-to-Text Requirements**:
   - The speech-to-text functionality requires a working microphone
   - For some systems, you may need to install additional audio dependencies:
     - **macOS**: No additional installation needed (built-in microphone support)
     - **Linux**: Install PortAudio: `sudo apt-get install portaudio19-dev python3-pyaudio`
     - **Windows**: Install PyAudio via pip or download precompiled binaries

Note: The speech-to-text feature uses Google's Speech Recognition API, which requires an internet connection.

## Usage

### Running the Agent

To run the voice-controlled search agent:

```bash
uv run python main.py
```

The agent will:
1. Listen for your voice input using the microphone
2. Convert your speech to text
3. Search the web for relevant information
4. Use the LLM to generate an answer
5. Print the answer to the console

### Example Interaction

```
Listening... Speak now.
[You say: "Who is the president of the United States?"]
Processing speech...
Recognized: Who is the president of the United States?

Answer: As of [current year], the president of the United States is [name].
```

### Customizing the Agent

If you want to use text input instead of voice, you can modify `main.py`:

```python
from src.features.agent.agent import agent

# Use text input instead of voice
user_question = "Your custom question here"

if user_question:
    result = agent.invoke({
        "messages": [{"role": "user", "content": user_question}]
    }, config={"configurable": {"thread_id": "thread1"}})
    print(f"\nAnswer: {result['messages'][-1].content}")
else:
    print("No valid input received. Please try again.")
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

### Speech-to-Text Module

The voice input functionality is provided by `src/features/speech_to_text/speech_to_text.py` which uses the `speech_recognition` library with Google's Speech Recognition API. Key features:
- Real-time microphone input
- Noise reduction
- Error handling for timeout, unknown speech, and API errors
- Adjustable listening parameters

## Technologies Used

- **LangChain**: Framework for building AI applications
- **LangGraph**: For building stateful, multi-agent applications
- **Ollama**: Local LLM engine
- **Qwen2.5:3b**: Open-source LLM by Alibaba Cloud
- **DuckDuckGo**: Privacy-focused search engine
- **uv**: Python package manager and development tool
- **Pydantic**: Data validation and parsing library
- **SpeechRecognition**: Library for speech-to-text conversion
- **PyAudio**: Audio input/output library (required by SpeechRecognition)

## Contributing

Feel free to submit issues or pull requests for improvements.

## License

MIT License (or specify your license here)