---
name: scheduled-tasks
description: |
  Schedule and manage recurring tasks via cron (Linux/Mac) or Task Scheduler (Windows).
  Handles daily briefings, weekly audits, periodic checks, and automated reports.
---

# Scheduled Tasks Skill

Automate recurring AI Employee operations with system schedulers.

## Supported Schedulers

| Platform | Scheduler | Skill Level |
|----------|-----------|-------------|
| Windows | Task Scheduler | ✅ Supported |
| macOS | cron / launchd | ✅ Supported |
| Linux | cron / systemd | ✅ Supported |

## Task Categories

| Task | Frequency | Best Time | Priority |
|------|-----------|-----------|----------|
| Daily Briefing | Daily | 7:00 AM | High |
| Process Needs_Action | Every 30 min | Business hours | High |
| Check Pending Approvals | Every hour | Business hours | Medium |
| Update Dashboard | Every 15 min | All day | Low |
| Weekly Audit | Weekly | Sunday 11 PM | High |
| Subscription Check | Monthly | 1st of month | Medium |
| Backup Verification | Weekly | Saturday 2 AM | High |

## Windows Task Scheduler Setup

### Create Scheduled Task via PowerShell

```powershell
# Daily Briefing at 7 AM daily
$action = New-ScheduledTaskAction -Execute "python" `
  -Argument "C:\Users\Rao Faizan\Documents\GitHub\Personal-AI-Employe\orchestrator.py --daily-briefing" `
  -WorkingDirectory "C:\Users\Rao Faizan\Documents\GitHub\Personal-AI-Employe"

$trigger = New-ScheduledTaskTrigger -Daily -At 7:00AM

$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME `
  -LogonType S4U -RunLevel Highest

Register-ScheduledTask -TaskName "AI_Employee_Daily_Briefing" `
  -Action $action -Trigger $trigger -Principal $principal `
  -Description "Generate daily AI Employee briefing"
```

### Process Needs_Action Every 30 Minutes

```powershell
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) `
  -RepetitionInterval (New-TimeSpan -Minutes 30)

Register-ScheduledTask -TaskName "AI_Employee_Process_Actions" `
  -Action $action -Trigger $trigger -Principal $principal `
  -Description "Process Needs_Action folder every 30 minutes"
```

### Weekly Audit - Sunday 11 PM

```powershell
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 11:00PM

Register-ScheduledTask -TaskName "AI_Employee_Weekly_Audit" `
  -Action $action -Trigger $trigger -Principal $principal `
  -Description "Weekly business audit and CEO briefing"
```

### Manage Tasks

```powershell
# List all AI Employee tasks
Get-ScheduledTask -TaskName "AI_Employee_*"

# View task history
Get-ScheduledTaskInfo -TaskName "AI_Employee_Daily_Briefing"

# Run task manually
Start-ScheduledTask -TaskName "AI_Employee_Process_Actions"

# Disable task
Disable-ScheduledTask -TaskName "AI_Employee_Update_Dashboard"

# Delete task
Unregister-ScheduledTask -TaskName "AI_Employee_Old_Task" -Confirm
```

## macOS / Linux cron Setup

### Edit crontab

```bash
crontab -e
```

### Add Entries

```cron
# Daily Briefing at 7 AM
0 7 * * * cd /path/to/Personal-AI-Employe && python3 orchestrator.py --daily-briefing >> logs/cron_daily.log 2>&1

# Process actions every 30 minutes during business hours (8 AM - 6 PM)
*/30 8-18 * * 1-5 cd /path/to/Personal-AI-Employe && python3 orchestrator.py --process-actions >> logs/cron_actions.log 2>&1

# Weekly audit Sunday 11 PM
0 23 * * 0 cd /path/to/Personal-AI-Employe && python3 orchestrator.py --weekly-audit >> logs/cron_weekly.log 2>&1

# Monthly subscription check - 1st of month at 9 AM
0 9 1 * * cd /path/to/Personal-AI-Employe && python3 orchestrator.py --subscription-check >> logs/cron_monthly.log 2>&1
```

### Verify cron Jobs

```bash
# List current cron jobs
crontab -l

# Check cron logs (macOS)
tail -f /var/log/system.log | grep cron

# Check cron logs (Linux)
tail -f /var/log/cron
```

## Orchestrator CLI Flags

Add these flags to `orchestrator.py` for scheduled execution:

```python
# In orchestrator.py main()
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--daily-briefing', action='store_true',
                    help='Generate daily briefing')
parser.add_argument('--weekly-audit', action='store_true',
                    help='Run weekly business audit')
parser.add_argument('--subscription-check', action='store_true',
                    help='Check subscription usage')
parser.add_argument('--process-actions', action='store_true',
                    help='Process Needs_Action folder')

args = parser.parse_args()

if args.daily_briefing:
    orchestrator.generate_daily_briefing()
elif args.weekly_audit:
    orchestrator.run_weekly_audit()
# ... etc
```

