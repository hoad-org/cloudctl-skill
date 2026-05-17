---
title: Multi-Cloud Testing Report — 2026-05-17
status: In Progress — GCP/Azure Session Issues Found
date: 2026-05-17
---

# CloudCTL Multi-Cloud Testing Report

## Summary
- ✅ **AWS**: Fully working, context properly set
- ❌ **GCP**: Session creation fails after login
- ❌ **Azure**: Session creation fails after login
- ✅ **Test Suite**: All 296 tests pass (using mocks)
- ❌ **Live Testing**: GCP/Azure switching fails with actual cloudctl binary

---

## Test Environment

```
cloudctl version: 4.1.0
Configured Organizations: 3 (myorg [AWS], gcp-terrorgems [GCP], azure-craighoad [AZURE])
AWS CLI: 2.31.18
Python: 3.13.13
Current Context: AWS (myorg, account 767828739298, role terraform, region eu-west-2)
```

---

## Test Results

### ✅ AWS (myorg)

**Status**: WORKING ✅

```bash
$ cloudctl org list
  myorg  [AWS]  enabled
    https://d-9c67661145.awsapps.com/start

$ cloudctl env
aws:myorg account=767828739298 role=terraform region=eu-west-2

$ cloudctl status
Shell wrapper: OK — Present in /Users/craighoad/.zshrc
AWS CLI: OK — aws-cli/2.31.18
```

**Available AWS Accounts**:
- 824737149338 (hcp-audit)
- 624426145233 (hcp-craighoad-prod)
- 404459110295 (hcp-log-archive)
- 821868546447 (hcp-qa)
- 995039994868 (hcp-shared-services)
- 767828739298 (hcp-terrorgems-prod) ← Current

### ❌ GCP (gcp-terrorgems)

**Status**: BROKEN ❌

**Configuration**:
```yaml
name: gcp-terrorgems
provider: gcp
default_project: asatst-gemini-api-v2
default_region: us-central1
```

**Switch Attempt**:
```
_cloudctl_bin switch gcp-terrorgems
→ No active session for org 'gcp-terrorgems'. Attempting login...
→ ✅ GCP authenticated as admin@craighoad.com
→ 🔄 Refreshing authentication for organization-level operations...
→ ⚠️  Using cached authentication (organization operations may require re-auth)
→ Login Successful.
→ Still no session after login for 'gcp-terrorgems'.

Exit Code: 1
Error: "Unknown error"
```

**Diagnosis**:
- GCP authentication succeeds: `gcloud auth list` shows admin@craighoad.com authenticated
- GCP access token is valid: `gcloud auth application-default print-access-token` returns token
- BUT: Session file is not created after login
- Context remains: `aws:myorg account=767828739298 ...` (unchanged)

**Possible Root Causes**:
1. GCP project `asatst-gemini-api-v2` may not exist or not be accessible
2. cloudctl v4.1.0 may have a bug in GCP session creation
3. gcloud configuration mismatch (current project: `hcp-prd-management`, expected: `asatst-gemini-api-v2`)

### ❌ Azure (azure-craighoad)

**Status**: BROKEN ❌

**Configuration**:
```yaml
name: azure-craighoad
provider: azure
subscription_id: 18c17ed4-4932-4ddc-91e6-bef66bb2129b
tenant_id: bd93c484-a208-44fc-bf28-5fbb11ab79ba
```

**Switch Attempt**:
```
_cloudctl_bin switch azure-craighoad
→ No active session for org 'azure-craighoad'. Attempting login...
→ Login Successful.
→ Still no session after login for 'azure-craighoad'.

Exit Code: 1
Error: "Unknown error"
```

**Diagnosis**:
- Azure authentication appears to succeed (no error during login)
- BUT: Session file is not created after login
- Context remains: `aws:myorg account=767828739298 ...` (unchanged)
- Azure CLI is accessible: `az account list` works

**Possible Root Causes**:
1. cloudctl v4.1.0 may have a bug in Azure session creation (same as GCP)
2. Subscription may not be properly set up in cloudctl

---

## Unit Test Results

**Test Suite Status**: ✅ 296/296 PASS

```
tests/test_mcp_server.py::TestMCPToolFunctions           ✅ 13 pass
tests/test_mcp_server.py::TestMCPServer                  ✅ 3 pass
tests/test_mcp_server.py::TestMCPToolAttributes          ✅ 1 pass
tests/test_mcp_error_paths.py::TestMCPToolErrorHandling  ✅ 15 pass
tests/test_mcp_error_paths.py::TestMCPServerAttributes   ✅ 4 pass
tests/test_*.py (remaining core tests)                   ✅ 259 pass
────────────────────────────────────────────────────────────────
Total:                                                    ✅ 296 pass
```

**Note**: Tests use mocks (`@patch("cloudctl_skill.mcp.CloudctlSkill")`) and do not execute the actual cloudctl binary. Tests pass even though live testing shows GCP/Azure failing.

---

## Live Integration Test Results

