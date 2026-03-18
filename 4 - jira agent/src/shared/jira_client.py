import os
import requests
from typing import Optional, List, Dict, Any
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

    def set_project(self, project_key: str):
        """Set the current project key."""
        self.project_key = project_key

    def get_projects(self) -> List[Dict[str, Any]]:
        """Get all projects accessible by the user."""
        if not self.is_configured():
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
        if not self.project_key:
            return {"success": False, "message": "No project selected"}

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
        jql = f'project = {self.project_key} AND status = "{status}"'
        return self.search_tickets(jql)

    def get_in_progress_tickets(self) -> List[Dict[str, Any]]:
        """Get all tickets in progress."""
        return self.get_tickets_by_status("In Progress")

    def get_done_tickets(self) -> List[Dict[str, Any]]:
        """Get all done tickets."""
        return self.get_tickets_by_status("Done")

    def get_all_tickets(self) -> List[Dict[str, Any]]:
        """Get all tickets in the project."""
        jql = f"project = {self.project_key} ORDER BY created DESC"
        return self.search_tickets(jql)

    def get_project_summary(self) -> Dict[str, Any]:
        """Get a status breakdown summary for the current project."""
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
        content = description.get("content", [])
        for item in content:
            if item.get("type") == "paragraph":
                text_parts = []
                for text_item in item.get("content", []):
                    if text_item.get("type") == "text":
                        text_parts.append(text_item.get("text", ""))
                return " ".join(text_parts)
        return ""


jira_client = JiraClient()

__all__ = ["JiraClient", "jira_client"]