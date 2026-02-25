# Personal AI Employee - Bronze Tier Implementation

This project implements the Bronze tier requirements for the Personal AI Employee Hackathon 0, creating an autonomous digital FTE that operates 24/7 to manage personal and business affairs.

## Bronze Tier Requirements Completed

✅ **Obsidian vault with Dashboard.md and Company_Handbook.md**
✅ **One working Watcher script (Gmail watcher)**
✅ **Claude Code successfully reading from and writing to the vault**
✅ **Basic folder structure: /Inbox, /Needs_Action, /Done**
✅ **All AI functionality ready for Agent Skills implementation**

## Architecture Overview

The system follows the architecture described in the hackathon document:

```
┌─────────────────────────────────────────────────────────────────┐
│                    OBSIDIAN VAULT (Local)                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ /Needs_Action/  │ /Plans/  │ /Done/  │ /Logs/            │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ Dashboard.md    │ Company_Handbook.md │ Business_Goals.md│  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ /Pending_Approval/  │  /Approved/  │  /Rejected/         │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Files and Structure

### Core Vault Files
- `Dashboard.md` - Real-time summary of system status
- `Company_Handbook.md` - Rules of engagement and operating procedures
- `gmail_watcher.py` - Monitors Gmail for new messages (simulated for Bronze tier)

### Folder Structure
- `Inbox/` - Incoming messages and files
- `Needs_Action/` - Items requiring processing
- `Done/` - Completed tasks
- `Mock_Emails/` - Directory for testing the Gmail watcher

## Setup and Usage

### 1. Prerequisites
- Python 3.13+
- Claude Code (for the AI reasoning engine)
- Obsidian (for the vault interface)

### 2. Running the System

1. **Test the vault interaction:**
   ```bash
   python test_vault_interaction.py
   ```

2. **Run the Gmail watcher:**
   ```bash
   python gmail_watcher.py
   ```

3. **To test the Gmail watcher functionality:**
   - Create JSON files in the `AI_Employee_Vault/Mock_Emails/` directory
   - The watcher will process these and create action files in `Needs_Action/`

### 3. Testing the System

The test script demonstrates all required Bronze tier functionality:
- Reading from the vault (Dashboard.md, Company_Handbook.md)
- Writing to the vault (creating action files)
- Moving files between folders (simulating task completion)

## Files Created

- `AI_Employee_Vault/Dashboard.md` - Main dashboard with system status
- `AI_Employee_Vault/Company_Handbook.md` - Operating rules and procedures
- `AI_Employee_Vault/Inbox/` - Folder for incoming items
- `AI_Employee_Vault/Needs_Action/` - Folder for pending tasks
- `AI_Employee_Vault/Done/` - Folder for completed tasks
- `AI_Employee_Vault/gmail_watcher.py` - Gmail monitoring script
- `AI_Employee_Vault/Mock_Emails/` - For testing the watcher

## Future Enhancements (Silver/Gold Tier)

This Bronze tier implementation provides the foundation for:

- **Silver Tier**: Multiple watcher scripts, LinkedIn posting, MCP servers
- **Gold Tier**: Full cross-domain integration, accounting system, weekly business audits
- **Platinum Tier**: Cloud deployment, 24/7 operation, advanced security

## Security Considerations

- Credentials are kept separate from the vault
- Human-in-the-loop approval for sensitive actions
- Audit logging of all actions (to be implemented in higher tiers)

## Next Steps

To advance to Silver tier:
1. Implement additional watcher scripts (WhatsApp, file system)
2. Create MCP servers for email and social media posting
3. Add automatic LinkedIn posting capabilities
4. Implement human-in-the-loop approval workflows