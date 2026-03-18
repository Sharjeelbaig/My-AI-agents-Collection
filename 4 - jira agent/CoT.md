# Chain of Thought (CoT)

### What is Chain of Thought?

Chain of Thought is a prompting technique that encourages the LLM to break down complex problems into intermediate reasoning steps before producing a final answer.

### Without CoT:
```
User: Delete the authentication bug ticket
Agent: [Calls delete_ticket with ticket_key="authentication bug ticket"]
      Error: Ticket not found
```

### With CoT:
```
User: Delete the authentication bug ticket
Agent: Let me think through this step by step:
       1. The user wants to delete a ticket about authentication bugs
       2. I don't have the exact ticket key - I need to find it first
       3. I should search for tickets with "authentication" in the summary
       4. Then identify which one is the bug ticket
       5. Finally delete it after confirmation

       [Calls get_all_tickets]
       Found: PROJ-101 "Fix authentication timeout bug"
              PROJ-102 "Add authentication logging"
       The first one matches "authentication bug"

       [Calls delete_ticket with ticket_key="PROJ-101"]
       Ticket PROJ-101 deleted successfully
```

### How to Implement CoT

Add explicit reasoning instructions to your system prompt:

```python
def system_prompt(tools):
    return f"""
You are a helpful Jira assistant that helps users manage their Jira tickets and projects.

## Reasoning Process (Chain of Thought)
Before taking any action, ALWAYS think through the request step by step:
1. What is the user asking me to do?
2. What information do I have? What information do I need?
3. Do I need to gather more information before I can complete the request?
4. What sequence of tool calls will accomplish the goal?
5. What could go wrong and how should I handle it?

## Available Tools
{tools}

## Decision Framework
- If the user provides a ticket KEY (e.g., "PROJ-123"): proceed directly with the operation
- If the user provides a DESCRIPTION or TITLE: first search for matching tickets, then ask for confirmation
- If the user asks to modify MULTIPLE tickets: list all matching tickets first, then proceed one by one with confirmation
- If an operation is DESTRUCTIVE (delete, transition): always confirm before executing

## Output Format
For complex requests, structure your response as:
1. **Reasoning**: Your step-by-step thought process
2. **Actions Taken**: What tools you called and why
3. **Results**: What happened
4. **Next Steps**: If any follow-up is needed
"""
```

---

## ReAct Pattern (Reasoning + Acting)

### What is ReAct?

ReAct combines reasoning and acting in an interleaved manner:
- **Reasoning**: Think about what to do next
- **Acting**: Execute a tool call
- **Observing**: See the result and reason again
- Repeat until goal is achieved

### The ReAct Loop

```
┌─────────────────────────────────────────────┐
│                    START                     │
└─────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────┐
│            THOUGHT (Reasoning)               │
│  "I need to find the authentication bug"     │
│  "First, I should get all tickets"           │
└─────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────┐
│              ACTION (Tool Call)              │
│  get_all_tickets()                          │
└─────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────┐
│            OBSERVATION (Result)              │
│  Found 3 tickets including PROJ-101         │
│  "Fix authentication timeout bug"           │
└─────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────┐
│            THOUGHT (Reasoning)               │
│  "PROJ-101 matches authentication bug"       │
│  "I should delete it after confirming"      │
└─────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────┐
│              ACTION (Tool Call)              │
│  delete_ticket("PROJ-101")                   │
└─────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────┐
│            OBSERVATION (Result)              │
│  "Ticket PROJ-101 deleted successfully"     │
└─────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────┐
│            ANSWER (Final Response)            │
│  "I've deleted the authentication bug        │
│   ticket (PROJ-101)"                         │
└─────────────────────────────────────────────┘
```

### Implementing ReAct in LangChain

LangChain's `create_react_agent` implements this pattern automatically:

```python
from langchain.agents import create_react_agent
from langchain import hub

# Pull the ReAct prompt template
prompt = hub.pull("hwchase17/react")

agent = create_react_agent(
    llm=llm,
    tools=tools,
    prompt=prompt
)
```

The ReAct prompt template includes:
```
Thought: Do I need to use a tool? Yes
Action: [tool name]
Action Input: [tool arguments]
Observation: [tool output]
... (repeat as needed)
Thought: Do I need to use a tool? No
Final Answer: [response to user]
```

