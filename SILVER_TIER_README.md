# Personal AI Employee — Silver Tier

> An autonomous AI employee that monitors emails, posts to LinkedIn, drafts replies, and manages tasks — with human oversight at every step.

**Hackathon:** Personal AI Employee Hackathon 0 — Building Autonomous FTEs in 2026  
**Status:** ✅ All Silver Tier Requirements Met  
**Author:** Khansa Tanveer

---

## Overview

This is a **Silver Tier** implementation of the Personal AI Employee (Hackathon 0: Building Autonomous FTEs in 2026). The system extends the Bronze Tier foundation by adding **perception** and **action** capabilities — your AI employee now monitors Gmail, posts to LinkedIn automatically, drafts professional email replies, and manages tasks through a transparent file-based workflow.

All outbound actions require **human approval** before execution.

### Core Principles

| Principle | Meaning |
|-----------|---------|
| 📁 **File-based** | Everything is a Markdown file. No databases, no hidden state. |
| 🔒 **Human-in-the-loop** | Nothing gets sent without your explicit approval. |
| 🏠 **Local-first** | Runs entirely on your machine. No cloud beyond Gmail/LinkedIn APIs. |
| 📊 **Transparent** | Every action logged, every decision visible, full audit trail. |
| 🤖 **Autonomous** | Watches, detects, drafts, and suggests — you just approve. |

---

## Architecture

| Layer | Component | Purpose |
|-------|-----------|---------|
| **Perception** | Gmail Watcher | Monitors Gmail for new emails continuously |
| **Reasoning** | `agent_skills.py`, `orchestrator.py` | Process, plan, and decide |
| **Action** | Gmail API (send emails), Playwright (LinkedIn posting) | Execute approved actions |
| **Memory/GUI** | Obsidian (local Markdown vault) | Dashboard, files, audit trail |

```
Gmail Watcher ──→ Needs_Action/ ──→ Human Approves ──→ Approved/ ──→ Gmail API (send)
LinkedIn Poster ──→ Reads Approved/ ──→ Posts automatically ──→ Done/
```

### Services

| Service | File | Started By | Interval | Purpose |
|---------|------|-----------|----------|---------|
| Gmail | `watchers/gmail_watcher.py` | Orchestrator | 120s | Monitor new emails |
| LinkedIn | `watchers/linkedin_poster.py` | Manual | Per post | Auto-post approved content |

---

## Features Implemented

### Core Components

1. **Dashboard.md** — Real-time system status and activity summary
2. **Company_Handbook.md** — Rules of engagement and operational guidelines
3. **Gmail Watcher** — Monitors Gmail for unread emails, creates action files, drafts replies, sends approved emails
4. **LinkedIn Auto Poster** — Fully automatic posting with human-like behavior and challenge detection
5. **Folder Structure** — Inbox, Needs_Action, Done, Plans, Pending_Approval, Approved, Rejected, Logs, Social_Posts, Emails, Briefings, Schedules, Accounting

### Agent Skills

| Skill | Description |
|-------|-------------|
| `read_dashboard_status()` | Read current dashboard information |
| `get_needs_action_files()` | List files requiring action |
| `create_plan_file()` | Create plan files for task execution |
| `move_file_to_done()` | Move completed tasks to Done folder |
| `update_dashboard_activity()` | Update dashboard with new activities |
| `create_linkedin_post()` | Create draft LinkedIn posts |
| `publish_linkedin_post()` | Publish approved LinkedIn posts |
| `request_post_approval()` | Move posts into approval workflow |
| `generate_business_post()` | Generate business-focused post content |
| `compose_email()` | Create draft email files |
| `request_email_approval()` | Create email approval requests |
| `send_email()` | Send approved emails via Gmail API |
| `generate_ceo_briefing()` | Generate daily CEO briefing |

---

## Setup Instructions

### Prerequisites

- Python 3.8+
- Google Cloud project with Gmail API enabled ([`credentials.json`](credentials.json) required)
- LinkedIn account with active session
- Playwright-compatible browser (Chromium)

### Step 1: Install Dependencies

```bash
cd AI_Employee_Vault
pip install -r requirements.txt
playwright install chromium
```

### Step 2: Setup Gmail OAuth

```bash
python setup_gmail.py
```

Opens browser for Google authorization. Grants three permissions:
- `gmail.readonly` — Read incoming emails
- `gmail.compose` — Draft email replies
- `gmail.send` — Send approved replies

Saves authentication token for future automated use.

### Step 3: Login to LinkedIn

```bash
python watchers/linkedin_poster.py --login
```

Opens LinkedIn in browser. Log in normally. Session is saved for future automated runs.

### Step 4: Verify Setup

