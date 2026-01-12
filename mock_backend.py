#!/usr/bin/env python3
"""
Simple mock backend for testing login flow
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from urllib.parse import urlparse, parse_qs

class MockBackendHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/api/health':
            self.send_json_response(200, {
                "status": "healthy",
                "service": "truebond-mock",
                "version": "1.0.0"
            })
        elif self.path == '/api/auth/me':
            # Mock user data
            auth_header = self.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                self.send_json_response(200, {
                    "id": "mock-user-123",
                    "name": "Test User",
                    "email": "test@example.com",
                    "age": 25,
                    "gender": "male",
                    "bio": "Test bio",
                    "profile_pictures": [],
                    "preferences": {
                        "interested_in": "female",
                        "min_age": 18,
                        "max_age": 35,
                        "max_distance_km": 50
                    },
                    "intent": "dating",
                    "mobile_number": "+1234567890",
                    "credits_balance": 100,
                    "is_verified": True,
                    "is_online": True,
                    "created_at": "2024-01-01T00:00:00Z"
                })
            else:
                self.send_json_response(401, {"detail": "Unauthorized"})
        else:
            self.send_json_response(404, {"detail": "Not found"})

    def do_POST(self):
        """Handle POST requests"""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')

        try:
            data = json.loads(body) if body else {}
        except:
            data = {}

        if self.path == '/api/auth/login':
            # Mock login - accept any email/password for testing
            self.send_json_response(200, {
                "message": "Login successful",
                "user_id": "mock-user-123",
                "tokens": {
                    "access_token": "mock-access-token-12345",
                    "refresh_token": "mock-refresh-token-67890",
                    "token_type": "bearer",
                    "user_id": "mock-user-123"
                }
            })
        elif self.path == '/api/auth/signup':
            # Mock signup
            self.send_json_response(200, {
                "message": "Account created successfully",
                "user_id": "mock-user-new",
                "credits_balance": 10,
                "tokens": {
                    "access_token": "mock-access-token-new",
                    "refresh_token": "mock-refresh-token-new",
                    "token_type": "bearer",
                    "user_id": "mock-user-new"
                }
            })
        elif self.path == '/api/auth/logout':
            self.send_json_response(200, {"message": "Logged out successfully"})
        else:
            self.send_json_response(404, {"detail": "Not found"})

    def send_json_response(self, status_code, data):
        """Helper to send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format, *args):
        """Custom log format"""
        print(f"[MOCK] {self.command} {args[0]} - {args[1]}")

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8000), MockBackendHandler)
    print("=" * 60)
    print("Mock TrueBond Backend Server")
    print("=" * 60)
    print("Server running at: http://localhost:8000")
    print("Health check: http://localhost:8000/api/health")
    print("\nAvailable endpoints:")
    print("  POST /api/auth/login")
    print("  POST /api/auth/signup")
    print("  GET  /api/auth/me")
    print("  POST /api/auth/logout")
    print("\nPress Ctrl+C to stop")
    print("=" * 60)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        server.shutdown()