### Test 1: MCP Tool - GCP Switch

```python
result = await mcp_module.cloudctl_switch('gcp-terrorgems')

Output:
{
  "success": false,
  "status": "failure",
  "output": "No active session for org 'gcp-terrorgems'...",
  "error": "Unknown error",
  "exit_code": 1
}
```

### Test 2: MCP Tool - Azure Switch

```python
result = await mcp_module.cloudctl_switch('azure-craighoad')

Output:
{
  "success": false,
  "status": "failure",
  "output": "No active session for org 'azure-craighoad'...",
  "error": "Unknown error",
  "exit_code": 1
}
```

### Test 3: Context After Failed Switches

```bash
$ cloudctl env
aws:myorg account=767828739298 role=terraform region=eu-west-2
# ← Context unchanged, still AWS
```

---

## Audit Logs

From `~/.config/cloudctl/audit/operations_20260517.jsonl`:

**GCP Switch Attempt (10:11:40)**:
```json
{
  "operation": "switch_context",
  "context_before": {"provider": "aws", "organization": "myorg"},
  "context_after": null,
  "success": false,
  "error": "Unknown error",
  "duration_ms": 1121.63
}
```

**Azure Switch Attempt (10:11:53)**:
```json
{
  "operation": "switch_context",
  "context_before": {"provider": "aws", "organization": "myorg"},
  "context_after": null,
  "success": false,
  "error": "Unknown error",
  "duration_ms": 8557.09
}
```

---

## Investigation Findings

### 1. ✅ Authentication is Working

Both GCP and Azure successfully authenticate:
- `gcloud auth list` → admin@craighoad.com authenticated
- `gcloud auth application-default print-access-token` → Returns valid access token
- `az account list` → Lists Azure subscriptions

### 2. ❌ Session Creation Fails

After successful authentication, cloudctl cannot create sessions:
- Error message: "Still no session after login for '[org]'"
- No session files created in `~/.config/cloudctl/`
- Context file (`~/.config/cloudctl/context`) remains unchanged

### 3. ❌ Not a TTY/Interactive Issue

This is NOT the expected "cannot prompt during non-interactive execution" error. The error is:
- Cloudctl successfully logs in (reports "Login Successful")
- Then fails to create session (reports "Still no session after login")

### 4. ⚠️ GCP Project Accessibility Issue

GCP configuration references `asatst-gemini-api-v2` but:
- Current gcloud project is `hcp-prd-management`
- Project `asatst-gemini-api-v2` not found in accessible projects list
- Possible missing permissions or project doesn't exist

---

## Fixes Needed

### Priority 1: Diagnose Session Creation Failure

**Action Required**:
1. Check cloudctl v4.1.0 GitHub issues for known GCP/Azure session bugs
2. Verify GCP project `asatst-gemini-api-v2` exists and user has access
3. Verify Azure subscription configuration is correct

**Command to debug**:
```bash
# Enable cloudctl debug output
_cloudctl_bin switch gcp-terrorgems --debug 2>&1

# Check what cloudctl expects
cat ~/.config/cloudctl/orgs.yaml | grep -A 10 gcp-terrorgems
```

### Priority 2: Fix GCP Configuration

**Possible Fixes**:
1. Update `default_project` in `~/.config/cloudctl/orgs.yaml` to a project we actually have access to
2. Verify service account has necessary permissions
3. Try using a different GCP project that's confirmed to be accessible

### Priority 3: Fix Azure Configuration

**Possible Fixes**:
1. Verify subscription ID is correct: `18c17ed4-4932-4ddc-91e6-bef66bb2129b`
2. Run `az account set --subscription [id]` manually to test
3. Check Azure role/permissions for the subscription

### Priority 4: Update Tests

Once fixes are applied:
1. Run live integration tests to confirm GCP/Azure switching works
2. Update unit tests if behavior changes
3. Add integration tests that don't use mocks

---

## Conclusions

1. ✅ **AWS is working perfectly** — No issues, full functionality
2. ❌ **GCP is broken** — Sessions not being created, likely GCP project/access issue
3. ❌ **Azure is broken** — Sessions not being created, likely configuration issue
4. ✅ **Tests pass but don't catch real issues** — Unit tests use mocks, live testing required

---

## Next Steps

1. **Investigate cloudctl v4.1.0 GCP/Azure behavior**
   - Check GitHub issues
   - Check cloudctl documentation
   - See if newer version exists

2. **Validate GCP/Azure configuration**
   - Confirm projects/subscriptions exist
   - Confirm user has access
   - Update config if needed

3. **Test fixes with live testing**
   - Don't rely on unit tests (they use mocks)
   - Manual testing required for validation

4. **Update documentation**
   - Document any workarounds
   - Add troubleshooting guide
   - Update Confluence Rail with findings

---

**Status**: Waiting for fixes to GCP/Azure session creation  
**Blocker**: Cannot switch to GCP/Azure until sessions are created  
**Workaround**: None currently available  
**Impact**: Multi-cloud workflows blocked for GCP/Azure
