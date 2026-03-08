# Personal AI Employee - Project Context

## Project Overview

This is a **Bronze Tier** implementation of a **Personal AI Employee** - an autonomous digital FTE (Full-Time Equivalent) that proactively manages personal and business affairs. The system uses **Claude Code** as the reasoning engine and **Obsidian** (Markdown-based) as the management dashboard/GUI.

### Architecture

The system follows a **Perception → Reasoning → Action** pattern:

| Layer | Component | Purpose |
|-------|-----------|---------|
| **Perception** | File System Watcher | Monitors `Drop_Folder` for new files |
| **Reasoning** | Claude Code + Orchestrator | Processes action files, creates plans |
| **Action** | MCP Servers (framework ready) | Executes external actions (email, payments, etc.) |
| **Memory/GUI** | Obsidian Vault | Dashboard, handbook, business goals |

### Core Technologies

- **Python 3.8+** - Watcher scripts and orchestration
- **Claude Code** - AI reasoning engine
- **Obsidian** - Markdown vault for dashboard and knowledge base
- **watchdog** - File system monitoring library

## Directory Structure

```
Personal-AI-Employe/
├── .claude/                    # Claude Code configuration
│   └── skills/                 # Agent Skills implementations
├── .obsidian/                  # Obsidian-specific settings
├── Inbox/                      # Files received for processing
├── Needs_Action/               # Action files requiring processing
├── Done/                       # Completed tasks
├── Plans/                      # Generated action plans
├── Pending_Approval/           # Items awaiting human approval
├── Logs/                       # System logs
├── Drop_Folder/                # Monitored folder for new files
├── Dashboard.md                # Central monitoring dashboard
├── Company_Handbook.md         # Rules and guidelines for AI
├── Business_Goals.md           # Business objectives and metrics
├── filesystem_watcher.py       # File system monitoring script
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
- Claude Code subscription
- Obsidian (optional, for viewing vault)

### Installation

```bash
# Install Python dependencies
pip install -r requirements.txt
```

### Running the System

```bash
# 1. Start the file system watcher (in a separate terminal)
python filesystem_watcher.py

# 2. Place files in Drop_Folder/ to trigger the AI Employee

# 3. Run the orchestrator to process items
python orchestrator.py

# 4. Run orchestrator continuously (checks every 60 seconds)
python orchestrator.py --continuous
```

### Testing the Setup

```bash
# Run setup script to verify configuration
python setup_bronze_tier.py

# Run demo to see Bronze Tier capabilities
python demo_bronze_tier.py
```

## Key Components

### File System Watcher (`filesystem_watcher.py`)

Monitors `Drop_Folder` for new files and:
- Copies files to `Inbox/` for processing
- Creates action files in `Needs_Action/` with metadata
- Updates `Dashboard.md` with new activity
- Supports: `.txt`, `.pdf`, `.docx`, `.xlsx`, `.csv`, `.jpg`, `.png`, `.md`

### Orchestrator (`orchestrator.py`)

Main workflow coordinator that:
- Processes items in `Needs_Action/`
- Creates plan files in `Plans/`
- Moves completed tasks to `Done/`
- Updates dashboard with current status
- Supports continuous operation mode

### Configuration Files

| File | Purpose |
|------|---------|
| `Dashboard.md` | Real-time status, activity log, quick stats |
| `Company_Handbook.md` | AI behavior rules, communication guidelines, financial protocols |
| `Business_Goals.md` | Revenue targets, key metrics, active projects |

## Development Conventions

### Coding Style

- Python scripts use type hints where applicable
- Logging configured to both file and console
- Scripts are executable with `#!/usr/bin/env python3` shebang
- Follow PEP 8 conventions

### Logging

- `watcher.log` - File system watcher events
- `orchestrator.log` - Orchestrator cycle events
- Format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`

### Folder Workflow

```
Drop_Folder → (Watcher detects) → Inbox/ + Needs_Action/
Needs_Action/ → (Orchestrator processes) → Plans/
Plans/ → (Task completed) → Done/
Sensitive actions → Pending_Approval/ → (Human approval) → Action
```

## Tier Progression

This is a **Bronze Tier** implementation. Higher tiers add:

| Tier | Additional Features |
|------|---------------------|
| **Silver** | Gmail/WhatsApp watchers, MCP servers, automated posting |
| **Gold** | Cross-domain integration, Odoo accounting, CEO briefings |
| **Platinum** | Cloud deployment, 24/7 operation, domain specialization |

## Security Notes

- All sensitive operations require human approval via `Pending_Approval/`
- Audit logs maintained in `Logs/` and log files
- Credentials stored separately from vault (never committed)
- File-based approval workflow for sensitive actions

## Repository

- **Remote:** https://github.com/Rao-Faizan/Personal-AI-Employe.git
- **License:** Not specified (check repository for details)

## Related Documentation

- `Personal AI Employee Hackathon 0_ Building Autonomous FTEs in 2026.md` - Full architectural blueprint and hackathon guide
- `README.md` - Setup instructions and Bronze Tier requirements
