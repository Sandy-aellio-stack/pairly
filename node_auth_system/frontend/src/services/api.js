import axios from 'axios';

const api = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api', // Matches default backend PORT 5000
    headers: {
        'Content-Type': 'application/json'
    }
});

export const authAPI = {
    // Matches new route names
    sendEmailOTP: (email) => api.post('/auth/send-email-otp', { email }),
    verifyEmailOTP: (email, otp) => api.post('/auth/verify-email-otp', { email, otp }),
    firebaseLogin: (data) => api.post('/auth/firebase-login', data),
    login: (data) => api.post('/auth/login', data)
};

export default api;
