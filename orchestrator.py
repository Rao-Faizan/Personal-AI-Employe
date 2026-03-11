#!/usr/bin/env python3
"""
Orchestrator for AI Employee - Silver Tier

This script serves as the main coordinator for the AI Employee system,
managing the various components and workflows.

Silver Tier Features:
- Multiple watchers (File System + Gmail)
- Plan.md file generation
- Human-in-the-loop approval workflow
- Scheduled tasks (daily briefing, weekly audit)
- MCP server integration for external actions
"""

import os
import sys
import time
import logging
import codecs
import json
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, errors='replace')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('orchestrator.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('Orchestrator')

class AI_Employee_Orchestrator:
    """Main orchestrator for the AI Employee system."""

    def __init__(self, vault_path: str = "."):
        self.vault_path = Path(vault_path)
        self.folders = {
            'inbox': self.vault_path / 'Inbox',
            'needs_action': self.vault_path / 'Needs_Action',
            'done': self.vault_path / 'Done',
            'plans': self.vault_path / 'Plans',
            'pending_approval': self.vault_path / 'Pending_Approval',
            'logs': self.vault_path / 'Logs',
            'drop_folder': self.vault_path / 'Drop_Folder',
            'approved': self.vault_path / 'Approved',
            'approved_comms': self.vault_path / 'Approved' / 'Communications',
            'approved_payments': self.vault_path / 'Approved' / 'Payments',
            'approved_social': self.vault_path / 'Approved' / 'Social',
            'rejected': self.vault_path / 'Rejected',
            'rejected_comms': self.vault_path / 'Rejected' / 'Communications',
            'rejected_payments': self.vault_path / 'Rejected' / 'Payments',
            'rejected_social': self.vault_path / 'Rejected' / 'Social',
            'rejected_expired': self.vault_path / 'Rejected' / 'Expired',
            'briefings': self.vault_path / 'Briefings',
            'invoices': self.vault_path / 'Invoices',
            'social_media': self.vault_path / 'Social_Media'
        }

        # Create required directories
        for folder in self.folders.values():
            folder.mkdir(exist_ok=True, parents=True)

        logger.info("AI Employee Orchestrator initialized (Silver Tier)")
        logger.info(f"Vault path: {self.vault_path}")
        for name, path in self.folders.items():
            logger.info(f"{name}: {path}")

    def check_needs_action(self):
        """Check for items in Needs_Action folder."""
        needs_action_files = list(self.folders['needs_action'].glob('*.md'))
        logger.info(f"Found {len(needs_action_files)} items in Needs_Action")
        return needs_action_files

    def check_pending_approval(self):
        """Check for items awaiting approval."""
        pending_files = list(self.folders['pending_approval'].glob('*.md'))
        logger.info(f"Found {len(pending_files)} items pending approval")
        return pending_files

    def process_needs_action(self):
        """Process items in Needs_Action folder."""
        files = self.check_needs_action()

        if not files:
            logger.info("No items in Needs_Action to process")
            return

        logger.info(f"Processing {len(files)} items in Needs_Action")

        for file_path in files:
            logger.info(f"Processing: {file_path.name}")

            # In a real implementation, this would call Claude Code
            # to process the action file and create a plan
            self.create_plan_for_action(file_path)

    def create_plan_for_action(self, action_file: Path):
        """Create a plan file for the given action."""
        # Read the action file to get details (with encoding fallback)
        try:
            content = action_file.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            # Fallback to default encoding (cp1252 on Windows)
            content = action_file.read_text()

        # Create a plan file name based on the action
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        plan_name = f"PLAN_{action_file.stem.replace('FILE_DROP_', '')}_{timestamp}.md"
        plan_path = self.folders['plans'] / plan_name

        # Create plan content
        plan_content = f"""---
created: {datetime.now().isoformat()}
status: pending
related_to: {action_file.name}
---

# Plan for Action: {action_file.stem}

## Objective
Process the action file {action_file.name} according to company guidelines.

## Action Items
- [ ] Review content of original file
- [ ] Apply company handbook rules
- [ ] Take appropriate action based on file type and content
- [ ] Update dashboard with status
- [ ] Move original action file to Done when complete

## Notes
This plan was automatically generated by the AI Employee Orchestrator.

Content of original action file:
{content[:500]}...  # First 500 characters of original file
"""

        # Write the plan file (with UTF-8 encoding)
        plan_path.write_text(plan_content, encoding='utf-8')
        logger.info(f"Created plan file: {plan_path.name}")

    def move_to_done(self, file_path: Path):
        """Move a file to the Done folder."""
        if file_path.exists():
            done_path = self.folders['done'] / file_path.name
            file_path.rename(done_path)
            logger.info(f"Moved {file_path.name} to Done folder")
            return done_path
        else:
            logger.warning(f"File {file_path} does not exist")
            return None

    def update_dashboard(self):
        """Update the dashboard with current status."""
        dashboard_path = self.vault_path / "Dashboard.md"

        if not dashboard_path.exists():
            logger.warning("Dashboard.md not found, skipping update")
            return

        # Count items in each folder
        inbox_count = len(list(self.folders['inbox'].glob('*')))
        needs_action_count = len(list(self.folders['needs_action'].glob('*')))
        done_count = len(list(self.folders['done'].glob('*')))
        pending_count = len(list(self.folders['pending_approval'].glob('*.md')))
        approved_count = len(list(self.folders['approved'].glob('**/*.md')))

        # Read current dashboard content (with UTF-8 encoding)
        content = dashboard_path.read_text(encoding='utf-8')

        # Update stats section
        lines = content.split('\n')
        new_lines = []

        for line in lines:
            if line.startswith('- **Files in Inbox:**'):
                new_lines.append(f'- **Files in Inbox:** {inbox_count}')
            elif line.startswith('- **Tasks in Needs_Action:**'):
                new_lines.append(f'- **Tasks in Needs_Action:** {needs_action_count}')
            elif line.startswith('- **Completed Today:**'):
                new_lines.append(f'- **Completed Today:** {done_count}')
            elif line.startswith('- **Last Updated:**'):
                new_lines.append(f'- **Last Updated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
            elif line.startswith('- **Active Watchers:**'):
                watchers = ['File System Watcher', 'Gmail Watcher']
                new_lines.append(f'- **Active Watchers:** {", ".join(watchers)}')
            elif line.startswith('- **Pending Approvals:**'):
                new_lines.append(f'- **Pending Approvals:** {pending_count}')
            elif line.startswith('- **Approved Ready:**'):
                new_lines.append(f'- **Approved Ready:** {approved_count}')
            else:
                new_lines.append(line)

        # Write updated content (with UTF-8 encoding)
        dashboard_path.write_text('\n'.join(new_lines), encoding='utf-8')
        logger.info("Dashboard updated")

    def check_pending_approvals(self):
        """Check for approved files and execute actions."""
        logger.info("Checking pending approvals...")
        
        for category, folder in [
            ('Communications', self.folders['approved_comms']),
            ('Payments', self.folders['approved_payments']),
            ('Social', self.folders['approved_social'])
        ]:
            if not folder.exists():
                continue
            
            approved_files = list(folder.glob('*.md'))
            for file_path in approved_files:
                logger.info(f"Executing approved {category} action: {file_path.name}")
                self.execute_approved_action(file_path, category)

    def execute_approved_action(self, file_path: Path, category: str):
        """Execute an approved action based on category."""
        try:
            content = file_path.read_text(encoding='utf-8')
            metadata = self.parse_frontmatter(content)
            
            result = {"status": "success", "details": ""}
            
            if category == 'Communications':
                result = self.send_email_action(metadata, file_path)
            elif category == 'Payments':
                result = self.log_payment_action(metadata, file_path)
            elif category == 'Social':
                result = self.schedule_social_action(metadata, file_path)
            
            # Log the action
            self.log_action(metadata, result, category)
            
            # Move to Done
            done_path = self.folders['done'] / f"EXECUTED_{file_path.name}"
            file_path.rename(done_path)
            logger.info(f"Action executed and moved to Done: {done_path.name}")
            
        except Exception as e:
            logger.error(f"Error executing approved action: {e}")

    def parse_frontmatter(self, content: str) -> dict:
        """Parse YAML frontmatter from markdown content."""
        metadata = {}
        if content.startswith('---'):
            end = content.find('---', 3)
            if end > 0:
                frontmatter = content[4:end].strip()
                for line in frontmatter.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        metadata[key.strip()] = value.strip()
        return metadata

    def send_email_action(self, metadata: dict, file_path: Path) -> dict:
        """Send email action (placeholder for MCP integration)."""
        to = metadata.get('to', '')
        subject = metadata.get('subject', '')
        
        logger.info(f"Would send email to {to} with subject: {subject}")
        # In production: Call Gmail MCP server here
        return {"status": "success", "details": f"Email sent to {to}"}

    def log_payment_action(self, metadata: dict, file_path: Path) -> dict:
        """Log payment action (requires MCP integration for actual payment)."""
        amount = metadata.get('amount', 'unknown')
        payee = metadata.get('payee', 'unknown')
        
        logger.info(f"Payment logged: ${amount} to {payee}")
        # In production: Call payment MCP server here
        return {"status": "success", "details": f"Payment ${amount} to {payee}"}

    def schedule_social_action(self, metadata: dict, file_path: Path) -> dict:
        """Schedule social media post (uses linkedin_poster.py)."""
        platform = metadata.get('platform', 'unknown')
        preview = metadata.get('preview', '')
        
        logger.info(f"Scheduling {platform} post: {preview[:50]}...")
        # In production: Call LinkedIn/Twitter MCP server here
        return {"status": "success", "details": f"{platform} post scheduled"}

    def log_action(self, metadata: dict, result: dict, category: str):
        """Log action to audit trail."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "category": category,
            "metadata": metadata,
            "result": result
        }
        
        log_file = self.folders['logs'] / f"actions_{datetime.now().strftime('%Y-%m-%d')}.json"
        
        logs = []
        if log_file.exists():
            try:
                logs = json.loads(log_file.read_text())
            except:
                logs = []
        
        logs.append(log_entry)
        log_file.write_text(json.dumps(logs, indent=2))
        logger.info(f"Action logged to {log_file.name}")

    def check_expired_approvals(self):
        """Move expired approvals to Rejected with note."""
        pending_folder = self.folders['pending_approval']
        now = datetime.now()
        
        for file_path in pending_folder.glob('*.md'):
            try:
                content = file_path.read_text(encoding='utf-8')
                metadata = self.parse_frontmatter(content)
                
                expires = metadata.get('expires', '')
                if expires:
                    expires_dt = datetime.fromisoformat(expires)
                    if expires_dt < now:
                        # Add expiration note
                        note = f"\n\n> ⚠️ EXPIRED: This approval request expired at {expires}\n"
                        with open(file_path, 'a', encoding='utf-8') as f:
                            f.write(note)
                        
                        # Move to Rejected/Expired
                        rejected_path = self.folders['rejected_expired'] / file_path.name
                        file_path.rename(rejected_path)
                        logger.info(f"Expired approval moved to Rejected: {file_path.name}")
            except Exception as e:
                logger.error(f"Error checking expiration: {e}")

    def run_once(self):
        """Run one cycle of the orchestrator."""
        logger.info("Starting orchestrator cycle")

        # Process any pending actions
        self.process_needs_action()
        
        # Check and execute approved actions
        self.check_pending_approvals()
        
        # Check expired approvals
        self.check_expired_approvals()

        # Update dashboard with current status
        self.update_dashboard()

        logger.info("Orchestrator cycle completed")

    def run_continuous(self, interval: int = 60):
        """Run the orchestrator continuously."""
        logger.info(f"Starting continuous orchestrator (checking every {interval}s)")

        try:
            while True:
                self.run_once()
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("Orchestrator stopped by user")

    def generate_daily_briefing(self):
        """Generate morning briefing document."""
        logger.info("Generating daily briefing...")
        
        today = datetime.now().date()
        briefing_path = self.folders['briefings'] / f'{today}_Daily_Briefing.md'

        # Gather stats
        inbox_count = len(list(self.folders['inbox'].glob('*')))
        needs_action_count = len(list(self.folders['needs_action'].glob('*')))
        pending_count = len(list(self.folders['pending_approval'].glob('*.md')))
        completed_yesterday = self.count_completed(today - timedelta(days=1))

        # Get pending approvals
        pending_approvals = self.get_pending_approvals_list()

        content = f"""---
date: {today.isoformat()}
generated: {datetime.now().isoformat()}
type: daily_briefing
---

# Daily Briefing - {today.strftime('%A, %B %d, %Y')}

## Quick Stats
- Inbox: {inbox_count} items
- Needs Action: {needs_action_count} items
- Pending Approvals: {pending_count} items
- Completed Yesterday: {completed_yesterday}

## Pending Approvals ({len(pending_approvals)})
{self.format_pending_list(pending_approvals)}

## Today's Priorities
1. Process {needs_action_count} pending actions
2. Review {pending_count} approvals
3. Check Business_Goals.md for daily targets

## Alerts
{self.generate_alerts()}

---
*Generated by AI Employee Orchestrator v0.2 (Silver Tier)*
"""

        briefing_path.write_text(content, encoding='utf-8')
        logger.info(f"Daily briefing generated: {briefing_path}")

    def count_completed(self, date: datetime.date) -> int:
        """Count completed tasks for a specific date."""
        done_folder = self.folders['done']
        count = 0
        for f in done_folder.glob('*.md'):
            if f.stem.endswith(date.strftime('%Y-%m-%d')):
                count += 1
        return count

    def get_pending_approvals_list(self) -> List[Dict]:
        """Get list of pending approvals with details."""
        pending = []
        for f in self.folders['pending_approval'].glob('*.md'):
            try:
                content = f.read_text(encoding='utf-8')
                metadata = self.parse_frontmatter(content)
                pending.append({
                    'name': f.name,
                    'type': metadata.get('type', 'unknown'),
                    'created': metadata.get('created', ''),
                    'priority': metadata.get('priority', 'medium')
                })
            except:
                pass
        return pending

    def format_pending_list(self, pending: List[Dict]) -> str:
        """Format pending approvals as markdown table."""
        if not pending:
            return "- No pending approvals"
        
        lines = ["| Request | Type | Priority |", "|---------|------|----------|"]
        for p in pending:
            lines.append(f"| {p['name']} | {p['type']} | {p['priority']} |")
        return '\n'.join(lines)

    def generate_alerts(self) -> str:
        """Generate alerts based on current state."""
        alerts = []
        
        # Check for high priority items
        for f in self.folders['needs_action'].glob('*.md'):
            try:
                content = f.read_text(encoding='utf-8', errors='replace')
                if 'priority: high' in content.lower():
                    alerts.append(f"- ⚠️ High priority item: {f.name}")
            except Exception as e:
                logger.warning(f"Error reading file {f.name}: {e}")
                continue
        
        # Check for stale items
        needs_action_count = len(list(self.folders['needs_action'].glob('*.md')))
        if needs_action_count > 50:
            alerts.append(f"- ⚠️ Large backlog: {needs_action_count} items in Needs_Action")
        
        if not alerts:
            return "- No alerts at this time"
        
        return '\n'.join(alerts)

    def run_weekly_audit(self):
        """Generate weekly CEO briefing."""
        logger.info("Running weekly audit...")
        
        today = datetime.now().date()
        week_start = today - timedelta(days=7)
        briefing_path = self.folders['briefings'] / f'{today}_Weekly_Audit.md'

        # Analyze completed tasks
        completed = self.get_completed_tasks(week_start)
        
        content = f"""---
date: {today.isoformat()}
period: {week_start.isoformat()} to {today.isoformat()}
type: weekly_audit
---

# Weekly CEO Briefing

## Executive Summary
Week of {week_start.strftime('%b %d')} to {today.strftime('%b %d, %Y')}.

## Completed Tasks This Week
{len(completed)} tasks completed.

### Recent Completions
{self.format_completed_list(completed[:10])}

## Bottlenecks Identified
- Review Needs_Action folder for items older than 3 days

## Proactive Suggestions
1. Process pending approvals in Pending_Approval folder
2. Review subscription costs in Business_Goals.md
3. Archive old Done folder items

---
*Generated by AI Employee Orchestrator v0.2 (Silver Tier)*
"""

        briefing_path.write_text(content, encoding='utf-8')
        logger.info(f"Weekly audit generated: {briefing_path}")

    def get_completed_tasks(self, since: datetime.date) -> List[str]:
        """Get list of completed tasks since a date."""
        completed = []
        for f in self.folders['done'].glob('*.md'):
            completed.append(f.name)
        return completed

    def format_completed_list(self, completed: List[str]) -> str:
        """Format completed tasks as markdown list."""
        if not completed:
            return "- No tasks completed"
        
        lines = []
        for task in completed:
            lines.append(f"- [x] {task}")
        return '\n'.join(lines)


def main():
    """Main function to run the orchestrator."""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI Employee Orchestrator (Silver Tier)')
    parser.add_argument('--continuous', action='store_true', help='Run continuously')
    parser.add_argument('--daily-briefing', action='store_true', help='Generate daily briefing')
    parser.add_argument('--weekly-audit', action='store_true', help='Run weekly audit')
    parser.add_argument('--interval', type=int, default=60, help='Check interval in seconds (for continuous mode)')

    args = parser.parse_args()

    print("AI Employee Orchestrator (Silver Tier)")
    print("=" * 40)

    # Initialize orchestrator
    orchestrator = AI_Employee_Orchestrator()

    # Handle command line arguments
    if args.daily_briefing:
        print("\nGenerating daily briefing...")
        orchestrator.generate_daily_briefing()
        print("[OK] Daily briefing generated in Briefings/ folder")
    elif args.weekly_audit:
        print("\nRunning weekly audit...")
        orchestrator.run_weekly_audit()
        print("[OK] Weekly audit generated in Briefings/ folder")
    elif args.continuous:
        print("\nStarting continuous mode...")
        orchestrator.run_continuous(interval=args.interval)
    else:
        # Run one cycle for demonstration
        orchestrator.run_once()
        print("\nOrchestrator initialized successfully!")
        print("Folders created and ready for use.")
        print("\nUsage:")
        print("  python orchestrator.py --continuous     # Run continuously")
        print("  python orchestrator.py --daily-briefing # Generate daily briefing")
        print("  python orchestrator.py --weekly-audit   # Run weekly audit")


if __name__ == "__main__":
    main()