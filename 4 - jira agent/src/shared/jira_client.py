import os
import requests
from typing import Optional, List, Dict, Any, Tuple
from dotenv import load_dotenv

load_dotenv()


class JiraClient:
    """Jira API client for interacting with Jira workspaces."""

    def __init__(self):
        self.url = os.getenv("JIRA_URL", "")
        self.email = os.getenv("JIRA_EMAIL", "")
        self.api_token = os.getenv("JIRA_API_TOKEN", "")
        self.project_key = ""
        self.session = requests.Session()
        if self.email and self.api_token:
            self.session.auth = (self.email, self.api_token)
        self.session.headers.update({"Accept": "application/json"})

    def is_configured(self) -> bool:
        """Check if Jira credentials are configured."""
        return bool(self.url and self.email and self.api_token)

    def ensure_configured(self) -> Tuple[bool, str]:
        """Return whether Jira credentials are configured and a user-facing message."""
        if self.is_configured():
            return True, ""
        return False, "Jira credentials are not configured."

    def ensure_project_selected(self) -> Tuple[bool, str]:
        """Return whether a Jira project is selected and a user-facing message."""
        if self.project_key:
            return True, ""
        return False, "No project selected. Please choose a Jira project first."

    @staticmethod
    def escape_jql_value(value: str) -> str:
        """Escape user text before interpolating it into a JQL string literal."""
        return (
            value.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\r", " ")
            .replace("\n", " ")
            .strip()
        )

    def set_project(self, project_key: str):
        """Set the current project key."""
        self.project_key = project_key

    def get_projects(self) -> List[Dict[str, Any]]:
        """Get all projects accessible by the user."""
        ok, _ = self.ensure_configured()
        if not ok:
            return []

        try:
            response = self.session.get(f"{self.url}/rest/api/3/project")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching projects: {e}")
            return []

    def get_project_issue_types(self) -> List[str]:
        """Get valid issue type names for the current project."""
        ok, _ = self.ensure_configured()
        if not ok:
            return ["Task"]

        ok, _ = self.ensure_project_selected()
        if not ok:
            return ["Task"]

        try:
            resp = self.session.get(
                f"{self.url}/rest/api/3/issue/createmeta",
                params={"projectKeys": self.project_key, "expand": "projects.issuetypes"}
            )
            if resp.ok:
                projects = resp.json().get("projects", [])
                if projects:
                    return [t.get("name") for t in projects[0].get("issuetypes", [])]
        except Exception:
            pass
        return ["Task"]  # safe fallback

    def create_ticket(
        self,
        summary: str,
        description: str = "",
        priority: str = "Medium",
        issue_type: str = "Task"
    ) -> Dict[str, Any]:
        """Create a new Jira ticket."""
        ok, message = self.ensure_configured()
        if not ok:
            return {"success": False, "message": message}

        ok, message = self.ensure_project_selected()
        if not ok:
            return {"success": False, "message": message}

        # Validate and fall back to Task if issue type is not in this project
        valid_types = self.get_project_issue_types()
        if issue_type not in valid_types:
            fallback = "Task" if "Task" in valid_types else (valid_types[0] if valid_types else "Task")
            print(f"[JiraClient] Issue type '{issue_type}' not found in project. "
                  f"Available: {valid_types}. Falling back to '{fallback}'.")
            issue_type = fallback

        payload = {
            "fields": {
                "summary": summary,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": description or " "}
                            ]
                        }
                    ]
                },
                "priority": {"name": priority},
                "project": {"key": self.project_key},
                "issuetype": {"name": issue_type},
            }
        }

        try:
            response = self.session.post(
                f"{self.url}/rest/api/3/issue",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            data = response.json()
            return {
                "success": True,
                "message": f"Ticket {data.get('key', '')} created successfully",
                "data": data
            }
        except Exception as e:
            return {"success": False, "message": f"Error creating ticket: {e}"}

    def delete_ticket(self, ticket_key: str) -> Dict[str, Any]:
        """Delete a Jira ticket."""
        ok, message = self.ensure_configured()
        if not ok:
            return {"success": False, "message": message}

        try:
            response = self.session.delete(
                f"{self.url}/rest/api/3/issue/{ticket_key}"
            )
            response.raise_for_status()
            return {"success": True, "message": f"Ticket {ticket_key} deleted"}
        except Exception as e:
            return {"success": False, "message": f"Error deleting ticket: {e}"}

    def get_ticket(self, ticket_key: str) -> Dict[str, Any]:
        """Get details of a specific ticket."""
        ok, message = self.ensure_configured()
        if not ok:
            return {"success": False, "message": message}

        try:
            response = self.session.get(
                f"{self.url}/rest/api/3/issue/{ticket_key}"
            )
            response.raise_for_status()
            data = response.json()
            fields = data.get("fields", {})
            return {
                "success": True,
                "data": {
                    "key": data.get("key"),
                    "summary": fields.get("summary"),
                    "description": self._extract_text(fields.get("description")),
                    "status": fields.get("status", {}).get("name"),
                    "assignee": (
                        fields.get("assignee", {}).get("displayName")
                        if fields.get("assignee") else "Unassigned"
                    ),
                    "priority": fields.get("priority", {}).get("name"),
                }
            }
        except Exception as e:
            return {"success": False, "message": f"Error fetching ticket: {e}"}

    # Fields to request from Jira API — must be explicit in the new /search/jql endpoint
    _SEARCH_FIELDS = "summary,status,priority,assignee,issuetype"

    def search_tickets(self, jql: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """Search for tickets using JQL via POST (new Jira Cloud API)."""
        ok, _ = self.ensure_configured()
        if not ok:
            return []

        try:
            response = self.session.post(
                f"{self.url}/rest/api/3/search/jql",
                json={
                    "jql": jql,
                    "maxResults": max_results,
                    "fields": ["summary", "status", "priority", "assignee", "issuetype"],
                },
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            data = response.json()
            tickets = []
            for issue in data.get("issues", []):
                fields = issue.get("fields") or {}
                tickets.append({
                    "key": issue.get("key"),
                    "summary": fields.get("summary"),
                    "status": (fields.get("status") or {}).get("name"),
                    "assignee": (
                        (fields.get("assignee") or {}).get("displayName", "Unassigned")
                    ),
                    "priority": (fields.get("priority") or {}).get("name"),
                    "issue_type": (fields.get("issuetype") or {}).get("name"),
                })
            return tickets
        except Exception as e:
            print(f"Error searching tickets: {e}")
            return []

    def get_tickets_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get all tickets with a specific status."""
        ok, _ = self.ensure_project_selected()
        if not ok:
            return []

        safe_status = self.escape_jql_value(status)
        jql = f'project = {self.project_key} AND status = "{safe_status}"'
        return self.search_tickets(jql)

    def get_in_progress_tickets(self) -> List[Dict[str, Any]]:
        """Get all tickets in progress."""
        return self.get_tickets_by_status("In Progress")

    def get_done_tickets(self) -> List[Dict[str, Any]]:
        """Get all done tickets."""
        return self.get_tickets_by_status("Done")

    def get_all_tickets(self) -> List[Dict[str, Any]]:
        """Get all tickets in the project."""
        ok, _ = self.ensure_project_selected()
        if not ok:
            return []

        jql = f"project = {self.project_key} ORDER BY created DESC"
        return self.search_tickets(jql)

    def get_project_summary(self) -> Dict[str, Any]:
        """Get a status breakdown summary for the current project."""
        ok, _ = self.ensure_project_selected()
        if not ok:
            return {
                "total": 0,
                "done": 0,
                "remaining": 0,
                "by_status": {},
                "tickets": [],
            }

        all_tickets = self.get_all_tickets()
        status_counts: Dict[str, int] = {}
        for t in all_tickets:
            s = t.get("status") or "Unknown"
            status_counts[s] = status_counts.get(s, 0) + 1
        total = len(all_tickets)
        done = status_counts.get("Done", 0)
        return {
            "total": total,
            "done": done,
            "remaining": total - done,
            "by_status": status_counts,
            "tickets": all_tickets,
        }

    def add_comment(self, ticket_key: str, comment: str) -> Dict[str, Any]:
        """Add a comment to a ticket."""
        ok, message = self.ensure_configured()
        if not ok:
            return {"success": False, "message": message}

        payload = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": comment}]
                    }
                ]
            }
        }
        try:
            response = self.session.post(
                f"{self.url}/rest/api/3/issue/{ticket_key}/comment",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return {"success": True, "message": f"Comment added to {ticket_key}"}
        except Exception as e:
            return {"success": False, "message": f"Error adding comment: {e}"}

    def get_comments(self, ticket_key: str) -> List[Dict[str, Any]]:
        """Get all comments for a ticket."""
        ok, _ = self.ensure_configured()
        if not ok:
            return []

        try:
            response = self.session.get(
                f"{self.url}/rest/api/3/issue/{ticket_key}/comment"
            )
            response.raise_for_status()
            data = response.json()
            comments = []
            for comment in data.get("comments", []):
                comments.append({
                    "author": comment.get("author", {}).get("displayName", "Unknown"),
                    "body": self._extract_text(comment.get("body")),
                    "created": comment.get("created", "")
                })
            return comments
        except Exception as e:
            print(f"Error fetching comments: {e}")
            return []

    def transition_ticket(
        self,
        ticket_key: str,
        transition_name: str
    ) -> Dict[str, Any]:
        """Transition a ticket to a new status."""
        ok, message = self.ensure_configured()
        if not ok:
            return {"success": False, "message": message}

        try:
            response = self.session.get(
                f"{self.url}/rest/api/3/issue/{ticket_key}/transitions"
            )
            response.raise_for_status()
            transitions = response.json().get("transitions", [])

            transition_id = None
            for t in transitions:
                if t.get("name", "").lower() == transition_name.lower():
                    transition_id = t.get("id")
                    break

            if not transition_id:
                return {
                    "success": False,
                    "message": f"Transition '{transition_name}' not found"
                }

            response = self.session.post(
                f"{self.url}/rest/api/3/issue/{ticket_key}/transitions",
                json={"transition": {"id": transition_id}}
            )
            response.raise_for_status()
            return {
                "success": True,
                "message": f"Ticket {ticket_key} moved to {transition_name}"
            }
        except Exception as e:
            return {"success": False, "message": f"Error transitioning ticket: {e}"}

    def find_assignable_users(self, ticket_key: str, query: str) -> List[Dict[str, Any]]:
        """Find assignable users for an issue by display-name query."""
        ok, _ = self.ensure_configured()
        if not ok:
            return []

        try:
            response = self.session.get(
                f"{self.url}/rest/api/2/user/assignable/search",
                params={
                    "issueKey": ticket_key,
                    "query": query,
                    "maxResults": 50,
                },
            )
            response.raise_for_status()
            users = []
            for user in response.json():
                users.append({
                    "accountId": user.get("accountId"),
                    "displayName": user.get("displayName"),
                    "active": user.get("active", True),
                })
            return users
        except Exception as e:
            print(f"Error finding assignable users: {e}")
            return []

    def assign_ticket(self, ticket_key: str, assignee_name: str) -> Dict[str, Any]:
        """Assign a ticket to an exact unique Jira display name."""
        ok, message = self.ensure_configured()
        if not ok:
            return {"success": False, "message": message}

        normalized_name = assignee_name.strip()
        if not normalized_name:
            return {"success": False, "message": "Assignee name is required"}

        users = self.find_assignable_users(ticket_key, normalized_name)
        exact_matches = [
            user for user in users
            if (user.get("displayName") or "").casefold() == normalized_name.casefold()
        ]

        if not exact_matches:
            suggestions = ", ".join(
                user["displayName"]
                for user in users[:5]
                if user.get("displayName")
            )
            suffix = (
                f" Similar assignable users: {suggestions}."
                if suggestions else ""
            )
            return {
                "success": False,
                "message": (
                    f"No assignable Jira user matched '{assignee_name}' for {ticket_key}."
                    f"{suffix}"
                ),
            }

        if len(exact_matches) > 1:
            candidates = ", ".join(
                user["displayName"]
                for user in exact_matches[:5]
                if user.get("displayName")
            )
            return {
                "success": False,
                "message": (
                    f"Multiple assignable Jira users matched '{assignee_name}' for {ticket_key}: "
                    f"{candidates}. Please be more specific."
                ),
            }

        match = exact_matches[0]
        account_id = match.get("accountId")
        if not account_id:
            return {
                "success": False,
                "message": f"Matched user '{match.get('displayName')}' is missing an accountId.",
            }

        try:
            response = self.session.put(
                f"{self.url}/rest/api/3/issue/{ticket_key}/assignee",
                json={"accountId": account_id},
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            return {
                "success": True,
                "message": f"Ticket {ticket_key} assigned to {match.get('displayName')}",
                "data": {
                    "ticket_key": ticket_key,
                    "assignee_name": match.get("displayName"),
                    "account_id": account_id,
                },
            }
        except Exception as e:
            return {"success": False, "message": f"Error assigning ticket: {e}"}

    def bulk_delete_tickets(
        self,
        ticket_keys: List[str],
        confirm: bool = False
    ) -> Dict[str, Any]:
        """Delete multiple tickets at once."""
        if not confirm:
            return {
                "success": False,
                "requires_confirmation": True,
                "message": (
                    f"About to delete {len(ticket_keys)} tickets: "
                    f"{', '.join(ticket_keys)}. "
                    "Set confirm=true to proceed."
                )
            }

        results = {"deleted": [], "failed": []}
        for key in ticket_keys:
            result = self.delete_ticket(key)
            if result.get("success"):
                results["deleted"].append(key)
            else:
                results["failed"].append({"key": key, "error": result.get("message")})

        return {
            "success": len(results["failed"]) == 0,
            "data": results,
            "message": (
                f"Deleted {len(results['deleted'])} tickets. "
                f"Failed: {len(results['failed'])}"
            )
        }

    def _extract_text(self, description: Optional[dict]) -> str:
        """Extract plain text from Jira's document format."""
        if not description:
            return ""

        def _flatten(node: Any) -> str:
            if isinstance(node, list):
                return "".join(_flatten(child) for child in node)
            if not isinstance(node, dict):
                return ""

            if node.get("type") == "text":
                return node.get("text", "")

            text = "".join(_flatten(child) for child in node.get("content", []))
            if node.get("type") in {"paragraph", "heading"}:
                return f"{text}\n"
            return text

        text = _flatten(description)
        return "\n".join(line.strip() for line in text.splitlines() if line.strip())


jira_client = JiraClient()

__all__ = ["JiraClient", "jira_client"]