---

## Project Structure Refactoring

### Current Structure (Problems)
```
src/features/agent/
├── agent.py
├── tools/
│   ├── registry.py          # All tools in one file
│   └── jira_tools.py        # All tool functions in one file
├── schemas/
│   └── jira_schemas.py      # All schemas in one file
└── prompts/
    └── system_prompt.py
```

### Recommended Structure
```
src/features/agent/
├── agent.py
├── tools/
│   ├── __init__.py
│   ├── registry.py          # Tool registration only
│   ├── create_ticket.py     # Individual tool files
│   ├── delete_ticket.py
│   ├── get_ticket.py
│   ├── get_tickets.py      # Bulk operations
│   ├── search_tickets.py   # JQL search
│   ├── comment_tools.py    # Add/get comments
│   └── transition_ticket.py
├── schemas/
│   ├── __init__.py
│   ├── ticket_schemas.py    # Ticket-related schemas
│   ├── comment_schemas.py   # Comment schemas
│   └── operation_schemas.py # Result schemas
├── prompts/
│   ├── __init__.py
│   ├── system_prompt.py     # Main system prompt with CoT
│   └── react_prompt.py      # ReAct-specific prompt
└── client/
    └── jira_client.py       # API client separation
```

---

## Tool Implementation with CoT Support

### Tool File Structure (Example: search_tickets.py)

```python
# src/features/agent/tools/search_tickets.py

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from typing import Optional
from ..client.jira_client import jira_client


class SearchTicketsInput(BaseModel):
    """Input schema for searching tickets."""
    query: str = Field(
        description="Search query or keywords to find tickets. "
                    "Can be partial ticket summary, description, or keywords."
    )
    status: Optional[str] = Field(
        default=None,
        description="Filter by status: 'To Do', 'In Progress', 'Done', 'Blocked'"
    )


def search_tickets(input_data: SearchTicketsInput) -> str:
    """
    Search for Jira tickets matching the query.

    Use this tool when:
    - User refers to a ticket by title/description instead of key
    - User asks "find tickets about X"
    - You need to resolve a ticket reference before another operation

    Returns a list of matching tickets with their keys.
    """
    # Build JQL query
    jql_parts = [f'project = {jira_client.project_key}']

    # Add text search
    jql_parts.append(f'summary ~ "{input_data.query}" OR description ~ "{input_data.query}"')

    # Add status filter if provided
    if input_data.status:
        jql_parts.append(f'status = "{input_data.status}"')

    jql = " AND ".join(jql_parts)
    tickets = jira_client.search_tickets(jql)

    if not tickets:
        return f"No tickets found matching '{input_data.query}'"

    result = [f"Found {len(tickets)} tickets:\n"]
    for ticket in tickets:
        result.append(f"[{ticket['key']}] {ticket['summary']}")
        result.append(f"  Status: {ticket['status']} | Assignee: {ticket['assignee']}\n")

    return "\n".join(result)


# Export as StructuredTool
search_tickets_tool = StructuredTool(
    name="search_tickets",
    func=lambda x: search_tickets(SearchTicketsInput(**x) if isinstance(x, dict) else x),
    description=(
        "Search for Jira tickets by keywords, title, or description. "
        "Use this when you need to find ticket keys from partial names. "
        "Returns matching tickets with their keys for use in other operations."
    ),
    args_schema=SearchTicketsInput
)


__all__ = ["search_tickets_tool"]
```

### Bulk Operation Tool (Example: bulk_delete.py)