## Task Templates

### Daily Briefing Task

```python
# orchestrator.py
def generate_daily_briefing(self):
    """Generate morning briefing document."""
    briefing_path = self.vault_path / 'Briefings' / f'{date.today()}_Daily_Briefing.md'

    # Gather stats
    inbox_count = len(list(self.folders['inbox'].glob('*')))
    needs_action_count = len(list(self.folders['needs_action'].glob('*')))
    completed_yesterday = self.count_completed(date.today() - timedelta(days=1))

    # Get pending approvals
    pending = self.get_pending_approvals()

    content = f"""---
date: {date.today().isoformat()}
generated: {datetime.now().isoformat()}
type: daily_briefing
---

# Daily Briefing - {date.today().strftime('%A, %B %d, %Y')}

## Quick Stats
- Inbox: {inbox_count} items
- Needs Action: {needs_action_count} items
- Completed Yesterday: {completed_yesterday}

## Pending Approvals ({len(pending)})
{self.format_pending_list(pending)}

## Today's Priorities
1. Process {needs_action_count} pending actions
2. Review {len(pending)} approvals
3. [Auto-generated based on Business_Goals.md]

## Alerts
{self.generate_alerts()}
"""

    briefing_path.write_text(content)
    logger.info(f"Daily briefing generated: {briefing_path}")
```

### Weekly Audit Task

```python
# orchestrator.py
def run_weekly_audit(self):
    """Generate weekly CEO briefing."""
    from datetime import datetime, timedelta

    week_start = datetime.now() - timedelta(days=7)
    briefing_path = self.vault_path / 'Briefings' / f'{date.today()}_Weekly_Audit.md'

    # Analyze completed tasks
    completed = self.get_completed_tasks(week_start)
    revenue = self.calculate_weekly_revenue()
    bottlenecks = self.identify_bottlenecks()

    # Subscription audit
    subscriptions = self.audit_subscriptions()

    content = f"""---
date: {date.today().isoformat()}
period: {week_start.date()} to {date.today().date()}
type: weekly_audit
---

# Weekly CEO Briefing

## Executive Summary
{self.generate_summary(revenue, completed)}

## Revenue This Week
- Total: ${revenue:,.2f}
- Transactions: {len(revenue)}
- Trend: {self.calculate_trend()}

## Completed Tasks
{self.format_completed_tasks(completed)}

## Bottlenecks Identified
{self.format_bottlenecks(bottlenecks)}

## Subscription Audit
{self.format_subscription_alerts(subscriptions)}

## Proactive Suggestions
{self.generate_suggestions()}
"""

    briefing_path.write_text(content)
    logger.info(f"Weekly audit generated: {briefing_path}")
```

## Monitoring & Alerts

### Health Check Script

```python
# health_check.py
import subprocess
import sys

def check_scheduled_tasks():
    """Verify all scheduled tasks are running."""
    issues = []

    # Check Windows Task Scheduler
    result = subprocess.run(
        ['schtasks', '/Query', '/TN', 'AI_Employee_*', '/FO', 'LIST'],
        capture_output=True, text=True
    )

    if 'Ready' not in result.stdout:
        issues.append("Some tasks not in Ready state")

    # Check last run times
    # Alert if no tasks ran in last 2 hours

    return issues

if __name__ == '__main__':
    issues = check_scheduled_tasks()
    if issues:
        print("ALERTS:", issues)
        sys.exit(1)
    print("All scheduled tasks healthy")
```

### Alert Integration

Add to `Company_Handbook.md`:

```markdown
## Scheduled Task Alerts

If scheduled tasks fail:
1. Check Task Scheduler / cron logs
2. Restart failed tasks
3. If persistent, alert human via WhatsApp
4. Log incident in /Logs/Issues/
```

## Error Handling

| Error | Recovery |
|-------|----------|
| Task won't start | Check user permissions, Python path |
| Task crashes mid-run | Check orchestrator.log, restart |
| Missed scheduled time | Manual trigger, check system sleep |
| Permission denied | Run as administrator / root |

## Troubleshooting

### Windows

| Issue | Solution |
|-------|----------|
| Task shows "Ready" but won't run | Check "Run whether user is logged on" |
| Python not found | Use full path to python.exe |
| Task runs but nothing happens | Check Working Directory setting |

### macOS / Linux

| Issue | Solution |
|-------|----------|
| cron job not running | Check `crontab -l`, verify syntax |
| Permission denied | chmod +x script, check user |
| Path issues | Use absolute paths in cron |

## Testing

```bash
# Test daily briefing manually
python orchestrator.py --daily-briefing

# Test weekly audit
python orchestrator.py --weekly-audit

# Verify output files created
ls -la Briefings/
```
