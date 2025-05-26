#!/bin/bash

echo "Testing URL routing fixes..."
echo "This script will start the development environment and test URL routing."
echo ""

# Start the development environment
echo "Starting development environment..."
docker-compose up -d --build

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 30

# Test if the frontend is accessible
echo "Testing frontend accessibility..."
if curl -f http://localhost:3001 > /dev/null 2>&1; then
    echo "✅ Frontend is accessible at http://localhost:3001"
else
    echo "❌ Frontend is not accessible"
    exit 1
fi

# Test if backend is accessible
echo "Testing backend accessibility..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is accessible at http://localhost:8000"
else
    echo "❌ Backend is not accessible"
    exit 1
fi

echo ""
echo "🎉 Basic connectivity tests passed!"
echo ""
echo "Manual testing required:"
echo "1. Open http://localhost:3001 in your browser"
echo "2. Try typing URLs directly:"
echo "   - http://localhost:3001/contests"
echo "   - http://localhost:3001/dashboard"
echo "   - http://localhost:3001/dashboard?tab=texts"
echo "3. Verify that dashboard tabs work correctly with URL parameters"
echo ""
echo "To stop the environment, run: docker-compose down" 