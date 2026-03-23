#!/bin/bash

# Luveloop Development Startup Script
# This script ensures both frontend and backend are running correctly

echo "🚀 Starting Luveloop Development Environment..."

# Check if backend is running on port 8000
echo "📡 Checking backend server..."
if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo "✅ Backend server is running on http://localhost:8000"
else
    echo "❌ Backend server is not running on port 8000"
    echo "💡 Please start the backend with:"
    echo "   cd c:\\Git\\pairly\\backend && python main.py"
    echo "   or: uvicorn main:app --reload --host 0.0.0.0 --port 8000"
    exit 1
fi

# Check if frontend is running on port 5000
echo "🌐 Checking frontend server..."
if curl -s http://localhost:5000 > /dev/null 2>&1; then
    echo "✅ Frontend server is running on http://localhost:5000"
else
    echo "❌ Frontend server is not running on port 5000"
    echo "💡 Please start the frontend with:"
    echo "   cd c:\\Git\\pairly\\frontend && npm run dev"
    exit 1
fi

# Test API connectivity
echo "🔗 Testing API connectivity..."
if curl -s http://localhost:8000/api/messages/test > /dev/null 2>&1; then
    echo "✅ API connectivity is working"
else
    echo "❌ API connectivity test failed"
    echo "💡 Check backend logs for any errors"
    exit 1
fi

echo "🎉 All services are running correctly!"
echo "🌐 Frontend: http://localhost:5000"
echo "📡 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "💡 If you still get 'API connectivity issue' errors:"
echo "   1. Check browser console for detailed error messages"
echo "   2. Ensure CORS is properly configured in backend"
echo "   3. Verify authentication tokens are present"
echo "   4. Check that backend logs show incoming requests"
