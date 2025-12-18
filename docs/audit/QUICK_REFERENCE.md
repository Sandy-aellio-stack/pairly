# TrueBond Quick Reference Guide

## 🚀 Quick Start

### Access URLs
- **Landing Page**: https://datebond.preview.emergentagent.com
- **User Dashboard**: https://datebond.preview.emergentagent.com/dashboard
- **Admin Dashboard**: https://datebond.preview.emergentagent.com/admin

### Test Credentials
```
Email: john.doe.test123@example.com
Password: TestPass@123
```

---

## 📁 File Locations

### Frontend Key Files
```
/app/frontend/src/
├── App.jsx                    # Main routing
├── main.jsx                   # Entry point
├── index.css                  # Global styles
├── services/api.js            # API calls
├── store/authStore.js         # Auth state
└── pages/
    ├── LandingPage.jsx        # Home
    ├── LoginPage.jsx          # Login
    ├── SignupPage.jsx         # Registration
    ├── dashboard/             # User pages
    └── admin/                 # Admin pages
```

### Backend Key Files
```
/app/backend/
├── server.py                  # Entry point
├── main.py                    # FastAPI app
├── models/tb_*.py             # Database models
├── routes/tb_*.py             # API endpoints
└── services/tb_*.py           # Business logic
```

---

## 🔗 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/signup` | Register |
| POST | `/api/auth/login` | Login |
| GET | `/api/auth/me` | Current user |

### Core Features
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/credits/balance` | Get balance |
| GET | `/api/credits/pricing` | Get pricing |
| GET | `/api/messages/conversations` | Get chats |
| POST | `/api/messages/send` | Send message |
| GET | `/api/location/nearby` | Nearby users |
| POST | `/api/payments/create-order` | Buy coins |

---

## 💰 Pricing Structure

| Action | Cost |
|--------|------|
| Send Message | 1 coin |
| Audio Call | 5 coins/min |
| Video Call | 10 coins/min |
| Signup Bonus | +10 FREE |

### Coin Packages
| Package | Coins | Price |
|---------|-------|-------|
| Starter | 50 | ₹100 |
| Basic | 150 | ₹250 |
| Popular | 350 | ₹500 |
| Premium | 800 | ₹1000 |

---

## 🎨 Color Palette

```css
--background: #F8FAFC;     /* Misty Morning */
--primary: #0F172A;        /* Midnight Navy */
--accent-1: #E9D5FF;       /* Soft Lavender */
--accent-2: #DBEAFE;       /* Sky Petal */
--accent-3: #FCE7F3;       /* Warm Blush */
--purple: #7C3AED;         /* Section Headers */
```

---

## 🛠 Common Commands

```bash
# Restart services
sudo supervisorctl restart backend
sudo supervisorctl restart frontend

# View logs
tail -f /var/log/supervisor/backend.*.log

# Install packages
cd /app/frontend && yarn add <package>
pip install <package>

# Check status
sudo supervisorctl status
```

---

## 📱 Page Routes

### Public Routes
| Route | Page |
|-------|------|
| `/` | Landing Page |
| `/login` | Login |
| `/signup` | Registration |
| `/terms` | Terms of Service |
| `/privacy` | Privacy Policy |
| `/about` | About Us |
| `/contact` | Contact |

### Protected Routes (Requires Login)
| Route | Page |
|-------|------|
| `/dashboard` | Home |
| `/dashboard/chat` | Messages |
| `/dashboard/nearby` | Nearby Map |
| `/dashboard/profile` | Profile |
| `/dashboard/credits` | Buy Coins |
| `/dashboard/settings` | Settings |
| `/call/:userId` | Call Screen |

### Admin Routes
| Route | Page |
|-------|------|
| `/admin` | Dashboard |
| `/admin/users` | User Management |
| `/admin/moderation` | Content Review |
| `/admin/analytics` | Analytics |
| `/admin/settings` | App Settings |
| `/admin/logs` | Audit Log |

---

## ✅ Feature Checklist

### Completed ✅
- [x] Landing Page (10+ sections)
- [x] User Registration (4 steps)
- [x] User Login
- [x] User Dashboard
- [x] Messaging System
- [x] Credits System
- [x] Payment Integration (Razorpay)
- [x] Profile Management
- [x] Photo Upload
- [x] Settings Page
- [x] Admin Dashboard
- [x] Admin Analytics (Charts)
- [x] User Management
- [x] Content Moderation UI
- [x] Custom Heart Cursor

### Pending ⚠️
- [ ] WebRTC Calling (UI ready)
- [ ] Mapbox Integration (using OSM)
- [ ] OTP Verification (backend ready)
- [ ] Real-time Chat (WebSocket)
- [ ] Push Notifications

---

## 🔐 Security Notes

1. **JWT Tokens**: Access (30min) + Refresh (7 days)
2. **Passwords**: Bcrypt hashed
3. **Private Data**: Address/phone never exposed
4. **Rate Limiting**: Active on all endpoints
5. **HTTPS**: Required in production

---

## 📊 Database Collections

| Collection | Purpose |
|------------|---------|
| `tb_users` | User accounts |
| `tb_messages` | Chat messages |
| `tb_credits` | Transactions |
| `tb_payments` | Payment records |
| `profiles` | Extended profiles |

---

*TrueBond v1.0.0 | December 2024*
