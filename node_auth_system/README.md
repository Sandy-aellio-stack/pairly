# Node.js Auth System Setup

This system supports Email and Mobile OTP authentication.

## 🛠️ Quick Start

### 1. Backend Setup
1. `cd node_auth_system`
2. `npm install`
3. Create a `.env` file from `.env.example`.
4. **Mandatory**: Set `MONGO_URL`.
5. **Optional**: Set `EMAIL_USER` and `EMAIL_PASS` (Gmail App Password). If left empty, the system will run in a limited mock mode where OTPs are created and stored, but plaintext OTPs are NOT printed to logs or returned in API responses.
6. `node server.js`

### 2. Frontend Setup
1. Navigate to your React project.
2. Install dependencies: `npm install firebase axios lucide-react`
3. Configure your Firebase Project and add the credentials to your frontend `.env`.

## 🧪 Testing Mock OTP
If you don't have SMTP configured yet:
1. Try to login with an email in the browser.
2. The backend will create the OTP and persist it for verification, but it will not print the plaintext code to logs.
3. To test locally without an email provider, either configure a test SMTP provider or inspect the OTP records in your dev database (not recommended on shared environments).
