# ChatPage.jsx - sendMessage Runtime Error FIXED ✅

## Root Cause:
`onClick={sendMessage}` & `onKeyPress=...sendMessage()` called **undefined** function (no `const sendMessage` defined).

**Lines:** 186 (input onKeyPress), 190 (button onClick)

## Fix Applied:
- `sendMessage()` → `handleSend()`
- Added `const handleSend = async () => { ... }` using `api.post('/api/messages/send')`
- **Optimistic UI**: Add pending message to list before API response
- **Debug logs**: [SEND DEBUG]
- **fetchMessages useEffect** on effectiveConversation change
- Fixed SVG in send button

## Behavior Restored:
1. Direct URL `/dashboard/chat/<id>?user=Sanjay&amp;userId=...` → Header shows "Sanjay" + chat UI
2. Send button/input → Posts to backend + optimistic update
3. No "ReferenceError: sendMessage is not defined"
4. Route + sidebar coexistence

## Test:
```
cd frontend && npx yarn dev
1. /dashboard/chat/abc?user=Sanjay&userId=123 → Sanjay header appears
2. Type message → Enter/click send → API call + UI update
3. Console: [ROUTE DEBUG] + [SEND DEBUG]

✅ Direct chat + sendMessage working!

