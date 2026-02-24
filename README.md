# Personal AI Employee - Bronze Tier

This is a Bronze Tier implementation of the Personal AI Employee as described in the hackathon document.

## Features Implemented

✅ **Obsidian Vault Structure**
- Dashboard.md - Central monitoring dashboard
- Company_Handbook.md - Rules and guidelines for the AI
- Business_Goals.md - Business objectives and metrics

✅ **Basic Folder Structure**
- `/Inbox` - For incoming items
- `/Needs_Action` - For items requiring processing
- `/Done` - For completed items
- `/Plans` - For action plans
- `/Pending_Approval` - For items requiring human approval
- `/Logs` - For system logs

✅ **File System Watcher**
- Monitors a designated drop folder for new files
- Creates action files in `/Needs_Action` when new files are detected
- Copies files to `/Inbox` for processing
- Updates dashboard with new activity

## Setup Instructions

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a drop folder for monitoring:
   ```bash
   mkdir Drop_Folder
   ```

3. Start the file system watcher:
   ```bash
   python filesystem_watcher.py
   ```

4. Place files in the `Drop_Folder` to trigger the AI Employee

## How It Works

1. The file system watcher monitors the `Drop_Folder` for new files
2. When a file is detected, it's copied to the `Inbox` folder
3. An action file is created in the `Needs_Action` folder with metadata
4. The dashboard is updated with the new activity
5. The AI Employee (Claude Code) can then process the action file

## Bronze Tier Requirements Met

- ✅ Obsidian vault with Dashboard.md and Company_Handbook.md
- ✅ One working Watcher script (File system monitoring)
- ✅ Claude Code successfully reading from and writing to the vault
- ✅ Basic folder structure: /Inbox, /Needs_Action, /Done
- ✅ All AI functionality should be implemented as Agent Skills (framework ready)

## Next Steps for Higher Tiers

- **Silver Tier**: Add Gmail and WhatsApp watchers, MCP servers, automated posting
- **Gold Tier**: Full cross-domain integration, accounting system, CEO briefings
- **Platinum Tier**: Cloud deployment, 24/7 operation, advanced security

## Security Notes

- All sensitive operations require human approval
- Audit logs maintained for all actions
- File-based approval system for sensitive operations
- Credentials stored separately from the vault