```python
# src/features/agent/tools/bulk_operations.py

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from typing import List, Optional
from ..client.jira_client import jira_client


class BulkDeleteInput(BaseModel):
    """Input schema for bulk delete operations."""
    ticket_keys: List[str] = Field(
        description="List of ticket keys to delete (e.g., ['PROJ-1', 'PROJ-2'])"
    )
    confirm: bool = Field(
        default=False,
        description="Set to true only after user has confirmed the deletion"
    )


def bulk_delete_tickets(input_data: BulkDeleteInput) -> str:
    """
    Delete multiple Jira tickets at once.

    IMPORTANT: Always get user confirmation before using this tool.
    """
    if not input_data.confirm:
        return (
            f"You are about to delete {len(input_data.ticket_keys)} tickets:\n"
            f"{', '.join(input_data.ticket_keys)}\n\n"
            "This action cannot be undone. Please confirm by setting confirm=true."
        )

    results = []
    for key in input_data.ticket_keys:
        result = jira_client.delete_ticket(key)
        if result.get("success"):
            results.append(f"✓ {key}: Deleted")
        else:
            results.append(f"✗ {key}: {result.get('message')}")

    return "\n".join(results)


bulk_delete_tool = StructuredTool(
    name="bulk_delete_tickets",
    func=lambda x: bulk_delete_tickets(BulkDeleteInput(**x) if isinstance(x, dict) else x),
    description=(
        "Delete multiple tickets at once. "
        "REQUIRES: First search and list the tickets, get user confirmation, then call with confirm=true. "
        "Use when user asks to 'delete all X' or 'delete multiple tickets'."
    ),
    args_schema=BulkDeleteInput
)
```

---

## Enhanced System Prompt with CoT + ReAct

```python
# src/features/agent/prompts/system_prompt.py

REACT_SYSTEM_PROMPT = """
You are a helpful Jira assistant that helps users manage their Jira tickets and projects.

## Your Reasoning Capabilities
You use Chain of Thought (CoT) reasoning to break down complex requests into steps.
You use the ReAct pattern: Think -> Act -> Observe -> Repeat until done.

## Available Tools
{tools}

## Tool Names
{tool_names}

## Reasoning Guidelines

### For Single Operations (user provides exact ticket key):
1. Validate you have all required information
2. Execute the tool
3. Report the result

### For Ambiguous Operations (user describes a ticket):
1. **Thought**: "I need to find which ticket the user means"
2. **Action**: Use search_tickets to find matching tickets
3. **Observation**: See the results
4. **Thought**: "X tickets match, I should present options to the user"
5. **Final Answer**: Present the tickets and ask for clarification

### For Bulk Operations (user wants to affect multiple tickets):
1. **Thought**: "User wants to affect multiple tickets, I need to identify them first"
2. **Action**: Use get_all_tickets or search_tickets
3. **Observation**: See matching tickets
4. **Thought**: "I found X tickets. Before proceeding, I need confirmation"
5. **Final Answer**: List the tickets and ask for confirmation
6. (After user confirms) Continue with the operation

### For Destructive Operations (delete, major transitions):
1. Always list what will be affected
2. Ask for explicit confirmation
3. Only proceed after confirmation

## Example Interactions

### Example 1: Ambiguous Reference
User: "Delete the authentication bug ticket"

Thought: The user wants to delete a ticket but didn't provide a ticket key.
        They mentioned "authentication bug" which describes content, not a key.
        I need to search for tickets matching this description first.

Action: search_tickets
Action Input: {{"query": "authentication bug"}}

Observation: Found 2 tickets:
[PROJ-101] Fix authentication timeout bug
[PROJ-102] Add authentication logging for bug tracking

Thought: I found 2 matching tickets. PROJ-101 clearly matches "authentication bug".
        But I should confirm with the user before deleting, since deletion is permanent.

Final Answer: I found 2 tickets matching "authentication bug":
1. [PROJ-101] Fix authentication timeout bug
2. [PROJ-102] Add authentication logging for bug tracking

Which ticket would you like to delete? Please confirm the ticket key.

### Example 2: Bulk Operation
User: "Delete all tickets related to testing"

Thought: User wants to delete multiple tickets. I need to:
        1. Find all testing-related tickets
        2. Show them to the user
        3. Get explicit confirmation before deleting
        This is a destructive operation requiring confirmation.

Action: search_tickets
Action Input: {{"query": "testing"}}

Observation: Found 5 tickets:
[PROJ-201] Unit testing for login
[PROJ-202] Integration testing suite
[PROJ-203] Testing documentation
[PROJ-204] Performance testing
[PROJ-205] E2E testing framework

Thought: I found 5 testing-related tickets. Before proceeding with deletion,
        I must show these to the user and get explicit confirmation.
        This is a destructive action that cannot be undone.

Final Answer: I found 5 tickets related to testing:

1. [PROJ-201] Unit testing for login
2. [PROJ-202] Integration testing suite
3. [PROJ-203] Testing documentation
4. [PROJ-204] Performance testing
5. [PROJ-205] E2E testing framework

⚠️ This will permanently delete all 5 tickets. This action cannot be undone.

Do you want to proceed? Please reply with "yes" to confirm deletion of these tickets.

### Example 3: Direct Operation (key provided)
User: "Get ticket PROJ-123"

Thought: User provided a specific ticket key. I can directly retrieve this ticket.

Action: get_ticket
Action Input: {{"ticket_key": "PROJ-123"}}

Observation: Ticket details retrieved successfully.

Final Answer: [Present ticket details]

## Current Project
You are working with project: {project_key}

Remember: Always think through complex requests, search before acting on descriptions,
and always confirm destructive operations.
"""

def get_system_prompt(tools, tool_names, project_key):
    return REACT_SYSTEM_PROMPT.format(
        tools=tools,
        tool_names=tool_names,
        project_key=project_key
    )
```

