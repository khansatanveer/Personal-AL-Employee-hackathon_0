# 🤖 AI Employee Vault - Bronze Tier Implementation

This is a complete Bronze Tier implementation of the Personal AI Employee as described in the hackathon document. The system includes Gmail monitoring capabilities and integrates with an Obsidian-style vault for management.

## ✅ Features Implemented

1. **Obsidian Vault Structure**
   - Dashboard.md: Main status dashboard
   - Company_Handbook.md: Operational guidelines
   - Standard folder structure (Needs_Action, Accounting, Projects, Archive)

2. **Gmail Watcher**
   - Monitors Gmail for important/unread messages
   - Creates action items in the Needs_Action folder
   - Uses Google API for secure access
   - Implements proper error handling and logging

3. **Vault Integration**
   - Claude Code can read from and write to the vault
   - Demonstrated through integration test script
   - Updates dashboard with real-time status

## 📁 Directory Structure

```
AI_Employee_Vault/
├── Dashboard.md          # Main status dashboard
├── Company_Handbook.md   # Operational guidelines
├── base_watcher.py       # Abstract base class for watchers
├── gmail_watcher.py      # Gmail monitoring implementation
├── orchestrator.py       # Main system orchestrator
├── vault_integration_test.py  # Test for Claude Code integration
├── requirements.txt      # Python dependencies
├── ai_employee.log       # Runtime logs
├── Needs_Action/         # Items requiring action
├── Accounting/           # Financial records
├── Projects/             # Project documentation
└── Archive/              # Old records
```

## 🚀 Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set up Gmail API Credentials
1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API
4. Create credentials (OAuth 2.0 client ID) for a desktop application
5. Download the credentials file and rename it to `gmail_credentials.json`
6. Place the file in the main directory

### 3. Run the System
```bash
python orchestrator.py
```

## 🔧 Testing the Implementation

You can test the Claude Code - vault integration by running:
```bash
python vault_integration_test.py
```

## 📋 Bronze Tier Requirements Verification

- [x] Obsidian vault with Dashboard.md and Company_Handbook.md
- [x] One working Watcher script (Gmail)
- [x] Claude Code successfully reading from and writing to the vault

## 🛠️ How It Works

1. **Gmail Watcher** monitors your Gmail account every 2 minutes for important/unread messages
2. When an important email is found, it creates a markdown file in the `Needs_Action` folder
3. The system updates the `Dashboard.md` with current status and counts
4. All data is stored locally in the Obsidian vault format

## 🌟 Next Steps (Silver/Gold Tiers)

This Bronze Tier implementation provides the foundation for:
- Additional watchers (WhatsApp, file system monitoring)
- More sophisticated action processing
- Integration with other business tools
- Advanced autonomous operations

## 🚨 Important Notes

- All data is stored locally for privacy
- The system requires proper OAuth credentials for Gmail access
- Logs are maintained for troubleshooting
- The system implements rate limiting and error handling

---
*Built for the Personal AI Employee Hackathon 0 - Building Autonomous FTEs in 2026*