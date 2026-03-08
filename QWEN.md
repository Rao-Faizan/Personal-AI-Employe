# Personal AI Employee - Project Context

## Project Overview

This is a **Silver Tier** implementation of a **Personal AI Employee** - an autonomous digital FTE (Full-Time Equivalent) that proactively manages personal and business affairs. The system uses **Qwen Code** as the reasoning engine and **Obsidian** (Markdown-based) as the management dashboard/GUI.

### Architecture

The system follows a **Perception → Reasoning → Action** pattern:

| Layer | Component | Purpose |
|-------|-----------|---------|
| **Perception** | File System, Gmail, WhatsApp Watchers | Monitor inputs for new items |
| **Reasoning** | Qwen Code + Orchestrator | Processes action files, creates plans |
| **Action** | MCP Servers (Email, Social Media) | Executes external actions |
| **Memory/GUI** | Obsidian Vault | Dashboard, handbook, business goals |

### Core Technologies

- **Python 3.8+** - Watcher scripts and orchestration
- **Qwen Code** - AI reasoning engine
- **Obsidian** - Markdown vault for dashboard and knowledge base
- **watchdog** - File system monitoring
- **Google API** - Gmail integration
- **Playwright** - Browser automation (WhatsApp Web)
- **MCP Servers** - External action execution

## Directory Structure

```
Personal-AI-Employe/
├── .claude/                    # Qwen Code configuration
│   └── skills/                 # Agent Skills implementations
│       ├── browsing-with-playwright/
│       ├── email-sending/
│       ├── social-media-posting/
│       ├── approval-workflow/
│       └── scheduled-tasks/
├── .obsidian/                  # Obsidian-specific settings
├── Inbox/                      # Files received for processing
├── Needs_Action/               # Action files requiring processing
├── Done/                       # Completed tasks
├── Plans/                      # Generated action plans
├── Pending_Approval/           # Items awaiting human approval
├── Approved/                   # Approved actions ready for execution
│   ├── Communications/
│   ├── Payments/
│   └── Social/
├── Rejected/                   # Rejected actions with reasons
├── Logs/                       # System logs
├── Drop_Folder/                # Monitored folder for new files
├── Briefings/                  # Daily/Weekly briefings
├── Dashboard.md                # Central monitoring dashboard
├── Company_Handbook.md         # Rules and guidelines for AI
├── Business_Goals.md           # Business objectives and metrics
├── filesystem_watcher.py       # File system monitoring script
├── gmail_watcher.py            # Gmail monitoring script
├── orchestrator.py             # Main workflow coordinator
├── setup_bronze_tier.py        # Setup script for Bronze Tier
├── demo_bronze_tier.py         # Demo script for Bronze Tier
├── requirements.txt            # Python dependencies
└── README.md                   # Project documentation
```

## Building and Running

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Node.js v24+ LTS (for MCP servers)
- Qwen Code subscription
- Obsidian (optional, for viewing vault)
- Google Cloud Console account (for Gmail API)

### Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install MCP servers (for Silver Tier features)
npm install -g @anthropic/gmail-mcp
npm install -g @linkedin/mcp-server
npm install -g @twitter/mcp-server

# Install Playwright browsers (for WhatsApp watcher)
playwright install
```

### Gmail API Setup (Required for Gmail Watcher)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Gmail API
4. Create OAuth 2.0 credentials
5. Download `credentials.json` and place in project root
6. Run authentication: `python gmail_watcher.py --auth`

### Running the System

```bash
# 1. Start the file system watcher (in a separate terminal)
python filesystem_watcher.py

# 2. Start Gmail watcher (after authentication)
python gmail_watcher.py

# 3. Place files in Drop_Folder/ to trigger the AI Employee

# 4. Run the orchestrator to process items
python orchestrator.py

# 5. Run orchestrator continuously (checks every 60 seconds)
python orchestrator.py --continuous
```

### Setting Up Scheduled Tasks

**Windows (Task Scheduler):**
```powershell
# Daily Briefing at 7 AM
$action = New-ScheduledTaskAction -Execute "python" `
  -Argument "orchestrator.py --daily-briefing" `
  -WorkingDirectory "C:\path\to\Personal-AI-Employe"
$trigger = New-ScheduledTaskTrigger -Daily -At 7:00AM
Register-ScheduledTask -TaskName "AI_Employee_Daily_Briefing" `
  -Action $action -Trigger $trigger
```

**macOS/Linux (cron):**
```bash
crontab -e
# Add: 0 7 * * * cd /path/to/project && python3 orchestrator.py --daily-briefing
```

## Key Components

### Watchers (Perception Layer)

| Watcher | Purpose | Status |
|---------|---------|--------|
| `filesystem_watcher.py` | Monitors `Drop_Folder` for new files | ✅ Bronze |
| `gmail_watcher.py` | Monitors Gmail for new emails | ✅ Silver |
| `whatsapp_watcher.py` | Monitors WhatsApp Web for messages | 🔄 Planned |

