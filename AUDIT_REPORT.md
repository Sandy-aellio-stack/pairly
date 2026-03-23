# Pairly Chat System Audit Report

**Date:** Current State Analysis
**Status:** Debug Instrumentation Complete | Test Verification Pending

## Current State (Post-Debug Patches)

### ✅ Working
```
- Route parsing: /dashboard/chat/{conversationId}?user=Sanjay ✓
- Direct chat header/fallback UI renders ✓  
- Audio/video call buttons present ✓
- Frontend error handling (toast fallback) ✓
```

### ❌ Broken  
```
- Conversations sidebar: "No conversations yet" (timeout)
- Text send: "Failed to send message" (TBMessage validation)
- Emoji picker state unconfirmed
```

## Root Cause Analysis

### 1. Conversations Fetch Timeout (Primary Blocker)
**Path:** `ChatPage.jsx` → `messagesAPI.getConversations()` → `/api/messages/conversations`

**Symptoms:**
- Toast: "Failed to load conversations (tap to retry)"
- Network request times out @10s
- Sidebar empty despite LIMIT 50 isolation

**Debug Live:**
```
Frontend: [FETCH DEBUG] token/URL/timings/error details
Backend: [CONV ROUTE ENTRY/AUTH/SERVICE/TOTAL] timings
Service: [CONV DEBUG QUERY_CONV/USERS/RESULT]
```

**Likely Causes (Ranked):**
1. **Proxy/Network**: No [CONV ROUTE ENTRY] log
2. **DB Query**: TBConversation.find($in participants) slow (no index)
3. **User Batch**: TBUser.find($in many_ids) slow/large result
4. **Serialization**: Large JSON response

### 2. Message Send Validation (TBMessage)
**Path:** ChatPage `handleSend()` → socket.emit('message:send') → socket_server.py `message_send`

**Symptoms:**
- "Failed to send message"
- Backend traceback: `conversation_id Field required [type=missing]`

**Model:** `TBMessage.conversation_id: Indexed(PydanticObjectId)` REQUIRED

**Debug Live:**
```
Socket: [SOCKET DEBUG] payload → ObjectId conversion → constructor params → insert error
Service: [SERVICE DEBUG] constructor params (HTTP fallback)
```

**Likely Causes:**
1. **ObjectId Type**: Frontend sends str, PydanticObjectId(sender_id) fails
2. **Missing Payload**: conversation_id not reaching backend
3. **Validation Timing**: Field missing before constructor

### 3. Emoji Picker (Lower Priority)
**Path:** ChatPage click handlers + useEffect outside-click

**Debug Live:** [EMOJI DEBUG] already present

## Verification Plan (Execute Now)

**Step-by-Step Test:**
```
1. Backend: uvicorn backend.main:app --reload
2. Frontend: Ctrl+Shift+R → /dashboard/chat/69a43e309840310b0b8bb969?user=Sanjay
3. Wait 15s (conversations timeout)
4. Send "test" message
5. Open emoji picker
```

**Required Raw Logs:**
```
A) Browser Console:
[FETCH DEBUG]*
[AXIOS DEBUG]*
[CHAT DEBUG]*
[SOCKET DEBUG]*
[EMOJI DEBUG]*

B) Backend Terminal:
[CONV ROUTE*]*
[CONV DEBUG*] 
[SERVICE DEBUG]*
[SOCKET DEBUG]*
Traceback*

C) Network Tab → /api/messages/conversations:
Status | Time | Size | Full URL | Response Preview
```

## Permanent Fixes (Post-Logs)

### Conversations:
```
1. Mongo Index: db.tb_conversations.createIndex({"participants":1, "last_message_at":-1})
2. Pagination: conversations?page=1&limit=20
3. User Projection: TBUser.find(..., projection={"name":1, "profile_picture":1})
```

### Message Send:
```
1. ObjectId Validation: conversation_id = PydanticObjectId(ensure_valid(data.conversation_id))
2. Frontend Normalize: conversation_id = otherChat.conversation_id || route.conversationId
3. Fallback: if !conversation_id → create_or_get_conversation first
```

### Emoji:
```
useEffect cleanup + refs verified
```

## Success Criteria
```
✓ Send "test" → message appears
✓ Sidebar loads conversations  
✓ Page refresh keeps state
✓ Emoji picker opens/closes correctly
✓ No backend validation/timeout errors
```

**Next Action:** Run test + paste raw logs → Phase 4 permanent fixes.

**Priority:** Conversations timeout → Message validation → Emoji polish

