"""
Gmail Monitoring Agent Skill for AI Employee Vault
Implements the Gmail watcher functionality as an agent skill
"""

from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List, Optional


def check_urgent_emails(vault_path: str = "AI_Employee_Vault") -> Dict:
    """
    Check Gmail for urgent/unread emails and create action items.

    Args:
        vault_path: Path to the AI Employee vault (default: "AI_Employee_Vault")

    Returns:
        Dictionary with summary of emails found and action items created
    """
    # This would integrate with the Gmail API in a real implementation
    # For now, we'll simulate the functionality

    vault = Path(vault_path)
    needs_action_dir = vault / "Needs_Action"
    needs_action_dir.mkdir(exist_ok=True)

    # Simulate finding urgent emails (in a real implementation, this would call Gmail API)
    urgent_emails = [
        {
            "from": "client@example.com",
            "subject": "Urgent: Project Deadline Inquiry",
            "body": "Hi, I wanted to check on the status of the project we discussed. Can you provide an update?",
            "timestamp": datetime.now().isoformat()
        }
    ]

    created_files = []
    for i, email in enumerate(urgent_emails):
        # Create action file for each urgent email
        filename = f"EMAIL_URGENT_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        filepath = needs_action_dir / filename

        content = f"""---
type: urgent_email
from: {email['from']}
subject: {email['subject']}
received: {email['timestamp']}
priority: high
status: pending
---

# Urgent Email: {email['subject']}

## Sender
{email['from']}

## Content
{email['body']}

## Suggested Actions
- [ ] Reply to sender with status update
- [ ] Escalate to appropriate team member
- [ ] Schedule follow-up if needed

## Created
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        filepath.write_text(content)
        created_files.append(str(filepath))

    return {
        "status": "success",
        "urgent_emails_found": len(urgent_emails),
        "action_items_created": len(created_files),
        "files_created": created_files,
        "timestamp": datetime.now().isoformat()
    }


def read_vault_file(filepath: str) -> str:
    """
    Read a specific file from the vault.

    Args:
        filepath: Path to the file relative to vault directory

    Returns:
        Content of the file as a string
    """
    full_path = Path("AI_Employee_Vault") / filepath
    if full_path.exists():
        try:
            return full_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            # Fallback to reading with error handling
            return full_path.read_text(encoding='utf-8', errors='replace')
    else:
        return f"File not found: {filepath}"


def write_vault_file(filepath: str, content: str) -> Dict:
    """
    Write content to a file in the vault.

    Args:
        filepath: Path where to save the file relative to vault directory
        content: Content to write to the file

    Returns:
        Status dictionary
    """
    full_path = Path("AI_Employee_Vault") / filepath
    full_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        full_path.write_text(content, encoding='utf-8')
        return {
            "status": "success",
            "file_path": str(full_path),
            "message": f"Successfully wrote to {full_path}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to write file: {str(e)}"
        }


def list_vault_directory(directory: str) -> List[str]:
    """
    List files in a specific vault directory.

    Args:
        directory: Directory name relative to vault (e.g., "Needs_Action", "Inbox", "Done")

    Returns:
        List of file paths in the directory
    """
    vault_dir = Path("AI_Employee_Vault") / directory
    if vault_dir.exists():
        files = [str(f.relative_to(Path("AI_Employee_Vault"))) for f in vault_dir.glob("*.md")]
        return files
    else:
        return []


def update_dashboard_status(status_updates: Dict) -> Dict:
    """
    Update the Dashboard.md file with current status information.

    Args:
        status_updates: Dictionary with status information to update

    Returns:
        Status dictionary
    """
    dashboard_path = Path("AI_Employee_Vault") / "Dashboard.md"

    if dashboard_path.exists():
        content = dashboard_path.read_text()

        # Update status fields based on the provided updates
        for key, value in status_updates.items():
            placeholder = f"{{{{{key}}}}}"
            content = content.replace(placeholder, str(value))

        # Update timestamp
        content = content.replace(
            "{{date}}",
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ).replace(
            "{{time}}",
            datetime.now().strftime('%H:%M:%S')
        )

        dashboard_path.write_text(content)

        return {
            "status": "success",
            "message": "Dashboard updated successfully",
            "updated_fields": list(status_updates.keys())
        }
    else:
        return {
            "status": "error",
            "message": "Dashboard.md not found"
        }