# Frontend Error Handling Guide

**Last Updated:** January 12, 2026
**Backend Version:** TrueBond v1.0.0

---

## Overview

This document describes how the TrueBond backend handles errors and how the frontend should respond to them. Following this guide ensures a consistent user experience and proper error recovery.

---

## Backend Error Response Format

All errors from the backend follow a consistent JSON structure:

```json
{
  "error": "Error message here",
  "status_code": 400,
  "path": "/api/endpoint",
  "details": []  // Optional, for validation errors
}
```

---

## HTTP Status Codes

### Authentication Errors (401)

**Status:** `401 Unauthorized`

**Common Causes:**
- Token expired
- Token invalid
- Token revoked (after logout)
- User logged out on another device

**Frontend Response:**
1. Clear local authentication state (tokens, user data)
2. Redirect to login page
3. Show message: "Your session has expired. Please log in again."
4. Store current page URL to redirect back after login

**Example:**
```javascript
if (response.status === 401) {
  // Clear auth state
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');

  // Store return URL
  const returnUrl = window.location.pathname;
  localStorage.setItem('returnUrl', returnUrl);

  // Redirect to login
  window.location.href = '/login?session_expired=true';
}
```

---

### Authorization Errors (403)

**Status:** `403 Forbidden`

**Common Causes:**
- User account deactivated
- Insufficient permissions
- Trying to access admin routes as regular user

**Frontend Response:**
1. Show error message to user
2. If account deactivated: log out and redirect to login
3. If permission denied: show "Access denied" message
4. Do NOT redirect to login (user IS authenticated)

**Example:**
```javascript
if (response.status === 403) {
  const error = await response.json();

  if (error.error.includes('deactivated')) {
    // Account deactivated - force logout
    logout();
    showError('Your account has been deactivated. Please contact support.');
  } else {
    // Permission denied
    showError('You do not have permission to access this resource.');
  }
}
```

---

### Payment Required (402)

**Status:** `402 Payment Required`

**Common Causes:**
- Insufficient credits to send message
- Insufficient credits to start call
- Need to purchase credits

**Frontend Response:**
1. Show friendly message about needing credits
2. Offer "Buy Credits" button/link
3. Do NOT show as generic error

**Example:**
```javascript
if (response.status === 402) {
  showModal({
    title: 'Insufficient Credits',
    message: 'You need more credits to send messages.',
    primaryAction: {
      text: 'Buy Credits',
      onClick: () => navigate('/credits')
    },
    secondaryAction: {
      text: 'Cancel',
      onClick: closeModal
    }
  });
}
```

---

### Validation Errors (422)

**Status:** `422 Unprocessable Entity`

**Response Format:**
```json
{
  "error": "Validation error",
  "status_code": 422,
  "details": [
    {
      "field": "body -> email",
      "message": "value is not a valid email address",
      "type": "value_error.email"
    },
    {
      "field": "body -> age",
      "message": "ensure this value is greater than or equal to 18",
      "type": "value_error.number.not_ge"
    }
  ],
  "path": "/api/auth/signup"
}
```

**Frontend Response:**
1. Parse `details` array
2. Show field-specific error messages
3. Highlight invalid form fields in red
4. Focus on first invalid field

**Example:**
```javascript
if (response.status === 422) {
  const error = await response.json();

  // Map errors to form fields
  error.details.forEach(({ field, message }) => {
    const fieldName = field.split(' -> ').pop(); // Extract field name
    setFieldError(fieldName, message);
    highlightField(fieldName, 'error');
  });

  // Focus first invalid field
  if (error.details.length > 0) {
    const firstField = error.details[0].field.split(' -> ').pop();
    document.querySelector(`[name="${firstField}"]`)?.focus();
  }
}
```

---

### Rate Limiting (429)

**Status:** `429 Too Many Requests`

**Response Format:**
```json
{
  "detail": "Too many requests",
  "retry_after": 30
}
```

**Response Headers:**
```
Retry-After: 30
```

