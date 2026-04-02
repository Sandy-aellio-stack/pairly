// Production-ready API configuration
// In development, we fallback to localhost:8000 to ensure socket connectivity
export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// FALLBACK is no longer used, as we strictly rely on env variables for stability
export const FALLBACK_API_BASE_URL = API_BASE_URL;
