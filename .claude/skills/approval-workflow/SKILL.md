---
name: approval-workflow
description: |
  Human-in-the-loop (HITL) approval system for sensitive actions. Manages approval
  requests, tracks approvals/rejections, and triggers actions after human consent.
---

# Human-in-the-Loop Approval Workflow

File-based approval system for sensitive AI actions requiring human oversight.

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────┐
│   Qwen      │────▶│ Pending_Approval │────▶│   Human      │
│   Creates   │     │     Folder       │     │   Reviews    │
└─────────────┘     └──────────────────┘     └──────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ Human Moves   │
                    │ to Approved/  │
                    │ or Rejected/  │
                    └───────────────┘
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
     ┌────────────────┐         ┌────────────────┐
     │  Orchestrator  │         │  Qwen Logs     │
     │  Executes      │         │  & Moves Done  │
     └────────────────┘         └────────────────┘
```

## Approval Categories

| Category | Auto-Approve | Requires Approval | Never Auto |
|----------|-------------|-------------------|------------|
| **Email** | Known contacts | New contacts | Bulk (>10) |
| **Payments** | < $50 recurring | $50-$500 | > $500, new payee |
| **Social Media** | - | All posts | - |
| **File Operations** | Create, read | - | Delete, external |
| **Calendar** | Meetings < 1hr | External meetings | Company-wide |
| **Data Access** | Internal data | - | Personal/financial |

## File Structure

### Approval Request Template

```markdown
---
type: approval_request
action: email_send
created: 2026-01-07T10:30:00Z
expires: 2026-01-08T10:30:00Z
priority: medium
category: communication
status: pending
---

# Approval Request: Send Email to Client A

## Action Details
- **To:** client_a@example.com
- **Subject:** Invoice #1234 - January 2026
- **Amount:** $1,500
- **Attachment:** /Vault/Invoices/2026-01_Client_A.pdf

## Context
Client requested invoice via WhatsApp on 2026-01-07.
Invoice generated per agreed rate ($1,500/month retainer).

## Risk Assessment
- ✅ Known contact (6 month history)
- ✅ Expected action (invoice request)
- ✅ Amount matches contract
- ⚠️ Attachment included

## To Approve
Move this file to: `/Approved/`

## To Reject
Move this file to: `/Rejected/` and add reason.

## To Request Changes
Edit this file, add comments, move back to `/Needs_Action/`
```

### Payment Approval Template

```markdown
---
type: approval_request
action: payment
created: 2026-01-07T10:30:00Z
expires: 2026-01-07T18:00:00Z  # Same day for payments
priority: high
category: financial
amount: 750.00
currency: USD
status: pending
---

# Approval Request: Payment to Vendor

## Payment Details
- **Payee:** Cloud Services Inc.
- **Amount:** $750.00 USD
- **Account:** ****1234 (Business Checking)
- **Reference:** Monthly server costs - January 2026
- **Due Date:** 2026-01-10

## Verification
- ✅ Recurring vendor (12 month history)
- ✅ Amount matches previous months
- ✅ Invoice received and verified
- ✅ Within monthly budget

## To Approve
Move to: `/Approved/Payments/`

## To Reject
Move to: `/Rejected/Payments/` with reason.
```

## Folder Structure

```
Vault/
├── Pending_Approval/          # Active approval requests
│   ├── EMAIL_Client_A_2026-01-07.md
│   └── PAYMENT_Vendor_X_2026-01-07.md
├── Approved/                   # Approved actions awaiting execution
│   ├── Communications/
│   │   └── EMAIL_...md
│   ├── Payments/
│   │   └── PAYMENT_...md
│   └── Social/
│       └── SOCIAL_...md
├── Rejected/                   # Rejected actions with reasons
│   └── [category]/
└── Logs/
    └── Approvals_YYYY-MM-DD.json
