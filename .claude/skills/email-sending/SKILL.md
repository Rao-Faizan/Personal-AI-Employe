---
name: email-sending
description: |
  Send emails via Gmail MCP server. Use for replying to clients, sending invoices,
  notifications, and business communications. Requires human approval for new contacts
  or bulk sends.
---

# Email Sending Skill

Send emails through Gmail MCP integration with human-in-the-loop approval.

## Configuration

### Prerequisites
1. Enable Gmail API in Google Cloud Console
2. Create OAuth 2.0 credentials
3. Install Gmail MCP server:
   ```bash
   npm install -g @anthropic/gmail-mcp
   ```

### MCP Server Setup
Add to `~/.qwen/mcp.json`:
```json
{
  "servers": [
    {
      "name": "gmail",
      "command": "npx",
      "args": ["@anthropic/gmail-mcp@latest"],
      "env": {
        "GMAIL_CLIENT_ID": "your_client_id",
        "GMAIL_CLIENT_SECRET": "your_client_secret",
        "GMAIL_REDIRECT_URI": "http://localhost:8080/callback"
      }
    }
  ]
}
```

## Usage Patterns

### Check for New Emails
```bash
# Search unread important emails
qwen "Check /Needs_Action for new EMAIL_ files and summarize unread messages"
```

### Send Email (Draft Mode - Default)
For new contacts or amounts > $100, create draft first:

```markdown
# /Vault/Pending_Approval/EMAIL_Draft_Client_A.md
---
type: email_draft
to: client_a@example.com
subject: Invoice #1234 - January 2026
body: |
  Dear Client A,

  Please find attached your invoice for January 2026.

  Amount: $1,500
  Due: 2026-02-01

  Best regards,
  AI Employee
attachment: /Vault/Invoices/2026-01_Client_A.pdf
priority: normal
requires_approval: true
status: pending
---

## To Approve
Move this file to /Approved folder to send.

## To Reject
Move this file to /Rejected folder.
```

### Send Email (Auto-Approved)
For known contacts and routine replies:

```bash
# Direct send via MCP call
python scripts/mcp-client.py call -u http://localhost:8080 -t gmail_send \
  -p '{"to": "known_contact@example.com", "subject": "Re: Meeting", "body": "Confirmed for 3pm"}'
```

## Approval Thresholds

| Action | Auto-Approve | Requires Approval |
|--------|-------------|-------------------|
| Reply to known contact | ✅ Yes | - |
| Reply to new contact | - | ⚠️ Always |
| Invoice < $500 | ✅ Yes | - |
| Invoice > $500 | - | ⚠️ Always |
| Bulk send (>10 emails) | - | ⚠️ Always |
| Attachment send | - | ⚠️ Always |

## Workflow: Invoice Email

1. **Watcher detects** WhatsApp/email requesting invoice
2. **Qwen creates** action file in `/Needs_Action`
3. **Qwen generates** invoice PDF in `/Vault/Invoices`
4. **Qwen creates** approval file in `/Pending_Approval`
5. **Human reviews** and moves to `/Approved`
6. **Orchestrator triggers** MCP send
7. **Qwen logs** action and moves files to `/Done`

## Error Handling

| Error | Recovery |
|-------|----------|
| OAuth token expired | Alert human, pause email operations |
| API rate limit | Wait 60s, retry with exponential backoff |
| Invalid recipient | Quarantine file, alert human |
| Attachment not found | Log error, create new action file |

## Logging Format

All sent emails logged to `/Vault/Logs/YYYY-MM-DD.json`:
```json
{
  "timestamp": "2026-01-07T10:30:00Z",
  "action_type": "email_send",
  "actor": "qwen_code",
  "target": "client@example.com",
  "subject": "Invoice #1234",
  "has_attachment": true,
  "approval_status": "approved",
  "approved_by": "human",
  "result": "success"
}
```

## Testing

```bash
# Test draft creation
python scripts/test-email-draft.py

# Test MCP connection
python scripts/mcp-client.py call -u http://localhost:8080 -t gmail_list -p '{"maxResults": 5}'
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| MCP won't connect | Check server running on port 8080 |
| Auth fails | Re-run OAuth flow, check credentials |
| Draft not created | Verify `/Pending_Approval` folder exists |
| Logs not writing | Check folder permissions |
