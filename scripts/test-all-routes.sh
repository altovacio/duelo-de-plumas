#!/bin/bash

echo "🧪 Testing all route fixes..."
echo ""

# Test basic connectivity
echo "1. Testing basic connectivity..."
if curl -f http://localhost:3001 > /dev/null 2>&1; then
    echo "✅ Frontend accessible"
else
    echo "❌ Frontend not accessible"
    exit 1
fi

if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend accessible"
else
    echo "❌ Backend not accessible"
    exit 1
fi

if curl -f http://localhost:3001/api/health > /dev/null 2>&1; then
    echo "✅ API proxy working"
else
    echo "❌ API proxy not working"
    exit 1
fi

echo ""

# Test React routes (these should return HTML, not 404)
echo "2. Testing React routes..."

routes=("/contests" "/dashboard" "/admin" "/ai-writer" "/editor")

for route in "${routes[@]}"; do
    response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:3001${route}")
    if [ "$response" = "200" ]; then
        echo "✅ Route ${route} returns 200"
    else
        echo "❌ Route ${route} returns ${response}"
    fi
done

echo ""

# Test API endpoints (these should be proxied correctly)
echo "3. Testing API endpoints..."

api_endpoints=("/api/health" "/api/models")

for endpoint in "${api_endpoints[@]}"; do
    response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:3001${endpoint}")
    if [ "$response" = "200" ] || [ "$response" = "401" ]; then
        echo "✅ API endpoint ${endpoint} proxied correctly (${response})"
    else
        echo "❌ API endpoint ${endpoint} failed (${response})"
    fi
done

echo ""
echo "🎉 Route testing completed!"
echo ""
echo "Manual testing checklist:"
echo "1. Open http://localhost:3001 in your browser"
echo "2. Try typing these URLs directly in the address bar:"
echo "   - http://localhost:3001/contests"
echo "   - http://localhost:3001/dashboard"
echo "   - http://localhost:3001/dashboard?tab=texts"
echo "   - http://localhost:3001/admin (if you're an admin)"
echo "3. Verify that dashboard tabs work correctly with URL parameters"
echo "4. Test browser back/forward navigation" 