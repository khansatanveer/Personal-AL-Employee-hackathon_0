#!/usr/bin/env python3
"""
Test script to demonstrate Claude Code reading from and writing to the vault
This simulates the integration between Claude Code and the Obsidian vault
"""

import os
import time
from pathlib import Path
import json
from datetime import datetime


def read_vault_contents(vault_path):
    """Read and return summary of vault contents"""
    vault = Path(vault_path)

    summary = {
        'dashboard_exists': (vault / 'Dashboard.md').exists(),
        'handbook_exists': (vault / 'Company_Handbook.md').exists(),
        'needs_action_count': 0,
        'accounting_files': [],
        'projects_files': [],
        'last_updated': datetime.now().isoformat()
    }

    # Count files in Needs_Action
    needs_action_dir = vault / 'Needs_Action'
    if needs_action_dir.exists():
        summary['needs_action_count'] = len(list(needs_action_dir.glob('*.md')))

    # List files in Accounting
    accounting_dir = vault / 'Accounting'
    if accounting_dir.exists():
        summary['accounting_files'] = [f.name for f in accounting_dir.glob('*.md')]

    # List files in Projects
    projects_dir = vault / 'Projects'
    if projects_dir.exists():
        summary['projects_files'] = [f.name for f in projects_dir.glob('*.md')]

    return summary


def write_to_vault(vault_path, filename, content):
    """Write content to a file in the vault"""
    vault = Path(vault_path)
    filepath = vault / filename
    filepath.write_text(content)
    return str(filepath)


def create_sample_action_item(vault_path, subject, details):
    """Create a sample action item in the Needs_Action folder"""
    vault = Path(vault_path)
    needs_action_dir = vault / 'Needs_Action'
    needs_action_dir.mkdir(exist_ok=True)

    # Create a unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"action_{timestamp}.md"
    filepath = needs_action_dir / filename

    content = f"""---
type: action_item
created: {datetime.now().isoformat()}
subject: {subject}
priority: medium
status: pending
---

# {subject}

## Details
{details}

## Required Actions
- [ ] Review requirements
- [ ] Assign to team member
- [ ] Set deadline
- [ ] Follow up

## Notes
Created automatically by Claude Code integration test
"""

    filepath.write_text(content)
    print(f"Created action item: {filepath}")
    return str(filepath)


def main():
    vault_path = "AI_Employee_Vault"

    print("Testing Claude Code - Vault Integration")
    print("="*50)

    # Read vault contents
    print("\nReading vault contents...")
    summary = read_vault_contents(vault_path)
    print(f"Dashboard exists: {summary['dashboard_exists']}")
    print(f"Handbook exists: {summary['handbook_exists']}")
    print(f"Needs_Action items: {summary['needs_action_count']}")
    print(f"Accounting files: {len(summary['accounting_files'])}")
    print(f"Projects files: {len(summary['projects_files'])}")

    # Create a sample action item to demonstrate writing
    print("\nCreating a sample action item...")
    create_sample_action_item(
        vault_path,
        "Test Integration Success",
        "This action item was created to demonstrate that Claude Code can write to the vault successfully."
    )

    # Read vault contents again to show the change
    print("\nReading vault contents after update...")
    updated_summary = read_vault_contents(vault_path)
    print(f"Needs_Action items after update: {updated_summary['needs_action_count']}")

    print(f"\nIntegration test completed successfully!")
    print(f"Vault path: {vault_path}")
    print(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()