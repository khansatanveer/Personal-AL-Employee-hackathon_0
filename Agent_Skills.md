# Agent Skills for Personal AI Employee

This document outlines how Agent Skills would be implemented for the Bronze tier Personal AI Employee system.

## Overview

Agent Skills are specialized functions that extend Claude Code's capabilities to interact with the Personal AI Employee system. They allow Claude to perform specific actions like processing emails, managing tasks, and updating the vault.

## Required Agent Skills for Bronze Tier

### 1. Email Processing Skill

```json
{
  "name": "gmail_processor",
  "description": "Process incoming emails from Gmail and create action files",
  "input_schema": {
    "type": "object",
    "properties": {
      "email_id": {
        "type": "string",
        "description": "The unique identifier of the email to process"
      },
      "action_required": {
        "type": "string",
        "description": "Specific action to take on the email"
      }
    },
    "required": ["email_id", "action_required"]
  }
}
```

### 2. Task Management Skill

```json
{
  "name": "task_manager",
  "description": "Move tasks between folders (Inbox, Needs_Action, Done)",
  "input_schema": {
    "type": "object",
    "properties": {
      "source_folder": {
        "type": "string",
        "description": "The folder to move from"
      },
      "destination_folder": {
        "type": "string",
        "description": "The folder to move to"
      },
      "task_file": {
        "type": "string",
        "description": "The name of the task file to move"
      }
    },
    "required": ["source_folder", "destination_folder", "task_file"]
  }
}
```

### 3. Vault Reader Skill

```json
{
  "name": "vault_reader",
  "description": "Read specific files from the Obsidian vault",
  "input_schema": {
    "type": "object",
    "properties": {
      "file_path": {
        "type": "string",
        "description": "The path to the file in the vault to read"
      }
    },
    "required": ["file_path"]
  }
}
```

### 4. Dashboard Updater Skill

```json
{
  "name": "dashboard_updater",
  "description": "Update the main dashboard with new information",
  "input_schema": {
    "type": "object",
    "properties": {
      "section": {
        "type": "string",
        "enum": ["recent_activity", "pending_actions", "system_status"],
        "description": "Which section of the dashboard to update"
      },
      "content": {
        "type": "string",
        "description": "The content to add to the specified section"
      }
    },
    "required": ["section", "content"]
  }
}
```

## Example Agent Skill Implementation (Conceptual)

In a complete implementation, these skills would be registered with Claude Code's system. Here's a conceptual example of how the task_manager skill might be implemented:

```python
# Conceptual implementation for task_manager agent skill
def move_task(source_folder, destination_folder, task_file):
    """
    Move a task file from source folder to destination folder
    """
    import os
    from pathlib import Path

    vault_path = "AI_Employee_Vault"
    source_path = Path(vault_path) / source_folder / task_file
    dest_path = Path(vault_path) / destination_folder / task_file

    if source_path.exists():
        # Create destination folder if it doesn't exist
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Move the file
        os.rename(str(source_path), str(dest_path))

        return {
            "success": True,
            "message": f"Moved {task_file} from {source_folder} to {destination_folder}"
        }
    else:
        return {
            "success": False,
            "message": f"Source file {source_path} does not exist"
        }
```

## Configuration

Agent Skills are configured in Claude Code through the settings system:

```json
{
  "custom_skills": [
    {
      "name": "gmail_processor",
      "handler": "skills.gmail_processor",
      "description": "Process incoming emails and create action files"
    },
    {
      "name": "task_manager",
      "handler": "skills.task_manager",
      "description": "Move tasks between folders (Inbox, Needs_Action, Done)"
    },
    {
      "name": "vault_reader",
      "handler": "skills.vault_reader",
      "description": "Read specific files from the Obsidian vault"
    },
    {
      "name": "dashboard_updater",
      "handler": "skills.dashboard_updater",
      "description": "Update the main dashboard with new information"
    }
  ]
}
```

## Integration with Current System

The Agent Skills would integrate with the existing files and structure:
- Process emails detected by the gmail_watcher.py
- Move task files between the /Inbox, /Needs_Action, and /Done folders
- Read from Dashboard.md and Company_Handbook.md as needed
- Update the dashboard with recent activities and status

This Agent Skills framework provides the foundation for the AI Employee to operate autonomously as specified in the Bronze tier requirements.