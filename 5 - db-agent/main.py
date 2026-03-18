import os
import sys
from dotenv import load_dotenv
from src.shared.db_client import db_client
from rich.console import Console
from rich.markdown import Markdown

load_dotenv()

console = Console()


def print_banner():
    print("\n" + "=" * 50)
    print("       DB AGENT - Interactive Console")
    print("=" * 50)
    print()


def print_help():
    print("\nAvailable commands:")
    print("  help          - Show this help message")
    print("  status        - Show current database connection")
    print("  exit/quit     - Exit the agent")
    print("\nNatural language commands:")
    print("  'what tables do I have?'")
    print("  'describe the users table'")
    print("  'show me the full schema'")
    print("  'show all orders where status = pending'")
    print("  'insert a new user: name=Alice, email=alice@example.com'")
    print("  'update order 42 status to shipped'")
    print("  'delete all test users'  (will ask for confirmation)")
    print("  'export all products to CSV'")
    print("  'how many rows are in each table?'")
    print()


def check_connection():
    ok, msg = db_client.test_connection()
    if not ok:
        print(f"\nERROR: Cannot connect to database.\n{msg}")
        print("\nCheck your DB_URL in .env:")
        print("  DB_URL=sqlite:///./database.db")
        print("  DB_URL=postgresql://user:password@localhost:5432/mydb")
        return False
    return True


def run_agent():
    from src.features.agent.agent import agent

    thread_id = "db_session"
    print("\nDB Agent is ready! Type 'help' for commands, 'exit' to quit.")
    print(f"Connected to: {db_client.db_url}")
    print("-" * 50)

    while True:
        try:
            user_input = input("\n> ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit", "q"]:
                print("\nGoodbye!")
                break

            if user_input.lower() == "help":
                print_help()
                continue

            if user_input.lower() == "status":
                ok, msg = db_client.test_connection()
                print(f"\nDatabase URL : {db_client.db_url}")
                print(f"Connection   : {'✅ OK' if ok else f'❌ {msg}'}")
                tables = db_client.list_tables()
                print(f"Tables found : {len(tables)}")
                continue

            result = agent.invoke(
                {"messages": [{"role": "user", "content": user_input}]},
                config={"configurable": {"thread_id": thread_id}},
            )
            response = result["messages"][-1].content
            print()
            console.print(Markdown(response))

        except KeyboardInterrupt:
            print("\n\nInterrupted. Type 'exit' to quit or continue.")
        except Exception as e:
            print(f"\nError: {e}")
            print("Please try again.")


def main():
    try:
        print_banner()
        if check_connection():
            run_agent()
    except KeyboardInterrupt:
        print("\n\nSession ended by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