```bash
python watchers/gmail_watcher.py --test
python watchers/linkedin_poster.py --test
```

---

## How to Run

### Start All Services

```bash
cd AI_Employee_Vault
python orchestrator.py
```

This starts the Gmail Watcher as a background service. The LinkedIn Poster is run manually for each approved post you want to publish.

### Monitor Gmail Only

```bash
python watchers/gmail_watcher.py
```

Checks for new emails every 120 seconds. Auto-creates action files, reply drafts, and action plans.

### Process Approved Emails → Create Draft Replies

```bash
python watchers/gmail_watcher.py --process-approved
```

Reads email files from `Approved/`, generates professional reply drafts, creates action plans.

### Send Approved Email Replies

```bash
python watchers/gmail_watcher.py --send-approved
```

Sends all email replies marked `[x] **APPROVE**` via Gmail API. Moves files to `Done/`.

### Post to LinkedIn

```bash
python watchers/linkedin_poster.py
```

Posts one approved LinkedIn post fully automatically. Moves file to `Done/` after success.

### Test Mode (No Actions)

```bash
python watchers/gmail_watcher.py --dry-run
python watchers/gmail_watcher.py --send-approved --dry-run
python watchers/linkedin_poster.py --test
```

---

## Demo Workflow — Step by Step

### Workflow A: Receive Email → Auto-Send Reply

```
Step 1: Email arrives in Gmail inbox
    ↓
Step 2: Gmail Watcher detects it (auto, every 2 min)
    ↓
Step 3: Three files created automatically:
    ├── Needs_Action/GMAIL_Sender_Subject.md (full email + suggested reply)
    ├── Plans/PLAN_EMAIL_Subject.md (action checklist + timeline)
    └── Pending_Approval/EMAIL_REPLY_Subject.md (draft reply)
    ↓
Step 4: You review the files in Obsidian or any text editor
    ↓
Step 5: Move email file to Approved/ (your approval decision)
    ↓
Step 6: Run: python watchers/gmail_watcher.py --process-approved
    ├── Parses approved email
    ├── Generates professional reply draft
    └── Creates action plan
    ↓
Step 7: Open draft reply in Pending_Approval/
    ↓
Step 8: Mark [x] **APPROVE** in the file
    ↓
Step 9: Run: python watchers/gmail_watcher.py --send-approved
    ├── Email sent via Gmail API ✅
    ├── Draft status → "sent"
    ├── Action plan → "completed"
    └── All files moved to Done/
```

### Workflow B: Post to LinkedIn

```
Step 1: Create post draft
    python -c "from agent_skills import AIEmployeeSkills; s = AIEmployeeSkills(); s.create_linkedin_post('Your content')"
    ↓
Step 2: Move draft to Approved/ (your decision)
    ↓
Step 3: Run: python watchers/linkedin_poster.py
    ├── Opens LinkedIn feed (auto)
    ├── Clicks "Start a post" (auto, 7 fallback methods)
    ├── Types content with human-like delays (auto)
    ├── Waits for Post button to enable (auto)
    ├── Clicks Post (auto, 3 methods)
    └── Verifies success with screenshots (auto)
    ↓
Step 4: File moved to Done/ — post is live! ✅
```

### Workflow C: Daily Operation

```
Morning:
    python orchestrator.py          # Start Gmail Watcher

During the day:
    • Emails auto-detected → Needs_Action/
    • Review files in Obsidian
    • Move important ones to Approved/
    • Run --process-approved to create drafts
    • Mark [x] **APPROVE** in drafts you like
    • Run --send-approved to send them

As needed:
    • Create LinkedIn posts via agent_skills
    • Move to Approved/
    • Run linkedin_poster.py

Evening:
    • Check Dashboard.md for daily summary
    • Review Done/ folder for audit trail
```

---

## Folder Structure

