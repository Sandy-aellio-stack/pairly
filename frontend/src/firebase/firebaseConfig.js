import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";

// These values should ideally come from .env (VITE_FIREBASE_...)
const firebaseConfig = {
    apiKey: "REAL_FIREBASE_API_KEY",
    authDomain: "PROJECT.firebaseapp.com",
    projectId: "PROJECT_ID",
    storageBucket: "PROJECT.appspot.com",
    messagingSenderId: "SENDER_ID",
    appId: "APP_ID"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
