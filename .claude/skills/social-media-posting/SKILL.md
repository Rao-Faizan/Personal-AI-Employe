---
name: social-media-posting
description: |
  Post to LinkedIn, Twitter (X), and other social platforms. Generate business content,
  schedule posts, and track engagement. All posts require human approval before publishing.
---

# Social Media Posting Skill

Automate social media posting for business lead generation with human oversight.

## Supported Platforms

| Platform | Post Type | Approval Required |
|----------|-----------|-------------------|
| LinkedIn | Text, Articles, Images | ✅ Always |
| Twitter/X | Tweets, Threads | ✅ Always |
| Facebook | Posts, Business updates | ✅ Always |
| Instagram | Captions (image via separate flow) | ✅ Always |

## Configuration

### LinkedIn Setup
1. Create LinkedIn App at https://www.linkedin.com/developers/apps
2. Get API credentials (Client ID, Client Secret)
3. Request `w_member_social` permission
4. Configure redirect URI

### Twitter/X Setup
1. Apply for Twitter API v2 access
2. Create app at https://developer.twitter.com/en/portal/dashboard
3. Get Bearer Token and API Keys
4. Enable OAuth 2.0

### MCP Server Installation
```bash
# LinkedIn MCP
npm install -g @linkedin/mcp-server

# Twitter MCP
npm install -g @twitter/mcp-server
```

### MCP Configuration
Add to `~/.qwen/mcp.json`:
```json
{
  "servers": [
    {
      "name": "linkedin",
      "command": "npx",
      "args": ["@linkedin/mcp-server@latest"],
      "env": {
        "LINKEDIN_CLIENT_ID": "your_client_id",
        "LINKEDIN_CLIENT_SECRET": "your_client_secret",
        "LINKEDIN_ACCESS_TOKEN": "your_access_token"
      }
    },
    {
      "name": "twitter",
      "command": "npx",
      "args": ["@twitter/mcp-server@latest"],
      "env": {
        "TWITTER_BEARER_TOKEN": "your_bearer_token",
        "TWITTER_API_KEY": "your_api_key",
        "TWITTER_API_SECRET": "your_api_secret"
      }
    }
  ]
}
```

## Content Generation Templates

### Business Update Post
```markdown
# Post Template: Business Update
---
platform: linkedin
type: text
topic: milestone
tone: professional
---

🎉 Exciting news! We've just [ACHIEVEMENT] at [COMPANY].

Key highlights:
• [STATISTIC 1]
• [STATISTIC 2]
• [IMPACT STATEMENT]

This wouldn't be possible without [THANK YOU].

#Industry #[HASHTAG1] #[HASHTAG2]
```

### Thought Leadership Post
```markdown
# Post Template: Thought Leadership
---
platform: linkedin
type: article_summary
topic: industry_insight
tone: authoritative
---

After working with [NUMBER] clients in [INDUSTRY], I've noticed a pattern:

[MOST COMMON PROBLEM]

Here's what works instead:

1️⃣ [SOLUTION STEP 1]
2️⃣ [SOLUTION STEP 2]
3️⃣ [SOLUTION STEP 3]

The result? [QUANTIFIED OUTCOME]

What's your experience been? Share below. 👇

#Leadership #[INDUSTRY] #Strategy
```

### Engagement Post
```markdown
# Post Template: Engagement
---
platform: twitter
type: thread
topic: quick_tips
tone: conversational
---

🧵 5 lessons from building [PROJECT]:

1/ [LESSON 1 - punchy one-liner]

2/ [LESSON 2 - with specific example]

3/ [LESSON 3 - counterintuitive insight]

4/ [LESSON 4 - actionable advice]

5/ [LESSON 5 - call to action]

Which resonates most? RT to share.
```

## Approval Workflow

### Step 1: Content Creation
Qwen generates post content and saves to `/Plans/SOCIAL_DRAFT_[DATE].md`:

```markdown
---
type: social_media_draft
platform: linkedin
created: 2026-01-07T10:30:00Z
scheduled_for: 2026-01-08T09:00:00Z
status: pending_approval
---

# LinkedIn Post Draft

## Content
🎉 Exciting milestone update...

## Hashtags
#AI #Automation #Business

## Image (optional)
/Vault/Social_Media/images/milestone_graphic.png

## To Approve
Move this file to /Approved/Social/ to schedule.

## To Reject
Move to /Rejected/ with reason.
```

### Step 2: Human Review
- Review content for accuracy and tone
- Check hashtags and mentions
- Verify any statistics or claims
- Move to `/Approved/Social/` or `/Rejected/`

### Step 3: Scheduling
Orchestrator picks up approved posts and schedules via MCP:

```bash
# Schedule LinkedIn post
python scripts/mcp-client.py call -u http://localhost:8081 -t linkedin_schedule \
  -p '{"text": "...", "scheduled_time": "2026-01-08T09:00:00Z", "image_url": "..."}'
```

### Step 4: Posting & Logging
After posting, log to `/Vault/Logs/social_media.json`:
```json
{
  "timestamp": "2026-01-08T09:00:00Z",
  "platform": "linkedin",
  "post_id": "urn:li:share:1234567890",
  "content_preview": "Exciting milestone update...",
  "approval_status": "approved",
  "approved_by": "human",
  "result": "posted",
  "engagement": {"likes": 0, "comments": 0, "shares": 0}
}
```

## Posting Schedule

| Platform | Frequency | Best Times |
|----------|-----------|------------|
| LinkedIn | 3-5x/week | Tue-Thu 8-10am |
| Twitter | 1-3x/day | Weekdays 12-3pm |
| Facebook | 3-7x/week | Weekdays 1-4pm |

## Content Calendar

Maintain `/Vault/Social_Media/Content_Calendar.md`:

```markdown
# Social Media Content Calendar - January 2026

| Date | Platform | Topic | Status |
|------|----------|-------|--------|
| Jan 8 | LinkedIn | Milestone update | Scheduled |
| Jan 9 | Twitter | Quick tips thread | Draft |
| Jan 10 | LinkedIn | Industry insight | Pending |
| Jan 12 | Twitter | Engagement question | Posted ✅ |
```

## Engagement Tracking

Weekly engagement summary in `/Vault/Social_Media/Weekly_Stats.md`:

```markdown
# Week 1 January 2026 - Social Stats

## LinkedIn
- Posts: 3
- Impressions: 2,450
- Engagement Rate: 4.2%
- New Connections: 15

## Twitter
- Tweets: 7
- Impressions: 1,890
- Engagement Rate: 2.8%
- New Followers: 8

## Top Performing Post
[Link to post with highest engagement]
```

## Error Handling

| Error | Recovery |
|-------|----------|
| API rate limit | Queue post, retry in 15 min |
| Invalid content | Alert human, quarantine draft |
| Auth expired | Pause posting, alert human |
| Image upload fail | Post text-only, log error |

## Compliance Rules

1. **Disclosure**: Add "AI-assisted" signature if required
2. **Fact-checking**: Verify all statistics before posting
3. **Brand voice**: Follow Company_Handbook.md tone guidelines
4. **Crisis protocol**: Pause all posting during sensitive events

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Post not scheduling | Check MCP server running |
| Image won't upload | Verify file path, check size < 5MB |
| Engagement not tracking | Refresh API tokens |
| Calendar not updating | Verify file permissions |
