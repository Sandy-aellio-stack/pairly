# Content Moderation Operations Runbook

## Overview

This runbook provides operational procedures for Pairly content moderators and platform administrators.

## Moderation Workflow

### 1. Automated Pre-Upload Screening

**Text Content:**
- Middleware analyzes text before it reaches the route
- High-confidence explicit content (score ≥ 0.85) → **BLOCKED**
- Suspicious content (score 0.50-0.84) → **QUARANTINED**
- Safe content (score < 0.50) → **PUBLISHED**

**Image Content:**
- Images analyzed on upload
- Classification via Google Vision SafeSearch or local heuristics
- Same threshold logic as text

### 2. Quarantine Processing

**What Happens:**
1. Content enters Redis quarantine queue
2. Celery worker picks up quarantine job
3. Deeper analysis performed (multi-classifier voting)
4. Decision: PUBLISH or REMOVE
5. User notified if removed

**Quarantine Queue Monitoring:**
```bash
# Check quarantine queue length
redis-cli LLEN moderation:quarantine_queue

# View quarantined items (first 10)
redis-cli LRANGE moderation:quarantine_queue 0 9
```

### 3. User Reports

Users report content via `/api/report` endpoint.

**Report Flow:**
1. User submits report (content_id, content_type, reason, details)
2. Report logged in `reports` collection
3. Admin dashboard displays pending reports
4. Moderator reviews and takes action

**Reviewing Reports:**
```bash
# View pending reports
curl -X GET http://localhost:8001/api/admin/reports \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -G -d "status=pending&limit=20"
```

**Taking Action:**
```bash
# Remove content
curl -X POST http://localhost:8001/api/admin/reports/{report_id}/action \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "remove",
    "moderator_notes": "Violates policy: explicit content"
  }'

# Dismiss report (false positive)
curl -X POST http://localhost:8001/api/admin/reports/{report_id}/action \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "dismiss",
    "moderator_notes": "Content within policy guidelines"
  }'
```

## Moderation Decision Matrix

| Content Type | Score Range | Action | SLA |
|--------------|-------------|--------|-----|
| Text - Explicit Keywords | ≥ 0.85 | BLOCK | Immediate |
| Text - Suspicious | 0.50-0.84 | QUARANTINE | < 5 min |
| Text - Safe | < 0.50 | PUBLISH | Immediate |
| Image - Adult/Violence | ≥ 0.85 | BLOCK | Immediate |
| Image - Suspicious | 0.50-0.84 | QUARANTINE | < 10 min |
| Image - Safe | < 0.50 | PUBLISH | Immediate |
| User Report | N/A | REVIEW | < 24 hours |
| CSAM Suspected | Any | REMOVE + ESCALATE | < 1 hour |

## Policy Violation Severity Levels

### Level 1: Minor (Warning)
- Spam or off-topic content
- Mild profanity
- Borderline PG-13 content

**Action:** Content removal + warning

### Level 2: Moderate (Suspension)
- Repeated spam
- Harassment or bullying
- Suggestive but non-explicit content

**Action:** 7-day suspension + policy reminder

### Level 3: Severe (Permanent Ban)
- Nudity or sexual content
- Hate speech
- Threats of violence
- Illegal goods/services

**Action:** Permanent ban + content deletion

### Level 4: Critical (Law Enforcement)
- CSAM (Child Sexual Abuse Material)
- Human trafficking
- Credible threats of violence

**Action:**
1. Immediate account termination
2. Preserve evidence
3. NCMEC CyberTipline report (CSAM)
4. Law enforcement notification
5. Legal team involvement

## CSAM Response Protocol

⚠️ **If CSAM is suspected, follow these steps IMMEDIATELY:**

### Step 1: DO NOT VIEW THE CONTENT
- If you accidentally viewed it, stop immediately
- Document what you saw without describing graphic details

### Step 2: Preserve Evidence
```bash
# Isolate content (do not delete yet)
mongosh pairly --eval 'db.posts.updateOne(
  {id: "<POST_ID>"},
  {$set: {csam_flagged: true, csam_flagged_at: new Date()}}
)'

# Download media URLs to secure storage (legal hold)
# Contact DevOps lead for evidence preservation
```

