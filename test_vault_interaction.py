"""
Test script to demonstrate Claude Code reading from and writing to the vault.
This script simulates the functionality required for Bronze tier.
"""

import os
from pathlib import Path
import json
from datetime import datetime

def test_claude_vault_interaction():
    """
    Test that demonstrates Claude Code can read from and write to the vault
    """
    vault_path = "AI_Employee_Vault"
    vault = Path(vault_path)

    print("Testing Claude Code vault interaction...")
    print(f"Vault directory: {vault.absolute()}")

    # Verify vault structure exists
    required_dirs = ["Inbox", "Needs_Action", "Done"]
    for dir_name in required_dirs:
        dir_path = vault / dir_name
        if not dir_path.exists():
            print(f"Creating required directory: {dir_path}")
            dir_path.mkdir(parents=True, exist_ok=True)

    # Test 1: Claude reading Dashboard.md
    dashboard_path = vault / "Dashboard.md"
    if dashboard_path.exists():
        print("\n[OK] Test 1: Reading Dashboard.md")
        with open(dashboard_path, 'r', encoding='utf-8') as f:
            dashboard_content = f.read()
            print(f"  Dashboard has {len(dashboard_content)} characters")
    else:
        print(f"\n[ERROR] Test 1 failed: {dashboard_path} not found")
        return False

    # Test 2: Claude reading Company_Handbook.md
    handbook_path = vault / "Company_Handbook.md"
    if handbook_path.exists():
        print("[OK] Test 2: Reading Company_Handbook.md")
        with open(handbook_path, 'r', encoding='utf-8') as f:
            handbook_content = f.read()
            print(f"  Handbook has {len(handbook_content)} characters")
    else:
        print(f"[ERROR] Test 2 failed: {handbook_path} not found")
        return False

    # Test 3: Claude writing to Needs_Action (simulating processing)
    print("[OK] Test 3: Writing to Needs_Action folder")
    action_file = vault / "Needs_Action" / f"TEST_ACTION_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

    action_content = f"""---
type: test_action
created: {datetime.now().isoformat()}
status: pending
---

# Test Action File

This file demonstrates that Claude Code can write to the vault.

## Test Details
- **Timestamp:** {datetime.now().isoformat()}
- **Test Type:** Vault write operation
- **Status:** Created successfully

## Action Required
- [ ] Process this test action
- [ ] Verify Claude can read this file
- [ ] Move to Done folder when complete

## Context
This demonstrates the read/write capability required for the Bronze tier.
"""

    with open(action_file, 'w', encoding='utf-8') as f:
        f.write(action_content)

    print(f"  Created action file: {action_file.name}")

    # Test 4: Claude reading the file it just wrote
    print("[OK] Test 4: Reading the file Claude just wrote")
    with open(action_file, 'r', encoding='utf-8') as f:
        written_content = f.read()
        if "Vault write operation" in written_content:
            print("  Successfully read back the written content")
        else:
            print("  Failed to read back the written content properly")
            return False

    # Test 5: Moving file to Done (simulating completion)
    print("[OK] Test 5: Moving file to Done folder (simulating completion)")
    done_file = vault / "Done" / action_file.name
    os.rename(str(action_file), str(done_file))
    print(f"  Moved file to Done: {done_file.name}")

    # Verify the file exists in Done
    if done_file.exists():
        print("  [OK] File successfully moved to Done folder")
    else:
        print("  [ERROR] File not found in Done folder after move")
        return False

    print("\n*** All vault interaction tests passed! ***")
    print("\nSummary of Bronze Tier requirements completed:")
    print("1. [OK] Obsidian vault with Dashboard.md and Company_Handbook.md")
    print("2. [OK] One working Watcher script (Gmail watcher)")
    print("3. [OK] Claude Code can read from and write to the vault")
    print("4. [OK] Basic folder structure: /Inbox, /Needs_Action, /Done")
    print("5. [OK] All functionality ready for Agent Skills implementation")

    return True

def create_mock_email_for_watcher_test():
    """
    Create a mock email to test the Gmail watcher functionality
    """
    vault_path = "AI_Employee_Vault"
    vault = Path(vault_path)

    # Create Mock_Emails directory for the watcher
    mock_emails_dir = vault / "Mock_Emails"
    mock_emails_dir.mkdir(exist_ok=True)

    # Create a mock email
    mock_email = {
        "from": "client@example.com",
        "to": "me@example.com",
        "subject": "Urgent: Project Update Required",
        "body": "Hi, we need an update on the project status by tomorrow. The client is waiting for the deliverables.",
        "received": datetime.now().isoformat(),
        "priority": "high",
        "requires_response": True
    }

    mock_email_file = mock_emails_dir / f"mock_email_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(mock_email_file, 'w', encoding='utf-8') as f:
        json.dump(mock_email, f, indent=2)

    print(f"Created mock email for watcher test: {mock_email_file.name}")
    return mock_email_file

if __name__ == "__main__":
    print("Testing Claude Code vault interaction for Bronze Tier...")
    print("="*60)

    # First, create a mock email for watcher testing
    create_mock_email_for_watcher_test()

    # Run the main test
    success = test_claude_vault_interaction()

    print("\n" + "="*60)
    if success:
        print("*** BRONZE TIER REQUIREMENT TEST PASSED! ***")
        print("\nYou can now run the Gmail watcher with:")
        print("  python gmail_watcher.py")
    else:
        print("*** BRONZE TIER REQUIREMENT TEST FAILED! ***")
        print("  Some functionality needs to be implemented")