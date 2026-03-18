# Database Agent

A natural-language AI agent for managing SQL databases (PostgreSQL / SQLite), built with LangChain, LangGraph, and a local Ollama LLM.

## Features

- Query tables with plain English
- List and describe tables and schema
- Insert, update, and delete rows with confirmation guards
- Bulk operations with preview-before-execute
- Export query results to CSV
- Chain of Thought reasoning for complex operations
- ReAct loop for multi-step workflows

## Setup

### 1. Install dependencies

```bash
uv sync
# or
pip install -e .
```

### 2. Configure environment

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

```env
# SQLite (default, no extra setup required)
DB_URL=sqlite:///./database.db

# PostgreSQL
# DB_URL=postgresql://user:password@localhost:5432/mydb

# Ollama model
LLM_MODEL=qwen2.5:3b
LLM_TEMPERATURE=0.3
```

### 3. Start Ollama

```bash
ollama run qwen2.5:3b
```

### 4. Run the agent

```bash
python main.py
```

## Example Interactions

```
> show all tables
> describe the users table
> show all orders from last week where amount > 500
> insert a new user: name=Alice, email=alice@example.com
> delete all test users (confirm required)
> update the status of order 42 to 'shipped'
> export the results of: SELECT * FROM products WHERE stock < 10
```

## Project Structure

```
src/
├── features/agent/
│   ├── agent.py
│   ├── tools/          # one file per tool
│   ├── schemas/        # pydantic input schemas
│   └── prompts/        # system_prompt.py with CoT + ReAct
├── shared/
│   └── db_client.py    # SQLAlchemy client
└── configs/llm/
    └── llm_config.py
tests/
main.py
```

## Available Tools

| Tool | Description |
|------|-------------|
| `list_tables` | List all tables in the database |
| `describe_table` | Show columns, types, and constraints for a table |
| `get_schema` | Full schema dump for all tables |
| `run_query` | Execute a read-only SELECT query |
| `insert_row` | Insert a single row into a table |
| `update_rows` | Update rows matching a condition |
| `delete_rows` | Delete rows matching a condition (requires confirmation) |
| `export_results` | Run a SELECT and export results to CSV |
| `get_db_summary` | High-level overview of all tables and row counts |
