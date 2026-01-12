# 🔴 TrueBond Missing APIs - Quick Reference

**Date:** January 12, 2026
**Priority:** Production Blockers

---

## 🚨 CRITICAL APIS (Must Have for Launch)

### Password Reset & Recovery
```
POST   /api/auth/password/forgot          # Request password reset email
POST   /api/auth/password/reset           # Reset password with token
POST   /api/auth/verify-email             # Email verification
```

**Why Critical:** Users get locked out, no recovery method

---

### Real-Time Calling
```
POST   /api/calls/initiate                # Start audio/video call
POST   /api/calls/accept                  # Accept incoming call
POST   /api/calls/reject                  # Reject call
POST   /api/calls/end                     # End active call
GET    /api/calls/active                  # Get active call status
GET    /api/calls/history                 # Call history
POST   /api/calls/rate                    # Rate call quality
WS     /api/calls/signaling               # WebRTC signaling channel
```

**Why Critical:** Core feature advertised in UI, UI exists but no backend

---

### Payment Webhooks (Production)
```
POST   /api/webhooks/stripe               # Handle Stripe events
POST   /api/webhooks/razorpay             # Handle Razorpay events
GET    /api/webhooks/logs                 # View webhook delivery logs
POST   /api/webhooks/retry/{id}           # Manually retry failed webhook
```

**Why Critical:** Payment confirmation won't work in production

---

### Media Upload (Cloud)
```
POST   /api/media/upload                  # Upload to S3/Cloud Storage
DELETE /api/media/{id}                    # Delete media
GET    /api/media/{id}/url                # Get signed URL
POST   /api/media/{id}/moderate           # Flag inappropriate media
```

**Why Critical:** Currently local storage only, not scalable

---

### Push Notifications
```
POST   /api/notifications/register-device # Register FCM/APNS token
DELETE /api/notifications/device/{id}     # Unregister device
PUT    /api/notifications/preferences     # Update notification settings
GET    /api/notifications/preferences     # Get current settings
```

**Why Critical:** Users won't know about messages/matches

---

## ⚠️ HIGH PRIORITY APIS (Needed Soon)

### Two-Factor Authentication
```
POST   /api/auth/2fa/enable               # Enable 2FA
POST   /api/auth/2fa/verify               # Verify 2FA code
POST   /api/auth/2fa/disable              # Disable 2FA
POST   /api/auth/2fa/backup-codes         # Generate backup codes
```

**Why High Priority:** Security and trust

---

### Session Management
```
GET    /api/auth/sessions                 # List active sessions
DELETE /api/auth/sessions/{id}            # Revoke specific session
DELETE /api/auth/sessions/all             # Revoke all sessions
GET    /api/auth/login-history            # View login history
```

**Why High Priority:** User security and control

---

### User Blocking & Reporting
```
POST   /api/users/{id}/block              # Block user
DELETE /api/users/{id}/block              # Unblock user
GET    /api/users/blocked                 # List blocked users
POST   /api/reports/create                # Report user/content
GET    /api/reports/my-reports            # My submitted reports
```

**Why High Priority:** Safety and moderation

---

### Advanced Matchmaking
```
GET    /api/matches/daily                 # Daily recommendations
POST   /api/matches/{id}/like             # Like a match
POST   /api/matches/{id}/pass             # Pass on match
GET    /api/matches/mutual                # Mutual likes
POST   /api/matches/{id}/feedback         # Provide feedback
GET    /api/matches/compatibility/{id}    # Get compatibility score
```

**Why High Priority:** Core value proposition

---

## 📊 MEDIUM PRIORITY APIS (Nice to Have)

### Social Feed
```
POST   /api/posts                         # Create post
GET    /api/posts/feed                    # Get personalized feed
POST   /api/posts/{id}/like               # Like post
DELETE /api/posts/{id}/like               # Unlike post
POST   /api/posts/{id}/comment            # Add comment
GET    /api/posts/{id}/comments           # Get comments
POST   /api/posts/{id}/report             # Report post
DELETE /api/posts/{id}                    # Delete post
```

**Why Medium Priority:** Engagement feature, not core

---

### Subscription System
```
GET    /api/subscriptions/plans           # List available plans
POST   /api/subscriptions/subscribe       # Subscribe to plan
PUT    /api/subscriptions/upgrade         # Upgrade plan
POST   /api/subscriptions/cancel          # Cancel subscription
GET    /api/subscriptions/status          # Check current status
POST   /api/subscriptions/portal          # Billing portal link
```

**Why Medium Priority:** Revenue feature, not launch blocker

---

### Advanced Analytics
```
GET    /api/analytics/user/engagement     # User engagement metrics
GET    /api/analytics/user/retention      # Retention analysis
GET    /api/analytics/revenue/mrr         # Monthly recurring revenue
GET    /api/analytics/funnel              # Conversion funnel
POST   /api/analytics/event               # Track custom event
GET    /api/analytics/cohorts             # Cohort analysis
```

**Why Medium Priority:** Growth optimization, not critical at launch

---

### Profile Enhancements
```
POST   /api/profile/verification/request  # Request photo verification
POST   /api/profile/verification/submit   # Submit verification
GET    /api/profile/views                 # Who viewed my profile
GET    /api/profile/visitors              # Profile visitors
POST   /api/profile/boost                 # Boost profile visibility
GET    /api/profile/insights              # Profile performance
```

