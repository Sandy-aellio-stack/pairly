# Node.js Auth System Setup

This system supports Email and Mobile OTP authentication.

## 🛠️ Quick Start

### 1. Backend Setup
1. `cd node_auth_system`
2. `npm install`
3. Create a `.env` file from `.env.example`.
4. **Mandatory**: Set `MONGO_URL`.
5. **Optional**: Set `EMAIL_USER` and `EMAIL_PASS` (Gmail App Password). If left empty, the system will run in **MOCK MODE** and print OTPs to the terminal.
6. `node server.js`

### 2. Frontend Setup
1. Navigate to your React project.
2. Install dependencies: `npm install firebase axios lucide-react`
3. Configure your Firebase Project and add the credentials to your frontend `.env`.

## 🧪 Testing Mock OTP
If you don't have Gmail SMTP set up yet:
1. Try to login with an email in the browser.
2. Check your **terminal/console** where the backend is running.
3. You will see: `MOCK MODE: OTP for user@example.com is 123456`.
4. Enter that code in the UI to proceed.
