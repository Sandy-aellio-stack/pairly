#!/bin/bash
echo "================================"
echo "TrueBond Login Flow Test"
echo "================================"
echo ""
echo "Testing backend endpoints..."
echo ""

echo "1. Health Check:"
curl -s http://localhost:8000/api/health | python3 -m json.tool
echo ""

echo "2. Login Test:"
curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}' | python3 -m json.tool
echo ""

echo "3. Get User Data:"
curl -s http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer mock-access-token-12345" | python3 -m json.tool
echo ""

echo "================================"
echo "All tests completed!"
echo ""
echo "Frontend: http://localhost:5173"
echo "Backend:  http://localhost:8000"
echo "================================"