**Frontend Response:**
1. Show user-friendly message
2. Disable form/button for `retry_after` seconds
3. Show countdown timer
4. Re-enable after timeout

**Example:**
```javascript
if (response.status === 429) {
  const error = await response.json();
  const retryAfter = error.retry_after || 60;

  // Disable form
  setFormDisabled(true);
  setRetryCountdown(retryAfter);

  // Show message
  showError(`Too many requests. Please wait ${retryAfter} seconds.`);

  // Start countdown
  const interval = setInterval(() => {
    setRetryCountdown(prev => {
      if (prev <= 1) {
        clearInterval(interval);
        setFormDisabled(false);
        return 0;
      }
      return prev - 1;
    });
  }, 1000);
}
```

---

### Server Errors (500)

**Status:** `500 Internal Server Error`

**Response Format (Development):**
```json
{
  "error": "Internal server error",
  "status_code": 500,
  "detail": "Detailed error message",
  "type": "ValueError",
  "path": "/api/endpoint"
}
```

**Response Format (Production):**
```json
{
  "error": "An unexpected error occurred",
  "status_code": 500,
  "path": "/api/endpoint"
}
```

**Frontend Response:**
1. Show generic error message (don't expose technical details)
2. Offer "Try Again" button
3. Log error details to console for debugging
4. Consider showing "Report Problem" link

**Example:**
```javascript
if (response.status === 500) {
  const error = await response.json();

  console.error('Server error:', error);

  showError({
    title: 'Something went wrong',
    message: 'An unexpected error occurred. Please try again.',
    actions: [
      {
        text: 'Try Again',
        onClick: retryRequest
      },
      {
        text: 'Report Problem',
        onClick: () => navigate('/support')
      }
    ]
  });
}
```

---

## Token Refresh Flow

### When Access Token Expires

**Scenario:** User makes a request but access token has expired

**Backend Response:** `401 Unauthorized` with `{"error": "Token expired"}`

**Frontend Flow:**

1. **Intercept 401 error**
2. **Check if refresh token exists**
3. **Call `/api/auth/refresh` with refresh token**
4. **If refresh succeeds:**
   - Save new tokens
   - Retry original request with new access token
5. **If refresh fails:**
   - Clear all tokens
   - Redirect to login

**Example (Axios Interceptor):**
```javascript
axios.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config;

    // Check if 401 and not already retried
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const refreshToken = localStorage.getItem('refresh_token');

      if (refreshToken) {
        try {
          // Try to refresh token
          const response = await axios.post('/api/auth/refresh', {
            refresh_token: refreshToken
          });

          const { access_token, refresh_token } = response.data;

          // Save new tokens
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', refresh_token);

          // Retry original request
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return axios(originalRequest);
        } catch (refreshError) {
          // Refresh failed - logout
          logout();
          window.location.href = '/login?session_expired=true';
          return Promise.reject(refreshError);
        }
      } else {
        // No refresh token - logout
        logout();
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);
```

---

## Network Errors

### No Internet Connection

**Scenario:** User has no internet connectivity

**Detection:** Request times out or fails to connect

**Frontend Response:**
1. Show "No internet connection" message
2. Offer "Retry" button
3. Consider showing offline indicator in header
4. Queue actions to retry when online (optional)

**Example:**
```javascript
try {
  const response = await fetch(url, options);
} catch (error) {
  if (!navigator.onLine) {
    showError({
      title: 'No Internet Connection',
      message: 'Please check your internet connection and try again.',
      icon: 'wifi-off',
      actions: [{
        text: 'Retry',
        onClick: retryRequest
      }]
    });
  } else {
    // Other network error
    showError({
      title: 'Connection Error',
      message: 'Unable to connect to server. Please try again.',
      actions: [{
        text: 'Retry',
        onClick: retryRequest
      }]
    });
  }
}
```

---

## Best Practices

### 1. Always Handle Errors

```javascript
// ❌ Bad
const response = await api.sendMessage(data);
setMessages([...messages, response.data]);

// ✅ Good
try {
  const response = await api.sendMessage(data);
  setMessages([...messages, response.data]);
} catch (error) {
  if (error.response?.status === 402) {
    showInsufficientCreditsModal();
  } else {
    showError('Failed to send message. Please try again.');
  }
}
```

### 2. Provide Context

```javascript
// ❌ Bad
showError('An error occurred');

// ✅ Good
showError('Failed to update profile. Please try again.');
```

### 3. Offer Actions

```javascript
// ❌ Bad
showError('Failed to load messages');

// ✅ Good
showError({
  message: 'Failed to load messages',
  actions: [{
    text: 'Retry',
    onClick: loadMessages
  }]
});
```

### 4. Log Errors

```javascript
try {
  const response = await api.call();
} catch (error) {
  // Log for debugging
  console.error('API Error:', {
    endpoint: error.config?.url,
    status: error.response?.status,
    message: error.message,
    timestamp: new Date().toISOString()
  });

  // Show user-friendly message
  showError('Something went wrong. Please try again.');
}
```

### 5. Graceful Degradation

```javascript
// Load user data with fallback
try {
  const user = await api.getCurrentUser();
  setUser(user);
} catch (error) {
  console.error('Failed to load user:', error);
  // Continue with cached/default data
  setUser(getCachedUser() || DEFAULT_USER);
}
```

---

## Error Display Components

### Toast Notifications (For Minor Errors)

Use for:
- Form validation errors
- Network timeouts
- Non-critical failures

```javascript
toast.error('Failed to update profile');
```

### Modal Dialogs (For Important Errors)

Use for:
- Session expiration
- Insufficient credits
- Account issues
- Payment errors

```javascript
showModal({
  title: 'Session Expired',
  message: 'Your session has expired. Please log in again.',
  primaryAction: {
    text: 'Log In',
    onClick: () => navigate('/login')
  }
});
```

### Inline Errors (For Form Validation)

Use for:
- Field-specific validation
- Real-time validation feedback

```javascript
<input
  name="email"
  error={fieldErrors.email}
  helperText={fieldErrors.email}
/>
```

---

## Testing Error Handling

### Manual Testing Checklist

- [ ] Test with expired token (wait 24 hours or modify token manually)
- [ ] Test with invalid token (modify token manually)
- [ ] Test with no token (clear localStorage)
- [ ] Test with no internet (disable network in DevTools)
- [ ] Test rate limiting (make many requests quickly)
- [ ] Test validation errors (submit invalid form data)
- [ ] Test 402 errors (send message with 0 credits)
- [ ] Test account deactivation
- [ ] Test password change (invalidates all tokens)

### Simulating Errors in Development

```javascript
// Simulate 401 error
if (import.meta.env.DEV && window.simulateExpiredToken) {
  throw new Error401('Token expired');
}

// Simulate network error
if (import.meta.env.DEV && window.simulateOffline) {
  throw new NetworkError('Failed to fetch');
}
```

---

## Summary

**Key Points:**
1. Always handle errors in API calls
2. Provide clear, user-friendly error messages
3. Offer actionable solutions (retry, buy credits, etc.)
4. Handle 401 errors by attempting token refresh first
5. Log errors for debugging but don't expose technical details to users
6. Use appropriate UI components (toast vs modal) based on severity
7. Test error handling thoroughly

**Frontend Checklist:**
- ✅ Global error interceptor configured
- ✅ Token refresh logic implemented
- ✅ 401 → logout flow working
- ✅ 402 → buy credits flow working
- ✅ Validation errors show field-specific messages
- ✅ Network errors handled gracefully
- ✅ Rate limiting shows countdown
- ✅ Error logging configured

---

*For backend error codes and details, see: `/docs/BACKEND_ARCHITECTURE.md`*
*For API endpoints and authentication, see: `/docs/PHASE1_SETUP.md`*