### Orchestrator (`orchestrator.py`)

Main workflow coordinator that:
- Processes items in `Needs_Action/`
- Creates plan files in `Plans/`
- Manages approval workflow
- Moves completed tasks to `Done/`
- Updates dashboard with current status
- Supports continuous operation mode
- Generates daily/weekly briefings

### Agent Skills (.claude/skills/)

| Skill | Purpose | Tier |
|-------|---------|------|
| `browsing-with-playwright` | Browser automation via Playwright MCP | Bronze |
| `email-sending` | Send emails via Gmail MCP with approval workflow | Silver |
| `social-media-posting` | Post to LinkedIn, Twitter with scheduling | Silver |
| `approval-workflow` | Human-in-the-loop approval system | Silver |
| `scheduled-tasks` | Cron/Task Scheduler integration | Silver |

### Configuration Files

| File | Purpose |
|------|---------|
| `Dashboard.md` | Real-time status, activity log, quick stats |
| `Company_Handbook.md` | AI behavior rules, communication guidelines, financial protocols |
| `Business_Goals.md` | Revenue targets, key metrics, active projects |

## Silver Tier Features

### 1. Multiple Watchers
- **File System Watcher** - Monitors local drop folder
- **Gmail Watcher** - Checks for new important emails every 2 minutes
- **WhatsApp Watcher** - Monitors WhatsApp Web for keyword-triggered messages

### 2. Social Media Automation
- LinkedIn post generation and scheduling
- Twitter/X thread creation
- Human approval required before posting
- Content calendar management

### 3. Email Integration
- Gmail API integration
- Draft creation for new contacts
- Auto-reply for known contacts
- Attachment handling

### 4. Human-in-the-Loop Approval
- File-based approval workflow
- Categories: Communications, Payments, Social Media
- Priority levels: High, Medium, Low
- Expiration handling for stale requests

### 5. Scheduled Tasks
- Daily briefing generation (7 AM)
- Weekly business audit (Sunday 11 PM)
- Monthly subscription check
- Process Needs_Action every 30 minutes

## Development Conventions

### Coding Style

- Python scripts use type hints where applicable
- Logging configured to both file and console
- Scripts are executable with `#!/usr/bin/env python3` shebang
- Follow PEP 8 conventions

### Logging

- `watcher.log` - File system watcher events
- `gmail_watcher.log` - Gmail watcher events
- `orchestrator.log` - Orchestrator cycle events
- Format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`

### Folder Workflow

```
Drop_Folder/ → (Watcher detects) → Inbox/ + Needs_Action/
Gmail → (Watcher detects) → Needs_Action/

Needs_Action/ → (Orchestrator processes) → Plans/
Plans/ → (Task completed) → Done/

Sensitive actions → Pending_Approval/ → (Human moves to Approved/) → Action executed
Approved/ → (After execution) → Done/
Rejected/ → (Logged with reason)
```

## Tier Progression

| Tier | Status | Features |
|------|--------|----------|
| **Bronze** | ✅ Complete | File watcher, basic folders, Qwen integration |
| **Silver** | ✅ Complete | Gmail watcher, email sending, social posting, approval workflow, scheduling |
| **Gold** | 🔄 Planned | Odoo integration, Facebook/Instagram, CEO briefings, Ralph Wiggum loop |
| **Platinum** | 📋 Planned | Cloud deployment, 24/7 operation, domain specialization |

## Security Notes

- All sensitive operations require human approval via `Pending_Approval/`
- Audit logs maintained in `Logs/` and log files
- Credentials stored separately from vault (`.env`, `token.json`)
- File-based approval workflow for sensitive actions
- OAuth tokens never committed to git

### Credential Management

```bash
# .env file (NEVER commit to git)
GMAIL_CLIENT_ID=your_client_id
GMAIL_CLIENT_SECRET=your_client_secret
LINKEDIN_ACCESS_TOKEN=your_token
TWITTER_BEARER_TOKEN=your_token
```

## Repository

- **Remote:** https://github.com/Rao-Faizan/Personal-AI-Employe.git
- **License:** Not specified (check repository for details)

## Related Documentation

- `Personal AI Employee Hackathon 0_ Building Autonomous FTEs in 2026.md` - Full architectural blueprint and hackathon guide
- `README.md` - Setup instructions and Bronze Tier requirements
- `.claude/skills/*/SKILL.md` - Individual skill documentation

## Silver Tier Checklist

- [x] All Bronze requirements
- [x] Two or more Watcher scripts (File System + Gmail)
- [x] Qwen reasoning loop that creates Plan.md files
- [x] One working MCP server for external action (Email)
- [x] Human-in-the-loop approval workflow
- [x] Basic scheduling via cron/Task Scheduler
- [x] All AI functionality as Agent Skills
- [ ] Automatically Post on LinkedIn (requires API credentials)
- [ ] WhatsApp watcher (requires Playwright setup)