```
Personal-AI-Employee/
│
├── credentials.json                      # Google OAuth client config
├── SILVER_TIER_README.md                 # This file
├── SILVER_TIER_COMPLETE.md               # Feature summary & test results
│
└── AI_Employee_Vault/                    # Main workspace (Obsidian vault)
    │
    ├── agent_skills.py                   # AI employee skills (13 methods)
    ├── orchestrator.py                   # Central process manager
    ├── setup_gmail.py                    # Gmail OAuth setup
    ├── requirements.txt                  # Python dependencies
    ├── Dashboard.md                      # Live status dashboard
    ├── Company_Handbook.md               # Company context & rules
    │
    ├── watchers/                         # Background services
    │   ├── gmail_watcher.py              # Email monitor + reply sender
    │   ├── linkedin_poster.py            # LinkedIn auto-poster
    │   ├── linkedin_poster_manual.py     # Manual posting mode
    │   └── reset_linkedin_session.py     # Session reset utility
    │
    ├── credentials/                      # OAuth credentials (secrets)
    │   ├── gmail_credentials.json        # Google API credentials
    │   └── gmail_token.pickle            # Auth token (auto-managed)
    │
    ├── sessions/                         # Browser sessions
    │   └── linkedin/                     # Saved LinkedIn session
    │
    ├── Needs_Action/                     # New items needing attention
    ├── Pending_Approval/                 # Waiting for human approval
    ├── Approved/                         # Human-approved, ready to act
    ├── Done/                             # Completed items (archive)
    ├── Plans/                            # Action plans
    ├── Logs/                             # Logs & screenshots
    ├── Social_Posts/                     # LinkedIn post drafts
    ├── Emails/                           # Email drafts
    ├── Briefings/                        # CEO daily briefings
    ├── Schedules/                        # Scheduled tasks
    ├── Templates/                        # File templates
    ├── Rejected/                         # Rejected items
    ├── Inbox/                            # Raw incoming items
    └── Accounting/                       # Financial records
```

---

## Commands Reference

| Command | Description |
|---------|-------------|
| `python orchestrator.py` | Start Gmail Watcher |
| `python watchers/gmail_watcher.py` | Monitor Gmail continuously |
| `python watchers/gmail_watcher.py --test` | Test Gmail connection |
| `python watchers/gmail_watcher.py --dry-run` | Monitor without creating files |
| `python watchers/gmail_watcher.py --process-approved` | Create drafts from approved emails |
| `python watchers/gmail_watcher.py --send-approved` | Send approved email replies |
| `python watchers/linkedin_poster.py` | Post approved LinkedIn content |
| `python watchers/linkedin_poster.py --login` | Login to LinkedIn (save session) |
| `python watchers/linkedin_poster.py --test` | Test mode (no posting) |
| `python setup_gmail.py` | Setup Gmail OAuth (re-authorize) |

---

## Silver Tier Requirements Verification

| # | Requirement | Status |
|---|-------------|:------:|
| 1 | All Bronze requirements | ✅ |
| 2 | Two+ Watcher scripts | ✅ (Gmail, LinkedIn) |
| 3 | Auto-post to LinkedIn | ✅ |
| 4 | Plan.md file creation | ✅ |
| 5 | MCP server for external action | ✅ (Gmail API, Playwright) |
| 6 | Human-in-the-loop approval | ✅ |
| 7 | Basic scheduling | ✅ |
| 8 | Agent Skills implementation | ✅ |

---

## Test Results Summary

| Test | Result |
|------|--------|
| Gmail email sending | ✅ 11/11 sent successfully |
| LinkedIn auto-posting | ✅ 10+ posts published |
| OAuth permissions | ✅ All 3 scopes granted |
| Duplicate prevention | ✅ Working |
| Challenge detection | ✅ Working |
| File management | ✅ All files correctly archived |
| Human approval workflow | ✅ Working end-to-end |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `403 insufficientPermissions` | Run `python setup_gmail.py` to refresh token with send scopes |
| LinkedIn not logged in | Run `python watchers/linkedin_poster.py --login` |
| Challenge page detected | Complete verification in browser; session is saved automatically |
| No approved posts | Create post → move to `Approved/` → run `linkedin_poster.py` |
| Gmail watcher errors | Check `Logs/gmail_watcher_YYYY-MM-DD.log` |
| Token expired | Delete `credentials/gmail_token.pickle` → re-run `setup_gmail.py` |

---

## Security & Privacy

- All data stored locally in Obsidian vault
- OAuth tokens saved locally, never shared
- Human-in-the-loop required for all outbound actions (emails, posts)
- No cloud dependencies beyond Gmail/LinkedIn APIs
- Challenge page detection stops automation immediately for manual intervention

---

## Dependencies

```
google-api-python-client>=2.100.0
google-auth-httplib2>=0.1.0
google-auth-oauthlib>=1.0.0
playwright>=1.40.0
watchdog>=3.0.0
```

Install: `pip install -r requirements.txt && playwright install chromium`

---

## Next Steps (Gold Tier)

- Multi-platform support (Facebook, Instagram, Twitter/X)
- Odoo accounting integration
- Ralph Wiggum loop for autonomous multi-step task completion
- Weekly Business and Accounting Audit with CEO Briefing
- Error recovery and graceful degradation
- Comprehensive audit logging

---

## License & Attribution

**Personal AI Employee — Silver Tier**  
Hackathon 0: Building Autonomous FTEs in 2026  
Built with Playwright, Gmail API, Python, and Obsidian.  
Author: Khansa Tanveer