```

## Orchestrator Integration

### Watch Loop
```python
# In orchestrator.py
def check_pending_approvals(self):
    """Check for approved files and execute actions."""
    approved_folder = self.vault_path / 'Approved'

    for category in ['Communications', 'Payments', 'Social']:
        category_folder = approved_folder / category
        if not category_folder.exists():
            continue

        for file_path in category_folder.glob('*.md'):
            self.execute_approved_action(file_path, category)
```

### Execution Handler
```python
def execute_approved_action(self, file_path: Path, category: str):
    """Execute an approved action based on category."""
    content = file_path.read_text()
    metadata = self.parse_frontmatter(content)

    if category == 'Communications':
        result = self.send_email(metadata)
    elif category == 'Payments':
        result = self.process_payment(metadata)
    elif category == 'Social':
        result = self.schedule_post(metadata)

    # Log the action
    self.log_action(metadata, result)

    # Move to Done
    self.move_to_done(file_path)
```

## Logging Format

All approval actions logged to `/Vault/Logs/Approvals_YYYY-MM-DD.json`:

```json
{
  "timestamp": "2026-01-07T10:45:00Z",
  "request_id": "EMAIL_Client_A_2026-01-07",
  "action_type": "email_send",
  "created": "2026-01-07T10:30:00Z",
  "approved_at": "2026-01-07T10:44:00Z",
  "approved_by": "human",
  "approval_method": "file_move",
  "execution_time": "2026-01-07T10:45:00Z",
  "result": "success",
  "details": {
    "recipient": "client_a@example.com",
    "subject": "Invoice #1234"
  }
}
```

## Expiration Handling

Approval requests expire after 24 hours (or custom time):

```python
def check_expired_approvals(self):
    """Move expired approvals to Rejected with note."""
    pending_folder = self.vault_path / 'Pending_Approval'
    now = datetime.now()

    for file_path in pending_folder.glob('*.md'):
        content = file_path.read_text()
        metadata = self.parse_frontmatter(content)

        expires = datetime.fromisoformat(metadata.get('expires'))
        if expires < now:
            # Add expiration note
            self.add_expiration_note(file_path)
            # Move to Rejected
            rejected_path = self.vault_path / 'Rejected' / 'Expired' / file_path.name
            file_path.rename(rejected_path)
```

## Priority Levels

| Priority | Response Time | Escalation |
|----------|---------------|------------|
| **High** | 1 hour | SMS/WhatsApp alert |
| **Medium** | 4 hours | Email notification |
| **Low** | 24 hours | Dashboard update |

## Dashboard Integration

Show pending approvals in `Dashboard.md`:

```markdown
## Pending Approvals

| Request | Type | Created | Priority | Time Remaining |
|---------|------|---------|----------|----------------|
| EMAIL_Client_A | Communication | 10:30am | Medium | 23h 45m |
| PAYMENT_Vendor_X | Financial | 9:15am | High | 7h 15m |

**Action Required:** 2 approvals pending
```

## Security Rules

1. **No auto-approval for new payees** - Always require human verification
2. **Payment limits enforced** - Hard cap at $500 without explicit approval
3. **Audit trail mandatory** - All approvals logged with timestamps
4. **Expiration enforced** - Stale requests auto-rejected
5. **No credential exposure** - Sensitive data never in approval files

## Error Recovery

| Scenario | Recovery |
|----------|----------|
| File moved accidentally | Check Logs, restore from backup |
| Wrong action executed | Immediate human alert, reversal procedure |
| Approval timeout | Escalate to human, quarantine request |
| Duplicate approval | Detect by ID, reject duplicate |

## Testing

```bash
# Test approval workflow
python scripts/test-approval-workflow.py

# Expected flow:
# 1. Creates test approval in Pending_Approval/
# 2. Simulates human move to Approved/
# 3. Verifies orchestrator executes
# 4. Checks log entry created
# 5. Confirms file moved to Done/
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Approval not executing | Check Approved/ folder structure |
| Logs not writing | Verify folder permissions |
| Expiration not working | Check system timezone settings |
| Duplicate executions | Verify file move is atomic |