**Why Medium Priority:** Premium features for later

---

## 🔧 INFRASTRUCTURE APIS (Supporting)

### Health & Monitoring
```
GET    /api/health/detailed               # Detailed health check
GET    /api/health/db                     # Database health
GET    /api/health/redis                  # Redis health
GET    /api/health/storage                # Storage health
GET    /api/health/services               # All services status
```

**Why Important:** Operations and monitoring

---

### Admin Advanced
```
GET    /api/admin/users/export            # Export user data
POST   /api/admin/users/bulk-action       # Bulk user operations
GET    /api/admin/revenue/reconcile       # Reconcile payments
POST   /api/admin/cache/clear             # Clear cache
GET    /api/admin/jobs/status             # Background jobs status
POST   /api/admin/maintenance/enable      # Enable maintenance mode
```

**Why Important:** Admin operations

---

## 📝 API IMPLEMENTATION PRIORITY

### Week 1 (Critical)
1. Password reset flow (6h)
2. Payment webhooks (8h)
3. Media upload to cloud (6h)

### Week 2 (Critical)
1. Calling initiate/accept/end (12h)
2. WebRTC signaling (8h)
3. FCM notification registration (4h)

### Week 3 (High Priority)
1. 2FA enable/verify (6h)
2. Session management (4h)
3. Block/unblock users (4h)
4. Report system (6h)

### Week 4 (High Priority)
1. Advanced matchmaking (8h)
2. Match feedback (4h)
3. Compatibility scoring (6h)

### Week 5-6 (Medium Priority)
1. Social feed (16h)
2. Subscription system (12h)
3. Advanced analytics (8h)

---

## 🎯 QUICK WIN APIS (Easy to Implement)

These can be done quickly for immediate value:

```
# User Experience
GET    /api/profile/views                 # 2h - Query existing data
GET    /api/auth/login-history            # 2h - Query sessions
GET    /api/users/blocked                 # 1h - Simple list

# Admin Tools
GET    /api/admin/users/export            # 3h - CSV export
GET    /api/admin/cache/clear             # 1h - Redis clear
POST   /api/admin/users/bulk-action       # 4h - Bulk ops

# Analytics
POST   /api/analytics/event               # 2h - Event tracking
GET    /api/analytics/funnel              # 4h - Query analytics
```

**Total Quick Wins:** ~19 hours, adds significant value

---

## 📋 API TESTING CHECKLIST

For each new API, ensure:
- [ ] Authentication required
- [ ] Input validation (Pydantic)
- [ ] Error handling (try/catch)
- [ ] Rate limiting applied
- [ ] Audit logging (for sensitive ops)
- [ ] API documentation (docstring)
- [ ] Unit tests written
- [ ] Integration test
- [ ] Manual testing in Postman
- [ ] Frontend integration tested

---

## 🔗 DEPENDENCIES

### APIs Blocked by Infrastructure:

**Waiting on Redis:**
- Session management APIs
- Real-time presence
- Distributed rate limiting

**Waiting on Celery:**
- Background job APIs
- Async notifications
- Scheduled tasks

**Waiting on S3/Cloud Storage:**
- Media upload (production)
- File attachment APIs
- Image processing

**Waiting on WebRTC Servers:**
- Call signaling
- Call quality monitoring
- Media relay

**Waiting on Email Service:**
- Password reset
- Email verification
- Notification emails

**Waiting on SMS Service:**
- OTP via SMS
- 2FA via SMS
- Security alerts

---

## 💡 RECOMMENDATIONS

### Start With
1. **Password Reset** - Most requested by users
2. **Payment Webhooks** - Unblock real payments
3. **Block/Report** - Essential for safety

### Then Add
1. **Calling APIs** - Core feature promise
2. **Push Notifications** - User engagement
3. **2FA** - Security and trust

### Finally
1. **Social Features** - Engagement boost
2. **Subscriptions** - Additional revenue
3. **Advanced Analytics** - Growth insights

---

## 📊 EFFORT ESTIMATION

| Priority | APIs | Estimated Time |
|----------|------|----------------|
| Critical | 25 APIs | 60 hours (1.5 weeks) |
| High | 20 APIs | 48 hours (1 week) |
| Medium | 30 APIs | 72 hours (2 weeks) |
| **TOTAL** | **75 APIs** | **180 hours (4.5 weeks)** |

**Note:** Assumes infrastructure is ready. Add 1-2 weeks for infrastructure setup.

---

## ✅ COMPLETED APIS (For Reference)

Already implemented and working:
- Authentication (login, signup, logout, refresh, me)
- Credits (balance, pricing, purchase, history, deduct)
- Payments (intent create/cancel/history, packages)
- Messaging V2 (send, read, delivered, conversations, stats)
- User profiles (view, update, upload photo, nearby)
- Admin (dashboard, users, analytics, moderation, settings)
- Location (update, nearby users)
- Notifications (list, read, read-all)
- Search (users by filters)

**Total Working APIs:** ~40 endpoints

**Total Needed APIs:** ~75 additional endpoints

**Total System APIs (when complete):** ~115 endpoints

---

*Generated: January 12, 2026*
*Use this as a development checklist*
