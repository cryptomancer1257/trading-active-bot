#!/bin/bash

echo "🧪 Testing Marketplace Subscription Control Endpoints"
echo "=================================================="

SUBSCRIPTION_ID=19
PRINCIPAL_ID="ok7jr-d6ktf-idahj-ucbcb-pg5tt-2ayc4-kjkjm-xm6qd-h4uxv-vbnrz-bqe"
API_KEY="bot_f6y2xuvbd0us3dmie61n"
BASE_URL="http://localhost:8000/marketplace"

echo ""
echo "1️⃣ Testing PAUSE subscription..."
echo "================================"
curl -X POST "${BASE_URL}/subscription/pause" \
  -H "Content-Type: application/json" \
  -d "{
    \"subscription_id\": ${SUBSCRIPTION_ID},
    \"principal_id\": \"${PRINCIPAL_ID}\",
    \"api_key\": \"${API_KEY}\"
  }" | jq .

echo ""
echo ""
echo "2️⃣ Testing RESUME subscription..."
echo "================================="
curl -X POST "${BASE_URL}/subscription/resume" \
  -H "Content-Type: application/json" \
  -d "{
    \"subscription_id\": ${SUBSCRIPTION_ID},
    \"principal_id\": \"${PRINCIPAL_ID}\",
    \"api_key\": \"${API_KEY}\"
  }" | jq .

echo ""
echo ""
echo "3️⃣ Testing CANCEL subscription..."
echo "================================="
curl -X POST "${BASE_URL}/subscription/cancel" \
  -H "Content-Type: application/json" \
  -d "{
    \"subscription_id\": ${SUBSCRIPTION_ID},
    \"principal_id\": \"${PRINCIPAL_ID}\",
    \"api_key\": \"${API_KEY}\"
  }" | jq .

echo ""
echo "✅ Test completed!"
