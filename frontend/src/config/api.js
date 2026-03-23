// When VITE_API_URL is not set, use relative URLs (empty string).
// The Vite dev server proxies /api and /socket.io to localhost:8000.
// In production, set VITE_API_URL to the full backend URL.

export const API_BASE_URL =
    typeof import.meta.env.VITE_API_URL === "string" && import.meta.env.VITE_API_URL !== ""
        ? import.meta.env.VITE_API_URL
        : ""; // Use proxy in development

// Fallback full backend URL for direct connection if proxy fails
export const FALLBACK_API_BASE_URL = "http://localhost:8000/api";
