# Job Apply Agent

> Tool-heavy job application agent. ~99% of the work is deterministic Python
> (parse the resume, search ATS boards, discover form fields, map them to
> profile values, fill the form with Playwright, log results). The LLM is
> only consulted at two narrow decision points: when the deterministic
> skill-overlap heuristic is ambiguous, and when a form has a free-text
> question that needs a one-paragraph answer.

## Why this design

Most "AI job apply" agents ask the LLM to drive every step — search, decide,
fill, click. That's slow, expensive, brittle, and hard to debug. This agent
inverts the ratio: a small system prompt tells the LLM "pick the right tool
and pass the args," and the tools do everything else with plain HTTP calls,
HTML parsing, and Playwright. Two LLM-using tools are isolated to a single
file each so you can audit (or replace) the AI surface in seconds.

## Architecture

```
main.py                          Interactive CLI (mirrors the other agents in this repo)
src/
├── configs/llm/llm_config.py    Picks the chat model (Ollama default, OpenAI / Anthropic optional)
├── features/agent/
│   ├── agent.py                 LangChain create_agent wrapper — purely a tool router
│   ├── prompts/system_prompt.py Tells the LLM "use the tools, do not improvise"
│   ├── schemas/                 Pydantic schemas (Profile, JobListing, FormField, tool inputs)
│   └── tools/                   StructuredTool definitions for the agent
└── shared/
    ├── boards/                  Adapters for Greenhouse / Lever / Ashby
    ├── browser.py               Playwright wrapper (lazy-loaded)
    ├── field_aliases.py         Ordered alias table — the brain of the field mapper
    ├── field_mapper.py          Deterministic FormField -> profile-value resolver
    ├── llm.py                   The 1% LLM surface — exactly one chat() helper
    ├── profile_parser.py        YAML loader + best-effort PDF enrichment
    ├── state.py                 Process-local cache for the loaded profile
    └── tracker_db.py            SQLite tracker: seen / matched / dry_run / applied / skipped
```

### Where the LLM is and isn't

| Layer        | LLM? | Notes                                                    |
|--------------|:----:|----------------------------------------------------------|
| Tool routing | yes  | One call per turn, just to pick a tool from the registry |
| `score_match`| sometimes | Only when the skill-overlap heuristic is in [0.25, 0.65] |
| `answer_open_question` | yes | Free-text questions only; profile-grounded |
| Everything else | no | HTTP / HTML / SQLite / Playwright |

## Tools

Tools are registered in
[`src/features/agent/tools/registry.py`](src/features/agent/tools/registry.py).

| Tool | What it does | Uses LLM? |
|------|--------------|:---------:|
| `load_profile` | Load YAML profile, optionally enrich from a resume PDF | no |
| `search_jobs` | Query Greenhouse / Lever / Ashby for matching jobs | no |
| `get_job_details` | Fetch full description + apply URL for one job | no |
| `discover_form` | Return the application form's normalised fields | no |
| `score_match` | Score candidate / job fit (0..1) | maybe |
| `map_fields` | Deterministically map fields to profile values | no |
| `answer_open_question` | Write a short answer for a free-text field | yes |
| `fill_form` | Open the form in headless Chromium and fill every field | no |
| `submit_application` | Click submit (only when `confirm=True`) | no |
| `log_application` | Record the result in SQLite | no |
| `list_applications` | Show the recent tracker entries | no |
| `run_pipeline` | End-to-end orchestrator — what the LLM normally calls | indirectly |

## Setup

```bash
cd "6 - job apply agent"
uv sync
uv run playwright install chromium
cp .env.example .env
cp profile.example.yaml profile.yaml
# Edit profile.yaml with your details. Place resume.pdf next to it.
```

### Configure boards

Set comma-separated company slugs for each ATS in `.env`:

```bash
GREENHOUSE_BOARDS=stripe,airbnb,figma
LEVER_BOARDS=netflix,shopify
ASHBY_BOARDS=ramp,linear,vercel
```

Slugs are the path segments in the public board URLs, e.g.
`https://boards.greenhouse.io/stripe` -> `stripe`.

### Pick an LLM

`JOB_AGENT_LLM_PROVIDER` selects which model is used for the 1% AI calls.

* `ollama` (default): local, free. Pull a model first: `ollama pull qwen2.5:3b`.
* `openai`: install with `uv sync --extra openai` and set `OPENAI_API_KEY`.
* `anthropic`: install with `uv sync --extra anthropic` and set `ANTHROPIC_API_KEY`.

## Usage

```bash
uv run python main.py
```

Then talk to it in natural language:

```
> load my profile

> find senior react engineer roles, remote, max 5

> apply to senior react engineer roles, remote, max 5
```

By default the agent runs in **dry-run mode**: every form is filled in a
headless browser but submit is never clicked. The tracker records each
filled application as `dry_run` so subsequent runs skip them.

To actually submit:

```
> apply to senior react engineer roles, remote, max 3, and submit
```

You can also call individual tools (the agent will route to the right one):

```
> show me the description of greenhouse:stripe:1234567

> what fields are on the form for lever:figma:abc-def

> list my applications
```

## Tracker

Application state is stored in SQLite at `JOB_AGENT_DB` (default
`applications.db`). Each row is keyed by `board:company:job_id`. Statuses:

* `seen` — listed but not yet considered
* `matched` — passed the score filter
* `dry_run` — form was filled but not submitted
* `applied` — submit was clicked successfully
* `skipped` — score below threshold or already processed
* `error` — something went wrong; see `notes`

## Adding a new ATS

1. Create `src/shared/boards/<name>.py` extending `BoardAdapter`.
2. Implement `list_jobs`, `get_details`, `discover_form`, and
   `fill_and_submit`.
3. Register the adapter in `src/shared/boards/__init__.py`.

That's it — the rest of the pipeline is generic.

## Tests

```bash
uv run pytest -q
```

The default suite covers the deterministic core (field mapper + profile
loader). It does NOT touch the network, the browser, or the LLM.

## Limitations

* LinkedIn / Workday / Indeed are not supported. They are aggressively
  bot-detected and the right way to apply there is by hand.
* The form-fill heuristics target the standard Greenhouse / Lever / Ashby
  layouts — heavily customised forms may need their selectors tweaked.
* Free-text answers are profile-grounded but you should review them before
  letting the agent submit.

## License

MIT (matches the rest of the repo).
