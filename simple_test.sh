#!/bin/bash

echo "=== Multi-Cloud Context Management Test ==="
echo ""

echo "1. Current Status (should be empty)"
cloudctl status && echo "✓ Status check passed" || echo "✗ No active context (expected)"
echo ""

echo "2. Listing all organizations"
cloudctl org list
echo ""

echo "3. Testing AWS (myorg)"
cloudctl switch myorg > /dev/null 2>&1 && \
  RESULT=$(cloudctl status 2>&1) && \
  echo "✓ AWS switched successfully" || echo "✗ AWS switch failed"
echo "   Status: $(cloudctl status 2>&1 | head -1)"
echo ""

echo "4. Testing GCP (gcp-terrorgems)"
cloudctl switch gcp-terrorgems > /dev/null 2>&1 && \
  echo "✓ GCP switched successfully" || echo "✗ GCP switch failed"
echo "   Status: $(cloudctl status 2>&1 | head -1)"
echo ""

echo "5. Testing Azure (azure-craighoad)"
cloudctl switch azure-craighoad > /dev/null 2>&1 && \
  echo "✓ Azure switched successfully" || echo "✗ Azure switch failed"
echo "   Status: $(cloudctl status 2>&1 | head -1)"
echo ""

echo "=== Test Complete ==="
