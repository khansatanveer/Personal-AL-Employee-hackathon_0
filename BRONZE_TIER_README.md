# Personal AI Employee - Bronze Tier Implementation

## Overview
This is a Bronze Tier implementation of the Personal AI Employee as part of the Hackathon 0: Building Autonomous FTEs in 2026. The system implements a local-first, agent-driven approach using Claude Code as the reasoning engine and Obsidian as the management dashboard.

## Architecture
- **The Brain**: Claude Code acts as the reasoning engine
- **The Memory/GUI**: Obsidian (local Markdown) as the dashboard
- **The Senses (Watchers)**: Python scripts monitor filesystems to trigger the AI
- **The Hands**: Agent skills handle external actions

## Features Implemented

### Core Components
1. **Dashboard.md**: Real-time summary of system status and activity
2. **Company_Handbook.md**: Rules of engagement and operational guidelines
3. **File System Watcher**: Monitors Inbox folder for new files
4. **Folder Structure**: Inbox, Needs_Action, Done, Plans, Pending_Approval, Logs

### Agent Skills
- `read_dashboard_status()`: Read current dashboard information
- `get_needs_action_files()`: List files requiring action
- `create_plan_file()`: Create plan files for task execution
- `move_file_to_done()`: Move completed tasks to Done folder
- `update_dashboard_activity()`: Update dashboard with new activities

## Setup Instructions

### Prerequisites
- Python 3.13 or higher
- Claude Code subscription
- Obsidian v1.10.6+

### Installation
1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Open the `AI_Employee_Vault` folder in Obsidian

### Usage

#### Running the File System Watcher
```bash
cd AI_Employee_Vault
python watchers/filesystem_watcher.py .
```

#### Using Agent Skills
The agent skills can be used by Claude Code to interact with the system:

1. The file system watcher monitors the `Inbox/` folder
2. When new `.md` files appear, they are automatically moved to `Needs_Action/`
3. Claude Code can then process files in `Needs_Action/` using agent skills
4. Plans are created in the `Plans/` folder
5. Completed tasks are moved to the `Done/` folder

#### Example Workflow
1. Place a task file in the `Inbox/` folder
2. The file system watcher detects it and moves it to `Needs_Action/`
3. Claude Code processes the file using agent skills
4. A plan is created in the `Plans/` folder
5. The task is moved to `Done/` when completed
6. The dashboard is updated with activity logs

## File Structure
- `Dashboard.md`: System dashboard with status and activity
- `Company_Handbook.md`: Rules and guidelines for the AI Employee
- `Inbox/`: Incoming files and tasks
- `Needs_Action/`: Files requiring processing
- `Done/`: Completed tasks
- `Plans/`: Created action plans
- `Pending_Approval/`: Tasks requiring human approval
- `Logs/`: System logs and audit trail
- `watchers/filesystem_watcher.py`: File system monitoring script
- `agent_skills.py`: Claude Code agent skills
- `requirements.txt`: Python dependencies

## Bronze Tier Requirements Verification
✅ Obsidian vault with Dashboard.md and Company_Handbook.md
✅ One working Watcher script (Gmail OR file system monitoring)
✅ Claude Code successfully reading from and writing to the vault
✅ Basic folder structure: /Inbox, /Needs_Action, /Done
✅ All AI functionality implemented as Agent Skills

## Security & Privacy
- All data stored locally in Obsidian vault
- No external data transmission (local-first architecture)
- Human-in-the-loop for sensitive actions

## Next Steps (Silver/Gold Tiers)
- Multiple watcher scripts (Gmail, WhatsApp, LinkedIn)
- MCP servers for external actions
- Automated posting capabilities
- Financial tracking and audit systems

## License
This project is part of the Personal AI Employee Hackathon 0 and follows the hackathon guidelines.