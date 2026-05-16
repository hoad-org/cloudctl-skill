#!/bin/bash
#
# Multi-Cloud Test Suite for cloudctl
# Tests AWS, GCP, and Azure authentication and context switching
#
# Usage:
#   ./test_multicloud.sh
#
# Requirements:
#   - cloudctl installed
#   - Azure CLI installed (brew install azure-cli)
#   - Authenticated with all three providers (aws configure, gcloud auth login, az login)
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
print_header() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════${NC}"
}

print_test() {
    echo -e "${YELLOW}▶ $1${NC}"
    ((TESTS_RUN++))
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
    ((TESTS_PASSED++))
}

print_failure() {
    echo -e "${RED}✗ $1${NC}"
    ((TESTS_FAILED++))
}

# Check if cloudctl is installed
check_cloudctl() {
    print_test "Check cloudctl is installed"
    if command -v cloudctl &> /dev/null; then
        CLOUDCTL_VERSION=$(cloudctl --version 2>&1 || echo "unknown")
        print_success "cloudctl found: $CLOUDCTL_VERSION"
    else
        print_failure "cloudctl not found in PATH"
        exit 1
    fi
}

# Check if Azure CLI is installed
check_azure_cli() {
    print_test "Check Azure CLI is installed"
    if command -v az &> /dev/null; then
        AZ_VERSION=$(az --version 2>&1 | head -1)
        print_success "Azure CLI found: $AZ_VERSION"
    else
        print_failure "Azure CLI not found - install with: brew install azure-cli"
        exit 1
    fi
}

# List configured organizations
list_organizations() {
    print_test "List configured organizations"
    ORG_OUTPUT=$(cloudctl org list 2>&1) || {
        print_failure "Failed to list organizations"
        return 1
    }
    echo "$ORG_OUTPUT" | while IFS= read -r line; do
        if [[ $line != "" && $line != *"Configured"* ]]; then
            echo "  $line"
        fi
    done
    print_success "Organizations listed successfully"
}

# Test AWS context
test_aws() {
    print_test "Test AWS context switch (myorg)"
    if cloudctl switch myorg &> /dev/null; then
        STATUS=$(cloudctl status 2>&1)
        if echo "$STATUS" | grep -q "aws\|AWS"; then
            print_success "AWS context switched successfully"
            echo "  Status: $(echo "$STATUS" | head -1)"
            return 0
        else
            print_failure "AWS context switched but status check failed"
            return 1
        fi
    else
        print_failure "Failed to switch to AWS context"
        return 1
    fi
}

# Test GCP context
test_gcp() {
    print_test "Test GCP context switch (gcp-terrorgems)"
    if cloudctl switch gcp-terrorgems &> /dev/null; then
        STATUS=$(cloudctl status 2>&1)
        if echo "$STATUS" | grep -q "gcp\|GCP\|google"; then
            print_success "GCP context switched successfully"
            echo "  Status: $(echo "$STATUS" | head -1)"
            return 0
        else
            print_failure "GCP context switched but status check failed"
            return 1
        fi
    else
        print_failure "Failed to switch to GCP context"
        return 1
    fi
}

# Check if Azure organization exists
check_azure_org() {
    print_test "Check if Azure organization exists"
    if cloudctl org list 2>&1 | grep -q "Azure\|\[AZURE\]"; then
        print_success "Azure organization found"
        return 0
    else
        print_failure "Azure organization not found - add with: cloudctl org add --provider azure --name azure-production"
        return 1
    fi
}

# Test Azure context (if it exists)
test_azure() {
    if ! check_azure_org; then
        echo -e "${YELLOW}⚠ Skipping Azure test - organization not configured${NC}"
        return 0
    fi

    print_test "Test Azure context switch"

    # Find the Azure organization name
    AZURE_ORG=$(cloudctl org list 2>&1 | grep -i "azure\|\[AZURE\]" | head -1 | awk '{print $1}' | tr -d '[:space:]')

    if [ -z "$AZURE_ORG" ]; then
        print_failure "Could not find Azure organization name"
        return 1
    fi

    if cloudctl switch "$AZURE_ORG" &> /dev/null; then
        STATUS=$(cloudctl status 2>&1)
        if echo "$STATUS" | grep -q "azure\|Azure\|AZURE"; then
            print_success "Azure context switched successfully"
            echo "  Organization: $AZURE_ORG"
            echo "  Status: $(echo "$STATUS" | head -1)"
            return 0
        else
            print_failure "Azure context switched but status check failed"
            echo "  Status: $(echo "$STATUS" | head -3)"
            return 1
        fi
    else
        print_failure "Failed to switch to Azure context"
        return 1
    fi
}

# Test sequential context switching
test_sequential_switching() {
    print_test "Test sequential context switching (AWS → GCP → Azure)"

    # AWS
    if ! cloudctl switch myorg &> /dev/null; then
        print_failure "Failed to switch to AWS in sequence"
        return 1
    fi

    # GCP
    if ! cloudctl switch gcp-terrorgems &> /dev/null; then
        print_failure "Failed to switch to GCP in sequence"
        return 1
    fi

    # Azure (if configured)
    AZURE_ORG=$(cloudctl org list 2>&1 | grep -i "azure\|\[AZURE\]" | head -1 | awk '{print $1}' | tr -d '[:space:]')
    if [ ! -z "$AZURE_ORG" ]; then
        if ! cloudctl switch "$AZURE_ORG" &> /dev/null; then
            print_failure "Failed to switch to Azure in sequence"
            return 1
        fi
    fi

    print_success "Sequential context switching works correctly"
    return 0
}

# Print test summary
print_summary() {
    print_header "Test Summary"
    echo -e "Tests run:    ${BLUE}$TESTS_RUN${NC}"
    echo -e "Tests passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Tests failed: ${RED}$TESTS_FAILED${NC}"

    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "\n${GREEN}✓ All tests passed!${NC}"
        return 0
    else
        echo -e "\n${RED}✗ Some tests failed.${NC}"
        return 1
    fi
}

# Main execution
main() {
    print_header "Multi-Cloud Context Management Test Suite"
    echo "Testing AWS, GCP, and Azure context switching with cloudctl"
    echo ""

    # Checks
    check_cloudctl
    check_azure_cli
    echo ""

    # List organizations
    list_organizations
    echo ""

    # Test each provider
    print_header "Testing Cloud Providers"
    test_aws || true
    echo ""

    test_gcp || true
    echo ""

    test_azure || true
    echo ""

    # Test sequential switching
    test_sequential_switching || true
    echo ""

    # Print summary
    print_summary
}

# Run main
main "$@"
