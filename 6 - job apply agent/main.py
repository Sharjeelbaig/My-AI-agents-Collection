"""Interactive CLI for the job-apply agent.

Mirrors the convention of the other agents in this repo: an interactive
prompt where the user types natural-language requests; the LLM picks the
right tool; the tools do the deterministic work.
"""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv

load_dotenv()


HELP = """
Available commands:
  help              Show this help
  status            Show profile / tracker status
  history           List recent applications from the tracker
  exit / quit       Exit the agent

Natural language commands:
  'load my profile from profile.yaml with resume resume.pdf'
  'find senior frontend engineer roles in remote'
  'apply to backend python roles, dry run, max 5'
  'apply to senior react roles and actually submit them'
  'show me the description of greenhouse:stripe:1234567'
  'what fields are on the form for lever:figma:abc-def'
  'list my applications'

Defaults:
  * Dry-run mode is on by default. The agent will fill forms but NOT
    submit them. Add 'and submit' to the request to actually apply.
  * Boards searched are read from GREENHOUSE_BOARDS / LEVER_BOARDS /
    ASHBY_BOARDS env vars (comma-separated company slugs).
"""


def banner():
    print("\n" + "=" * 60)
    print("       JOB APPLY AGENT - Interactive Console")
    print("       (99% deterministic tools, 1% LLM)")
    print("=" * 60 + "\n")


def status() -> str:
    from src.shared import state, tracker_db

    profile_path = os.getenv("JOB_AGENT_PROFILE", "profile.yaml")
    db_path = os.getenv("JOB_AGENT_DB", "applications.db")
    has = state.has_profile()
    name = ""
    if has:
        p = state.get_profile()
        name = p.basics.full_name or f"{p.basics.first_name} {p.basics.last_name}".strip()
    rows = tracker_db.list_recent(limit=5)
    return (
        f"Profile loaded: {has}{' (' + name + ')' if name else ''}\n"
        f"Profile path:   {profile_path}\n"
        f"Tracker DB:     {db_path}\n"
        f"Run mode:       {os.getenv('JOB_AGENT_MODE', 'dry_run')}\n"
        f"Recent records: {len(rows)}"
    )


def run():
    from src.features.agent.agent import agent

    thread_id = "job-apply-session"
    print("Type 'help' for commands, 'exit' to quit.")
    print("-" * 60)

    while True:
        try:
            text = input("\n> ").strip()
        except EOFError:
            print()
            break
        if not text:
            continue
        low = text.lower()
        if low in {"exit", "quit", "q"}:
            print("Goodbye.")
            return
        if low == "help":
            print(HELP)
            continue
        if low == "status":
            print(status())
            continue
        if low == "history":
            from src.features.agent.tools.tracker import list_applications_func

            print(list_applications_func())
            continue

        try:
            result = agent.invoke(
                {"messages": [{"role": "user", "content": text}]},
                config={"configurable": {"thread_id": thread_id}},
            )
            response = result["messages"][-1].content
            print(f"\n{response}")
        except KeyboardInterrupt:
            print("\nInterrupted.")
        except Exception as e:
            print(f"\nError: {e}")


def main():
    banner()
    try:
        run()
    except KeyboardInterrupt:
        print("\nSession ended by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