### Step 3: File NCMEC Report
1. Go to: https://www.cybertipline.org
2. File report with:
   - User details (email, IP, registration date)
   - Content metadata (upload timestamp, file hash)
   - DO NOT include the actual image in the report
3. Save NCMEC report ID

### Step 4: Notify Stakeholders
- **Immediate:** Security lead
- **Within 1 hour:** Legal counsel
- **Within 24 hours:** CEO/COO

### Step 5: Terminate Account
```bash
# Permanently ban user
curl -X POST http://localhost:8001/api/admin/users/{user_id}/ban \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "CSAM violation",
    "permanent": true,
    "ncmec_report_id": "<NCMEC_ID>"
  }'
```

### Step 6: Do NOT Notify the User
- Federal law prohibits notifying users about CSAM investigations
- All communication handled by law enforcement

## Moderator Tools

### View User History
```bash
# Get user's all content
curl -X GET http://localhost:8001/api/admin/users/{user_id}/content \
  -H "Authorization: Bearer <ADMIN_TOKEN>"

# Get user's moderation history
curl -X GET http://localhost:8001/api/admin/users/{user_id}/moderation-history \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
```

### Bulk Content Removal
```bash
# Remove all content from a user
curl -X DELETE http://localhost:8001/api/admin/users/{user_id}/content \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Policy violation"}'
```

### Check Moderation Metrics
```bash
# Prometheus metrics
curl http://localhost:8001/metrics | grep moderation

# Sample output:
moderation_quarantined_total{type="text"} 45
moderation_removed_total{type="image"} 12
moderation_published_total 1823
moderation_quarantine_queue_length 3
```

## Alert Response

### ModerationQueueBacklog
**Symptom:** Quarantine queue > 100 items

**Investigation:**
```bash
# Check worker status
supervisorctl status moderation_worker

# Check worker logs
tail -f /var/log/supervisor/moderation_worker.*.log

# Check Redis connection
redis-cli PING
```

**Resolution:**
1. Scale up moderation workers
2. Check for stuck jobs (remove if needed)
3. Increase worker concurrency

### HighExplicitContentRate
**Symptom:** > 10% of content blocked/removed in 1 hour

**Investigation:**
- Check for spam attack or bot activity
- Review recent user signups
- Check IP clustering (multiple accounts from same IP)

**Resolution:**
1. Enable stricter rate limiting
2. Temporary account creation restrictions
3. Block offending IPs
4. Review classifier thresholds (may be too sensitive)

## Moderator Best Practices

### 1. Consistency
- Apply policy uniformly across all users
- Document decisions for precedent
- Avoid personal bias

### 2. Context Matters
- Consider cultural differences
- Review full conversation context
- Check user's intent (humor vs. harm)

### 3. Trauma-Informed Review
- Take breaks when reviewing disturbing content
- Use wellness resources (EAP, counseling)
- Report burnout to management

### 4. Privacy & Confidentiality
- Do not share user content externally
- Do not discuss cases outside work
- Follow GDPR/privacy protocols

### 5. Escalation
Escalate to senior moderator or legal if:
- Uncertain about policy application
- Content involves minors
- Legal implications (threats, illegal goods)
- High-profile user/celebrity

## Regular Maintenance

### Daily
- [ ] Review pending reports (target: < 24 hour turnaround)
- [ ] Check quarantine queue length
- [ ] Monitor moderation metrics dashboard

### Weekly
- [ ] Review policy violation trends
- [ ] Update keyword blocklist if needed
- [ ] Team sync on edge cases and precedents

### Monthly
- [ ] Classifier accuracy audit
- [ ] Policy update review
- [ ] Moderator training refresher

## Contact Information

**Moderation Team Lead:** moderation-lead@pairly.app

**Legal/Compliance:** legal@pairly.app

**Security Incidents:** security@pairly.app

**CSAM Hotline:** csam-emergency@pairly.app (24/7)

**Wellness/EAP:** wellness@pairly.app

---

**Remember:** Your role is critical to maintaining a safe platform. When in doubt, escalate. Your mental health matters - take breaks and use wellness resources.