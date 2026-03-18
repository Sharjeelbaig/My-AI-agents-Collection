import os
import sys
from dotenv import load_dotenv
from src.shared.jira_client import jira_client

load_dotenv()


def print_banner():
    """Print welcome banner."""
    print("\n" + "=" * 50)
    print("       JIRA AGENT - Interactive Console")
    print("=" * 50)
    print()


def print_help():
    """Print available commands."""
    print("\nAvailable commands:")
    print("  help          - Show this help message")
    print("  projects      - List available projects")
    print("  status        - Show current workspace status")
    print("  exit/quit     - Exit the agent")
    print("\nNatural language commands:")
    print("  'create a ticket for...'")
    print("  'assign PROJ-123 to Sharjeel Baig'")
    print("  'delete ticket PROJ-123'")
    print("  'show in progress tickets'")
    print("  'show done tickets'")
    print("  'show all tickets'")
    print("  'search for X'")
    print("  'what is the status of PROJ-123'")
    print("  'add comment to PROJ-123: ...'")
    print("  'show comments for PROJ-123'")
    print("  'move PROJ-123 to In Progress/Done'")
    print("\nNote: delete and move commands ask for confirmation before changing Jira.")
    print()


def check_credentials():
    """Check if Jira credentials are configured."""
    if not jira_client.is_configured():
        print("\nERROR: Jira credentials not configured!")
        print("\nPlease set up your .env file with:")
        print("  JIRA_URL=https://yourcompany.atlassian.net")
        print("  JIRA_EMAIL=your-email@example.com")
        print("  JIRA_API_TOKEN=your-api-token")
        print("\nYou can get an API token from:")
        print("  https://id.atlassian.com/manage-profile/security/api-tokens")
        return False
    return True


def select_project():
    """Let user select a project/workspace."""
    print("\nFetching available projects...")
    projects = jira_client.get_projects()

    if not projects:
        print("No projects found or unable to fetch projects.")
        print("Please check your credentials and permissions.")
        return False

    print("\nAvailable Projects:")
    for i, project in enumerate(projects, 1):
        print(f"  {i}. {project.get('key')} - {project.get('name')}")

    while True:
        try:
            choice = input("\nSelect a project number (or 'q' to quit): ").strip()
            if choice.lower() == 'q':
                return False

            index = int(choice) - 1
            if 0 <= index < len(projects):
                selected = projects[index]
                jira_client.set_project(selected.get('key'))
                print(f"\nSelected project: {selected.get('key')} - {selected.get('name')}")
                return True
            else:
                print("Invalid selection. Please try again.")
        except ValueError:
            print("Please enter a valid number.")


def onboarding():
    """Run the onboarding process."""
    print_banner()

    if not check_credentials():
        return False

    if not select_project():
        return False

    return True


def run_agent():
    """Run the interactive agent loop."""
    from src.features.agent.agent import agent

    thread_id = "jira_session"
    print("\nJira Agent is ready! Type 'help' for commands, 'exit' to quit.")
    print("-" * 50)

    while True:
        try:
            user_input = input("\n").strip()

            if not user_input:
                continue

            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\nGoodbye! Thanks for using Jira Agent.")
                break

            if user_input.lower() == 'help':
                print_help()
                continue

            if user_input.lower() == 'projects':
                projects = jira_client.get_projects()
                print("\nAvailable Projects:")
                for p in projects:
                    print(f"  - {p.get('key')}: {p.get('name')}")
                continue

            if user_input.lower() == 'status':
                print(f"\nCurrent Project: {jira_client.project_key}")
                print(f"Jira URL: {jira_client.url}")
                continue

            result = agent.invoke(
                {"messages": [{"role": "user", "content": user_input}]},
                config={"configurable": {"thread_id": thread_id}}
            )
            response = result["messages"][-1].content
            print(f"\n{response}")

        except KeyboardInterrupt:
            print("\n\nInterrupted. Type 'exit' to quit or continue.")
        except Exception as e:
            print(f"\nError: {e}")
            print("Please try again.")


def main():
    """Main entry point."""
    try:
        if onboarding():
            run_agent()
    except KeyboardInterrupt:
        print("\n\nSession ended by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
