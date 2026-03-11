# Gold Tier Implementation Guide

## Overview
Gold Tier adds advanced automation features including multi-platform social media posting, accounting integration, and autonomous multi-step task completion.

## Features Implemented

### 1. Twitter/X Posting (`scripts/twitter_poster.py`)
Post to Twitter/X using browser automation with approval workflow.

**Setup:**
```bash
pip install playwright
playwright install
python scripts/twitter_poster.py --login
```

**Usage:**
```bash
# Create post (requires approval)
python scripts/twitter_poster.py --post "Hello Twitter!"

# Post immediately
python scripts/twitter_poster.py --post-now "Breaking news!"

# Create thread
python scripts/twitter_poster.py --thread "First tweet|||Second tweet|||Third tweet"

# Process approved posts
python scripts/twitter_poster.py --process
```

**Approval Workflow:**
1. Script creates approval file in `Pending_Approval/`
2. Human reviews and moves to `Approved/Social/`
3. Run `--process` to execute approved posts

---

### 2. Odoo Accounting Integration (`scripts/odoo_integration.py`)
Integrate with Odoo ERP for invoicing, payments, and financial reports.

**Setup:**
```bash
# Install Odoo Community Edition (local or cloud)
# Then configure:
python scripts/odoo_integration.py --setup
```

**Configuration (`odoo_config.json`):**
```json
{
  "url": "http://localhost:8069",
  "db": "odoo",
  "username": "admin",
  "api_key": "your-api-key",
  "uid": null
}
```

**Usage:**
```bash
# Test connection
python scripts/odoo_integration.py --test

# Fetch financial reports
python scripts/odoo_integration.py --reports

# Create invoice (via approval workflow)
# Creates approval file in Pending_Approval/
```

**Features:**
- Create customer invoices
- Record payments
- Fetch receivables/payables reports
- Track pending invoices

---

### 3. Ralph Wiggum Loop (`scripts/ralph_wiggum_loop.py`)
Autonomous multi-step task completion using the "Ralph Wiggum" pattern.

**How It Works:**
1. AI receives a task
2. AI works on task
3. AI tries to exit
4. Loop checks: Is task complete?
5. NO → Re-inject prompt, continue working
6. YES → Allow exit

**Usage:**
```bash
# Direct mode (requires Claude Code in PATH)
python scripts/ralph_wiggum_loop.py "Process all files in Needs_Action" --max-iterations 10

# File-based mode
python scripts/ralph_wiggum_loop.py "Generate weekly report" --file-mode
```

**Completion Detection:**
- Promise-based: `<promise>TASK_COMPLETE</promise>`
- File movement: Items moved from Needs_Action to Done
- Plan completion: All checklist items checked

---

### 4. Enhanced Orchestrator
Updated `orchestrator.py` with Gold Tier features:

```bash
# Process Needs_Action and create Plan.md files
python orchestrator.py

# Generate daily briefing
python orchestrator.py --daily-briefing

# Run weekly audit
python orchestrator.py --weekly-audit

# Continuous operation
python orchestrator.py --continuous --interval 60
```

---

## Folder Structure (Gold Tier)

```
Personal-AI-Employe/
├── scripts/
│   ├── twitter_poster.py       # Twitter/X posting
│   ├── odoo_integration.py     # Odoo accounting
│   ├── ralph_wiggum_loop.py    # Autonomous tasks
│   └── mcp_email_client.py     # Email MCP client
├── .claude/skills/
│   ├── email-sending/
│   ├── social-media-posting/
│   ├── approval-workflow/
│   └── scheduled-tasks/
├── Approved/
│   ├── Communications/
│   ├── Payments/
│   └── Social/
├── Rejected/
│   ├── Communications/
│   ├── Payments/
│   ├── Social/
│   └── Expired/
├── Briefings/                  # Daily/Weekly briefings
├── Invoices/                   # Generated invoices
├── Social_Media/
│   └── images/
├── Logs/                       # System logs
├── Plans/                      # Action plans
├── Needs_Action/               # Items to process
├── Pending_Approval/           # Awaiting approval
├── Done/                       # Completed tasks
└── Dashboard_Gold.md           # Gold Tier dashboard
```

---

## Gold Tier Checklist

### Social Media Integration
- [x] LinkedIn posting with approval workflow
- [x] Twitter/X posting with approval workflow
- [ ] Facebook posting (planned)
- [ ] Instagram posting (planned)

### Accounting Integration
- [x] Odoo ERP integration script
- [x] Invoice creation API
- [x] Payment recording API
- [x] Financial reports
- [ ] Auto-categorization of transactions

### Autonomous Operations
- [x] Ralph Wiggum loop implementation
- [x] File-based task tracking
- [x] Completion detection
- [x] Iteration limiting

### Approval Workflow
- [x] Communications category
- [x] Payments category
- [x] Social media category
- [x] Expiration handling

---

## Testing Gold Tier

### 1. Test Twitter Poster
```bash
cd D:\Personal-AI-Employe
python scripts/twitter_poster.py --demo
```

### 2. Test Odoo Integration
```bash
python scripts/odoo_integration.py --test
```

### 3. Test Ralph Wiggum Loop
```bash
python scripts/ralph_wiggum_loop.py "Count files in Needs_Action" --max-iterations 3
```

### 4. Test Orchestrator
```bash
python orchestrator.py --daily-briefing
python orchestrator.py --weekly-audit
```

---

## Next Steps (Platinum Tier)

1. **Cloud Deployment**
   - Deploy to Oracle Cloud Free VM or AWS
   - Set up 24/7 operation
   - Configure health monitoring

2. **Work-Zone Specialization**
   - Cloud owns: Email triage, draft replies, social post drafts
   - Local owns: Approvals, WhatsApp, payments, final actions

3. **Vault Sync**
   - Git-based sync between Cloud and Local
   - Prevent double-work with claim-by-move rule
   - Secure credential management

4. **A2A Communication**
   - Replace file handoffs with direct agent messages
   - Keep vault as audit record

---

## Troubleshooting

### Twitter Poster Issues
- **Not logged in:** Run `python scripts/twitter_poster.py --login`
- **Post failed:** Check session folder `.twitter_session/`
- **Playwright error:** Run `playwright install`

### Odoo Integration Issues
- **Connection failed:** Check `odoo_config.json` URL and credentials
- **Authentication error:** Verify API key in Odoo settings
- **No data returned:** Check database name and permissions

### Ralph Wiggum Loop Issues
- **Claude not found:** Ensure Claude Code is installed and in PATH
- **Max iterations reached:** Task may be too complex, break into smaller steps
- **State file errors:** Delete `Logs/ralph_state.json` and restart

---

## Security Notes

1. **Credentials:** Never commit `odoo_config.json` or session folders to git
2. **Approvals:** All sensitive actions require human approval
3. **Audit Trail:** All actions logged to `Logs/` folder
4. **Rate Limiting:** Implement delays between social media posts

---

*Gold Tier Implementation - Personal AI Employee v0.3*