---

## Complete Agent Implementation

```python
# src/features/agent/agent.py

from langchain.agents import create_react_agent
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver
from langchain import hub

from src.features.agent.tools.registry import (
    create_ticket,
    delete_ticket,
    get_ticket,
    search_tickets,
    get_all_tickets,
    get_in_progress,
    get_done,
    add_comment,
    get_comments,
    transition_ticket,
    bulk_delete_tickets,
)
from src.features.agent.prompts.system_prompt import get_system_prompt
from src.features.agent.client.jira_client import jira_client
from src.configs.llm.llm_config import LLM_CONFIG

# Initialize LLM
llm = ChatOllama(
    model=LLM_CONFIG["model_name"],
    temperature=LLM_CONFIG["temperature"]
)

# Define all tools
tools = [
    create_ticket,
    delete_ticket,
    get_ticket,
    search_tickets,
    get_all_tickets,
    get_in_progress,
    get_done,
    add_comment,
    get_comments,
    transition_ticket,
    bulk_delete_tickets,
]

# Get tool names
tool_names = [t.name for t in tools]

# Pull the ReAct prompt template (or use custom)
prompt = hub.pull("hwchase17/react")

# Or use custom prompt with CoT instructions
# prompt = get_system_prompt(tools, tool_names, jira_client.project_key)

# Create the ReAct agent
agent = create_react_agent(
    model=llm,
    tools=tools,
    prompt=prompt,
    checkpointer=MemorySaver()
)

__all__ = ["agent"]
```

---

## Key Differences Summary

| Aspect | Simple Agent | CoT + ReAct Agent |
|--------|--------------|-------------------|
| **Reasoning** | None - direct tool calls | Step-by-step reasoning before each action |
| **Ambiguity Handling** | Fails or guesses | Searches first, presents options |
| **Bulk Operations** | One ticket at a time | Identifies all, confirms, then acts |
| **Error Recovery** | Stops on error | Re-evaluates and tries alternatives |
| **User Confirmation** | Optional | Required for destructive operations |
| **File Structure** | Monolithic | Modular (one file per tool) |

---

## Testing Your Agent

### Test Cases for CoT + ReAct

1. **Direct Key Reference**: "Delete ticket PROJ-123"
   - Should proceed directly with confirmation

2. **Description Reference**: "Delete the login bug"
   - Should search first, show matches, ask for confirmation

3. **Bulk Operation**: "Delete all testing tickets"
   - Should list all matches, ask for explicit confirmation

4. **Ambiguous Request**: "Move that ticket to done"
   - Should ask: "Which ticket?"

5. **Multi-step Operation**: "Close all done tickets older than 30 days"
   - Should reason: find tickets, filter by date, confirm, then execute

---

## Next Steps

1. Refactor tools into separate files
2. Refactor schemas into separate files
3. Add `search_tickets` tool for resolving title-to-key
4. Add `bulk_delete_tickets` tool for bulk operations
5. Add confirmation workflow for destructive operations
6. Update system prompt with CoT + ReAct instructions
7. Switch to `create_react_agent` from `create_agent`
8. Add comprehensive error handling
9. Add logging for debugging reasoning steps