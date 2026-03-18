# Chain of Thought (CoT)

### What is Chain of Thought?

Chain of Thought is a prompting technique that encourages the LLM to break down complex
problems into intermediate reasoning steps before producing a final answer.

### Without CoT:
```
User: Delete all inactive users
Agent: [Calls delete_rows with table="users", condition="active = false"]
      Deleted 847 rows.   ← No preview, no confirmation, irreversible
```

### With CoT:
```
User: Delete all inactive users
Agent: Let me think through this step by step:
       1. The user wants to delete users marked as inactive
       2. I don't know how many rows that affects — I should check first
       3. I'll run a SELECT COUNT(*) to preview the impact
       4. Then present the count to the user and ask for confirmation
       5. Only delete after explicit confirmation

       [Calls run_query: SELECT COUNT(*) FROM users WHERE active = false]
       Result: 847 rows would be affected.

       ⚠️  This will permanently delete 847 rows from 'users'. Reply 'yes' to confirm.
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
│  "User wants inactive users deleted"         │
│  "I need to know the table structure first"  │
└─────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────┐
│              ACTION (Tool Call)              │
│  describe_table("users")                     │
└─────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────┐
│            OBSERVATION (Result)              │
│  Table has: id, name, email, active (bool)   │
└─────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────┐
│            THOUGHT (Reasoning)               │
│  "Column 'active' is a boolean — good"       │
│  "Now count affected rows before deleting"  │
└─────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────┐
│              ACTION (Tool Call)              │
│  run_query("SELECT COUNT(*) FROM users       │
│             WHERE active = false")           │
└─────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────┐
│            OBSERVATION (Result)              │
│  847 rows match                              │
└─────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────┐
│            ANSWER (Ask Confirmation)         │
│  "847 users are inactive. Delete them?       │
│   Reply 'yes' to confirm."                  │
└─────────────────────────────────────────────┘
```

---

## Decision Framework

| User says...                                        | Agent action                                             |
|-----------------------------------------------------|----------------------------------------------------------|
| "show me all orders"                                | `run_query` directly                                     |
| "delete orders from last month"                     | `run_query` COUNT first → preview → confirm → `delete_rows` |
| "what tables do I have?"                            | `list_tables`                                            |
| "describe the products table"                       | `describe_table`                                         |
| "insert a new product"                              | `insert_row` (confirm if user didn't provide all fields) |
| "update the price of product 42 to 19.99"          | `update_rows` with confirm=false first → confirm         |
| "export all users to CSV"                           | `export_results`                                         |
| "how many rows are in each table?"                  | `get_db_summary`                                         |

---

## Key Differences Summary

| Aspect | Simple Agent | CoT + ReAct Agent |
|--------|--------------|-------------------|
| **Reasoning** | None — direct tool calls | Step-by-step before each action |
| **Destructive ops** | Executes immediately | Previews impact, asks confirmation |
| **Schema awareness** | Assumes column names | Calls describe_table first if uncertain |
| **Error recovery** | Stops on error | Re-evaluates and retries or clarifies |
| **Bulk operations** | One shot | Shows preview count, then confirms |
