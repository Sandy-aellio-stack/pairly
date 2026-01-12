# TrueBond Rollback Plan

**Version:** 1.0.0
**Last Updated:** January 12, 2026
**Purpose:** Emergency rollback procedures for production issues

---

## Table of Contents

1. [Overview](#overview)
2. [When to Rollback](#when-to-rollback)
3. [Rollback Types](#rollback-types)
4. [Pre-Rollback Checklist](#pre-rollback-checklist)
5. [Rollback Procedures](#rollback-procedures)
6. [Post-Rollback Verification](#post-rollback-verification)
7. [Communication Plan](#communication-plan)
8. [Prevention](#prevention)

---

## Overview

This document provides step-by-step procedures for rolling back the TrueBond application to a previous stable version in case of critical issues in production.

### Rollback Objectives

- **Recovery Time Objective (RTO):** 15 minutes
- **Recovery Point Objective (RPO):** 5 minutes
- **Data Loss:** Minimize or eliminate
- **Downtime:** <5 minutes during rollback

---

## When to Rollback

### Immediate Rollback Triggers (Critical)

Roll back **IMMEDIATELY** without discussion if:

1. **Security Breach**
   - Data leak detected
   - Unauthorized access confirmed
   - Security vulnerability actively exploited

2. **Data Corruption**
   - Database corruption detected
   - Data integrity compromised
   - Irreversible data loss occurring

3. **Complete Service Outage**
   - Application completely down (>5 minutes)
   - All health checks failing
   - Unable to recover with restart

4. **Critical Feature Failure**
   - Authentication completely broken
   - Users unable to login
   - Payment system compromised (when enabled)

### Conditional Rollback Triggers (Consider Rollback)

Evaluate and decide within 30 minutes:

1. **High Error Rate**
   - Error rate >10%
   - Critical errors affecting >50% of users
   - Persistent errors not resolved by restart

2. **Performance Degradation**
   - Response times >5 seconds consistently
   - Database queries timing out
   - Memory leaks causing OOM

3. **Major Feature Broken**
   - Real-time messaging completely down
   - Critical workflow broken
   - Multiple users reporting same issue

4. **User Impact**
   - >100 support tickets in 1 hour
   - Social media backlash trending
   - Major negative press

### Do NOT Rollback For

- Minor UI issues
- Single user reports
- Non-critical feature bugs
- Performance issues <2x baseline
- Planned maintenance

---

## Rollback Types

### Type 1: Application Rollback (Fast)

**Duration:** 5-10 minutes
**Risk:** Low
**Data Loss:** None

Roll back Docker container to previous version.

### Type 2: Database Schema Rollback (Slow)

**Duration:** 15-30 minutes
**Risk:** Medium
**Data Loss:** Possible (requires careful planning)

Roll back database schema changes (rarely needed).

### Type 3: Full System Rollback (Comprehensive)

**Duration:** 30-60 minutes
**Risk:** High
**Data Loss:** Possible

Roll back entire system including database, Redis, and application.

### Type 4: Partial Feature Rollback (Surgical)

**Duration:** 5-15 minutes
**Risk:** Low
**Data Loss:** None

Disable specific features via feature flags.

---

## Pre-Rollback Checklist

### Before Starting Rollback

- [ ] **Identify Issue**
  - Document the problem
  - Confirm it's not transient
  - Verify rollback is necessary

- [ ] **Notify Team**
  - Alert all team members
  - Assign roles (Lead, Executor, Communicator, Observer)
  - Open war room channel

- [ ] **Capture State**
  - Take database snapshot
  - Export Redis state
  - Capture current metrics
  - Save error logs
  - Document symptoms

- [ ] **Confirm Previous Version**
  - Previous version identified
  - Previous version accessible
  - Previous version tested (if time permits)

- [ ] **Communication**
  - Status page updated (if available)
  - Users notified via appropriate channels
  - Support team briefed

---

## Rollback Procedures

### Procedure 1: Application Rollback (Type 1)

**Use when:** Application code causing issues, database schema unchanged

#### Step 1: Identify Previous Version

```bash
# SSH into production server
ssh truebond@production-server

# List Docker images
docker images | grep truebond-backend

# Identify previous version tag
# Example: truebond-backend:v1.0.0 (current)
#          truebond-backend:v0.9.5 (previous)
```

#### Step 2: Stop Current Containers

```bash
cd /home/truebond/truebond

# Stop containers gracefully
docker-compose -f docker-compose.production.yml down

# Verify stopped
docker ps | grep truebond
```

#### Step 3: Switch to Previous Version

```bash
# Update docker-compose.yml to use previous image
nano docker-compose.production.yml

# Change image tag:
# FROM: truebond-backend:v1.0.0
# TO: truebond-backend:v0.9.5
```

Or if using git tags:

```bash
# Checkout previous version
git fetch --tags
git checkout v0.9.5

# Rebuild image
docker build -f backend/Dockerfile.production -t truebond-backend:v0.9.5 backend/
```

#### Step 4: Start Previous Version

```bash
# Start containers
docker-compose -f docker-compose.production.yml up -d

# Watch logs
docker-compose -f docker-compose.production.yml logs -f backend
```

#### Step 5: Verify Rollback

```bash
# Health check
curl https://yourdomain.com/api/health

# Detailed health
curl https://yourdomain.com/api/health/detailed

# Test critical endpoint
curl https://yourdomain.com/api/auth/health
```

**Time:** 5-10 minutes

---

### Procedure 2: Database Schema Rollback (Type 2)

**Use when:** Database migrations caused issues

⚠️ **WARNING:** Database rollbacks are dangerous and may cause data loss!

#### Step 1: Assess Database Changes

```bash
# Connect to MongoDB
mongosh "your-production-connection-string"

# List collections
show collections

# Check for new collections or fields
db.collection_name.findOne()
```

#### Step 2: Application Rollback First

```bash
# Always rollback application BEFORE database
# Follow Procedure 1 first
```

#### Step 3: Database Rollback (if needed)

```bash
# Restore from backup (MongoDB Atlas)
# 1. Go to MongoDB Atlas Dashboard
# 2. Select Cluster
# 3. Go to Backups
# 4. Select restore point (before deployment)
# 5. Restore to same cluster (or test cluster first)

# OR manual rollback (if simple changes)
mongosh "your-connection-string"

# Example: Remove new field
db.users.updateMany({}, { $unset: { new_field: "" } })

# Example: Drop new collection
db.new_collection.drop()
```

**Time:** 15-30 minutes

---

### Procedure 3: Full System Rollback (Type 3)

**Use when:** Multiple components affected, coordinated rollback needed

#### Step 1: Stop All Services

```bash
# Stop application
docker-compose -f docker-compose.production.yml down

# Stop Redis (if self-hosted)
sudo systemctl stop redis-server
```

#### Step 2: Restore Database

```bash
# MongoDB Atlas: Restore from backup (see Procedure 2)
# Self-hosted: Restore from dump

mongorestore --uri="your-connection-string" /backup/previous-version/
```

#### Step 3: Restore Redis

```bash
# Copy backup RDB file
sudo cp /backup/redis-previous.rdb /var/lib/redis/dump.rdb

# Start Redis
sudo systemctl start redis-server

# Verify
redis-cli ping
```

#### Step 4: Rollback Application

```bash
# Follow Procedure 1 to rollback application
```

#### Step 5: Start All Services

```bash
# Start application
docker-compose -f docker-compose.production.yml up -d

# Verify all services
curl https://yourdomain.com/api/health/detailed
```

**Time:** 30-60 minutes

---

### Procedure 4: Feature Disable (Type 4)

**Use when:** Specific feature causing issues, can be disabled

#### Step 1: Identify Feature Flag

```bash
# Check environment variables
cat .env.production | grep FEATURE

# Example feature flags:
# REALTIME_MESSAGING_ENABLED=true
# PAYMENTS_ENABLED=false
```

#### Step 2: Disable Feature

```bash
# Edit environment file
nano .env.production

# Set feature flag to false
# Example: REALTIME_MESSAGING_ENABLED=false
```

#### Step 3: Restart Application

```bash
# Restart containers to pick up new environment
docker-compose -f docker-compose.production.yml restart backend

# Or reload without downtime (if supported)
docker exec truebond-backend kill -HUP 1
```

#### Step 4: Verify Feature Disabled

```bash
# Check feature status via API
curl https://yourdomain.com/api/features

# Test that feature is disabled
```

**Time:** 5-15 minutes

---

## Post-Rollback Verification

### Immediate Verification (T+0 to T+5)

- [ ] **Health Checks**
  - All health endpoints returning 200
  - All services showing healthy
  - No errors in logs

- [ ] **Critical Paths**
  - Signup working
  - Login working
  - Send message working
  - Search working

- [ ] **Performance**
  - Response times normal
  - Error rate <1%
  - Database responsive
  - Redis responsive

### Extended Verification (T+5 to T+30)

- [ ] **User Testing**
  - Manual user flow test
  - Mobile testing
  - WebSocket connections stable
  - Real-time features working

- [ ] **Monitoring**
  - Sentry error rate normal
  - Uptime monitor showing 100%
  - Metrics dashboard normal
  - No alerts firing

- [ ] **Database Integrity**
  - No data corruption
  - Relationships intact
  - Indexes present
  - Queries performing well

### Long-term Verification (T+30 to T+24h)

- [ ] **User Feedback**
  - No spike in support tickets
  - No user complaints
  - Social media sentiment normal

- [ ] **System Stability**
  - No memory leaks
  - No resource exhaustion
  - Consistent performance
  - Logs clean

---

## Communication Plan

### Internal Communication

**Rollback Initiated:**
```
🚨 ROLLBACK IN PROGRESS 🚨

Issue: [Brief description]
Severity: Critical/High/Medium
ETA: [Time estimate]
Lead: [Name]
Status: In Progress

Updates: [Channel/Thread]
```

**Rollback Complete:**
```
✅ ROLLBACK COMPLETE ✅

Duration: [Minutes]
Version: Rolled back to v[X.X.X]
Status: Services healthy
Next Steps: Root cause analysis

All clear to resume normal operations.
```

### External Communication

**Status Page (if available):**
```
🔴 Investigating Issue

We're investigating reports of [brief issue description].
Updates will be posted here.

Posted: [Time]
```

**Status Update:**
```
🟡 Identified Issue

We've identified the issue and are implementing a fix.
Expected resolution: [Time estimate]

Updated: [Time]
```

**Resolution:**
```
🟢 Resolved

The issue has been resolved. All systems are operational.
We apologize for any inconvenience.

Resolved: [Time]
```

### User Communication

**Email (if major incident):**
```
Subject: TrueBond Service Restored

Hi,

We experienced a technical issue today from [start time] to [end time]
that affected [description of impact].

The issue has been fully resolved and all services are now operating normally.

We sincerely apologize for any inconvenience this may have caused.

What happened:
[Brief explanation]

What we're doing:
[Prevention measures]

Thank you for your patience.

The TrueBond Team
```

---

## Root Cause Analysis

### Within 24 Hours

- [ ] **Incident Timeline**
  - Document exact timeline
  - Identify when issue started
  - Note when detected
  - Track response time
  - Record resolution time

- [ ] **Root Cause**
  - Identify primary cause
  - Identify contributing factors
  - Verify with evidence

- [ ] **Impact Assessment**
  - Users affected
  - Duration of impact
  - Data integrity status
  - Revenue impact (if any)

### Within 1 Week

- [ ] **Prevention Plan**
  - Preventive measures identified
  - Testing improvements planned
  - Monitoring improvements planned
  - Process improvements documented

- [ ] **Team Retrospective**
  - What went well
  - What went poorly
  - Action items
  - Documentation updates

---

## Prevention

### Pre-Deployment

1. **Staging Environment**
   - Always test in staging first
   - Staging mirrors production exactly
   - Test critical paths thoroughly

2. **Code Review**
   - All code reviewed by 2+ people
   - Security review for sensitive changes
   - Performance review for database changes

3. **Automated Testing**
   - Unit tests pass
   - Integration tests pass
   - Load tests pass
   - Security tests pass

4. **Gradual Rollout**
   - Deploy to 10% of users first
   - Monitor for 1 hour
   - Deploy to 50%
   - Monitor for 1 hour
   - Deploy to 100%

### During Deployment

1. **Monitoring**
   - Watch error rates continuously
   - Watch performance metrics
   - Watch user feedback channels

2. **Rollback Readiness**
   - Previous version ready
   - Team standing by
   - Rollback tested

### Post-Deployment

1. **Extended Monitoring**
   - Monitor for 24 hours
   - On-call rotation clear
   - Alerts configured

2. **User Feedback**
   - Monitor support channels
   - Monitor social media
   - Check analytics

---

## Rollback Decision Matrix

| Issue Severity | Error Rate | Uptime | Response Time | Decision |
|----------------|------------|--------|---------------|----------|
| Critical | >10% | <95% | >5s | **Immediate Rollback** |
| High | 5-10% | 95-99% | 2-5s | **Consider Rollback** |
| Medium | 1-5% | 99-99.9% | 1-2s | **Monitor** |
| Low | <1% | >99.9% | <1s | **Continue** |

---

## Roles & Responsibilities

### Rollback Lead
- Makes final rollback decision
- Coordinates team
- Communicates with stakeholders
- Signs off on completion

### Technical Executor
- Executes rollback commands
- Monitors technical metrics
- Reports status to lead

### Communication Lead
- Updates status page
- Communicates with users
- Briefs support team
- Handles external communication

### Observer
- Documents timeline
- Takes screenshots
- Captures logs
- Prepares RCA

---

## Emergency Contacts

```
Technical Lead: [Name] - [Phone] - [Email]
DevOps Lead: [Name] - [Phone] - [Email]
Product Owner: [Name] - [Phone] - [Email]
Support Lead: [Name] - [Phone] - [Email]

On-Call: [Current on-call engineer]
Escalation: [Escalation path]
```

---

## Rollback Log Template

```
Date: [Date]
Time Started: [Time]
Issue: [Brief description]
Severity: Critical/High/Medium/Low
Rollback Type: Type 1/2/3/4
Previous Version: v[X.X.X]
Current Version: v[X.X.X]

Timeline:
- [Time] Issue detected
- [Time] Team notified
- [Time] Rollback initiated
- [Time] Rollback completed
- [Time] Verification completed

Impact:
- Users affected: [Number or percentage]
- Duration: [Minutes]
- Data loss: Yes/No

Root Cause:
[Brief description]

Prevention:
[Action items]

Sign-off:
Lead: [Name] - [Time]
```

---

## Quick Reference Card

**Print this and keep near your workstation**

```
═══════════════════════════════════════════
       TRUEBOND EMERGENCY ROLLBACK
═══════════════════════════════════════════

1. IDENTIFY ISSUE
   - Is it critical? (See triggers above)
   - Notify team immediately

2. CAPTURE STATE
   - Document symptoms
   - Save logs to /backup/incident-[date]/
   - Take database snapshot

3. EXECUTE ROLLBACK
   ssh truebond@prod-server
   cd /home/truebond/truebond
   docker-compose down
   git checkout v[PREVIOUS]
   docker-compose up -d

4. VERIFY
   curl https://yourdomain.com/api/health
   Test critical paths

5. COMMUNICATE
   - Update status page
   - Notify users
   - Brief team

═══════════════════════════════════════════
Emergency: Call [On-Call Number]
═══════════════════════════════════════════
```

---

**End of Rollback Plan**

*Keep this document accessible during deployments and incidents.*
*Review and update after each rollback or major deployment.*
