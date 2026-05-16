# CloudctlSkill — Multi-Cloud Context Management for Claude

**Version**: 1.2.0  
**Status**: Production Ready  
**Last Updated**: April 26, 2026

---

## Overview

CloudctlSkill is an enterprise-grade Python library that provides seamless multi-cloud context management for Claude through the Model Context Protocol (MCP). It enables autonomous context switching across AWS, Google Cloud Platform (GCP), and Microsoft Azure without requiring credentials to be stored in the skill code.

### Key Features

- ✅ **Multi-Cloud Support**: Manage AWS, GCP, and Azure contexts
- ✅ **Zero Configuration in Code**: All organization data stored locally only
- ✅ **Credential-Free Architecture**: Credentials managed externally by cloud CLIs
- ✅ **12 MCP Tools**: Complete set of cloud context management tools
- ✅ **Context Caching**: Improved performance with configurable TTL
- ✅ **Audit Logging**: Full JSONL compliance logging
- ✅ **Health Checks**: System validation and diagnostics
- ✅ **Production Ready**: 48 comprehensive tests, >85% coverage

---

## Architecture

### 3-Pillar Design

CloudctlSkill follows a three-pillar architecture for maximum flexibility and testability:

```
┌─────────────────────────────────────────────┐
│        MCP Server Layer (mcp.py)            │
│   • JSON-RPC message handling               │
│   • Tool registration (12 async functions)  │
│   • FastMCP framework integration           │
└──────────────────────┬──────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        ▼                             ▼
┌──────────────────────┐    ┌─────────────────┐
│   Skill Layer        │    │   Config Layer  │
│  (skill.py)          │    │  (config.py)    │
│                      │    │                 │
│ • Context mgmt       │    │ • 4-level       │
│ • Switching          │    │   hierarchy     │
│ • Validation         │    │ • Env vars      │
│ • Audit logging      │    │ • Local files   │
│ • Health checks      │    │ • Defaults      │
└──────────────────────┘    └─────────────────┘
        │                             │
        └──────────────┬──────────────┘
                       ▼
        ┌──────────────────────────┐
        │    cloudctl Binary       │
        │  (External Application)  │
        │                          │
        │ • Credential management  │
        │ • Organization switching │
        │ • Cloud provider access  │
        │ • Auth token handling    │
        └──────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
    AWS CLI        gcloud CLI      Azure CLI
```

### Security Model: Zero Secrets

CloudctlSkill implements **defense-in-depth security** with zero credentials in code:

```
┌─────────────────────────────────────────────────────────┐
│  CloudctlSkill Code Repository (Public/Open-Source)     │
├─────────────────────────────────────────────────────────┤
│ ✓ No AWS access keys                                    │
│ ✓ No GCP service account keys                           │
│ ✓ No Azure client secrets                               │
│ ✓ No subscription IDs or tenant IDs                     │
│ ✓ No account numbers                                    │
│ ✓ No API tokens                                         │
│ ✓ No SSH keys                                           │
│ ✓ No passwords                                          │
│                                                         │
│ Only Generic Code:                                      │
│ • Async/await functions                                │
│ • cloudctl binary wrapper                              │
│ • Configuration models (Pydantic)                       │
│ • Error handling                                        │
└─────────────────────────────────────────────────────────┘
                         │
                         │ Calls cloudctl binary
                         ▼
┌─────────────────────────────────────────────────────────┐
│         Local Machine (Secure, Private)                 │
├─────────────────────────────────────────────────────────┤
│ ~/.config/cloudctl/orgs.yaml                            │
│ ├─ Organization names                                   │
│ ├─ Cloud providers (AWS/GCP/Azure)                      │
│ ├─ Subscription IDs (metadata only)                     │
│ ├─ Tenant IDs (metadata only)                           │
│ ├─ Default regions                                      │
│ └─ Allowed regions                                      │
│                                                         │
│ ~/.aws/                                                 │
│ ├─ AWS credentials (AWS CLI managed)                    │
│ └─ AWS configuration                                    │
│                                                         │
│ ~/.config/gcloud/                                       │
│ ├─ GCP credentials (gcloud managed)                     │
│ └─ GCP configuration                                    │
│                                                         │
│ ~/.azure/                                               │
│ ├─ Azure credentials (Azure CLI managed)                │
│ └─ Azure configuration                                  │
└─────────────────────────────────────────────────────────┘
```

---

## Multi-Cloud Configuration

### Supported Cloud Providers

#### 1. Amazon Web Services (AWS)

```yaml
- name: myorg
  provider: aws
  partition: aws
  sso_start_url: https://d-9c67661145.awsapps.com/start
  sso_region: eu-west-2
  default_region: eu-west-2
  allowed_regions:
    - eu-west-1
    - eu-west-2
    - us-east-1
```

**Authentication**: AWS SSO / IAM roles  
**Credentials Stored**: `~/.aws/` (AWS CLI managed)  
**Tool Support**: All 12 tools

#### 2. Google Cloud Platform (GCP)

```yaml
- name: gcp-terrorgems
  provider: gcp
  default_project: asatst-gemini-api-v2
  default_region: us-central1
  allowed_regions:
    - us-central1
    - europe-west1
    - asia-southeast1
```

**Authentication**: gcloud auth / service accounts  
**Credentials Stored**: `~/.config/gcloud/` (gcloud managed)  
**Tool Support**: All 12 tools

#### 3. Microsoft Azure

```yaml
- name: azure-craighoad
  provider: azure
  subscription_id: 18c17ed4-4932-4ddc-91e6-bef66bb2129b
  tenant_id: bd93c484-a208-44fc-bf28-5fbb11ab79ba
  default_region: eastus
  allowed_regions:
    - eastus
    - westus
    - northeurope
    - westeurope
```

**Authentication**: Azure CLI / service principals  
**Credentials Stored**: `~/.azure/` (Azure CLI managed)  
**Tool Support**: All 12 tools

---

## Available Tools (12 MCP Functions)

All tools are available through the `/cloudctl` command in Claude.

### Context Management

#### 1. `cloudctl_context`
Get the currently active cloud context.

```
/cloudctl status
```

**Returns**:
- Provider (aws/gcp/azure)
- Organization name
- Account/Project/Subscription ID
- Current region
- IAM role (if applicable)
- Credential validity
- Last update timestamp

#### 2. `cloudctl_list_orgs`
List all configured cloud organizations.

```
/cloudctl list orgs
```

**Returns**:
- Organization names
- Cloud providers
- Default projects/regions
- Enabled/disabled status

### Context Switching

#### 3. `cloudctl_switch`
Switch to a different cloud organization context.

```
/cloudctl switch <organization>
```

**Parameters**:
- organization: Organization name (myorg, gcp-terrorgems, azure-craighoad)

**Returns**:
- Success/failure status
- New context details
- Time elapsed
- Verification result (if enabled)

#### 4. `cloudctl_switch_region`
Change the active region within current cloud provider.

```
/cloudctl switch region <region>
```

**Parameters**:
- region: Region name (us-west-2, europe-west1, eastus)

**Returns**:
- New region
- Validation status
- Allowed regions list

#### 5. `cloudctl_switch_project`
Switch GCP project or AWS account (if multiple available).

```
/cloudctl switch project <project_id>
```

**Parameters**:
- project_id: Project/account ID

**Returns**:
- Project details
- Validation confirmation

### Credential & Token Management

#### 6. `cloudctl_check_credentials`
Verify credentials are valid across all organizations.

```
/cloudctl verify credentials
```

**Returns**:
- Credential validity per organization
- Expiration times
- Last verified timestamp
- Issues/recommendations

#### 7. `cloudctl_token_status`
Check OAuth token expiration and refresh status.

```
/cloudctl token status
```

**Returns**:
- Token validity
- Expiration time
- Time until expiry
- Last refresh time

#### 8. `cloudctl_verify_credentials`
Perform deep credential validation with cloud providers.

```
/cloudctl verify all
```

**Returns**:
- Per-provider validation results
- IAM permissions check
- Service connectivity status
- Detailed error messages if failed

### Validation & Access

#### 9. `cloudctl_ensure_access`
Ensure current context has required access.

```
/cloudctl ensure access
```

**Returns**:
- Access validation result
- Required permissions
- Missing permissions (if any)
- Recommended fixes

#### 10. `cloudctl_validate_switch`
Validate a context switch operation without executing it.

```
/cloudctl validate switch <organization>
```

**Parameters**:
- organization: Target organization

**Returns**:
- Validation result
- Pre-switch checks
- Potential issues
- Safety assessment

### Health & Diagnostics

#### 11. `cloudctl_health`
Full system health check across all cloud providers.

```
/cloudctl health check
```

**Returns**:
- System status (healthy/degraded/critical)
- cloudctl installation status
- Available organizations count
- Credentials validity
- Access to each cloud provider
- Audit logging status
- Configuration validation

#### 12. `cloudctl_ensure_access` (Alias)
Alias for access validation.

```
/cloudctl access check
```

---

## Installation & Setup

### Prerequisites

- Python 3.12+
- Claude Desktop v1.4758.0 or later
- Cloud CLIs:
  - AWS CLI (for AWS support)
  - gcloud CLI (for GCP support)
  - Azure CLI (for Azure support)

### Installation

```bash
# Clone repository
git clone https://github.com/rhyscraig/cloudctl-skill
cd cloudctl-skill

# Install in development mode
pip install -e .

# Verify installation
cloudctl --version
which cloudctl
```

### Configuration

#### Step 1: Configure Organizations

Edit `~/.config/cloudctl/orgs.yaml`:

```yaml
orgs:
  - name: myorg
    provider: aws
    # ... AWS config

  - name: gcp-terrorgems
    provider: gcp
    # ... GCP config

  - name: azure-craighoad
    provider: azure
    # ... Azure config

enabled_orgs:
  - myorg
  - gcp-terrorgems
  - azure-craighoad
```

#### Step 2: Configure Cloud CLIs

**AWS**:
```bash
aws configure
```

**GCP**:
```bash
gcloud auth login
gcloud config set project <project-id>
```

**Azure**:
```bash
az login --use-device-code
```

#### Step 3: Verify Configuration

```bash
cloudctl org list
cloudctl status
cloudctl health
```

---

## Usage Examples

### Basic Context Management

```bash
# See current context
cloudctl status

# List all organizations
cloudctl org list

# Switch to AWS
cloudctl switch myorg

# Switch to GCP
cloudctl switch gcp-terrorgems

# Switch to Azure
cloudctl switch azure-craighoad
```

### Multi-Cloud Operations

```bash
# Check credentials across all clouds
cloudctl verify credentials

# Check token validity
cloudctl token status

# Full health check
cloudctl health

# Validate access to current context
cloudctl ensure access
```

### Region Management

```bash
# Switch AWS region
cloudctl switch region eu-west-1

# Switch GCP region
cloudctl switch region europe-west1

# Switch Azure region
cloudctl switch region westus
```

### In Claude

```
/cloudctl list orgs
/cloudctl status
/cloudctl switch azure-craighoad
/cloudctl health check
/cloudctl verify credentials
```

---

## Configuration Reference

### ~/.config/cloudctl/orgs.yaml

Master organization configuration file (local machine only).

**Structure**:
```yaml
orgs:
  - name: <organization-name>
    provider: <aws|gcp|azure>
    # Provider-specific configuration
    ...

enabled_orgs:
  - <org-name-1>
  - <org-name-2>
  - <org-name-3>
```

**AWS Fields**:
- `partition` (string): AWS partition (aws, aws-cn, aws-us-gov)
- `sso_start_url` (string): AWS SSO portal URL
- `sso_region` (string): AWS region for SSO
- `default_region` (string): Default AWS region
- `allowed_regions` (list): Regions available for switching

**GCP Fields**:
- `default_project` (string): Default GCP project ID
- `default_region` (string): Default GCP region
- `allowed_regions` (list): Regions available for switching

**Azure Fields**:
- `subscription_id` (string): Azure subscription ID (metadata only)
- `tenant_id` (string): Azure tenant/directory ID (metadata only)
- `default_region` (string): Default Azure region
- `allowed_regions` (list): Regions available for switching

### ~/.cloudctl.yaml (Optional)

Local skill configuration (optional, overrides defaults).

```yaml
cloudctl:
  timeout_seconds: 30
  max_retries: 3
  verify_context_after_switch: true
  enable_audit_logging: true
  enable_caching: true
  cache_ttl_seconds: 300

environment_overrides:
  AWS_REGION: us-west-2
  GCLOUD_PROJECT: my-project
  AZURE_SUBSCRIPTION_ID: <subscription-id>
```

---

## Security Best Practices

### ✅ What CloudctlSkill Does Right

1. **Zero Configuration in Code**
   - No hardcoded organization names
   - No subscription/tenant/account IDs
   - No credentials anywhere
   - Safe for public repositories

2. **Credentials Managed Externally**
   - AWS CLI manages AWS credentials
   - gcloud manages GCP credentials
   - Azure CLI manages Azure credentials
   - CloudctlSkill never touches credentials

3. **Local-Only Configuration**
   - All org data in `~/.config/cloudctl/`
   - Never committed to repositories
   - Never shared with external services
   - Only used locally by cloudctl

4. **Audit Logging**
   - JSONL compliance format
   - Stored in `~/.config/cloudctl/audit/`
   - Includes operation timestamps
   - No sensitive data in logs

### ⚠️ Important Security Notes

1. **Never Commit Configuration**
   ```bash
   # ~/.gitignore
   .cloudctl.yaml
   .azure/
   .aws/
   .config/gcloud/
   ```

2. **Credential Rotation**
   - Rotate AWS credentials regularly
   - Refresh GCP service accounts
   - Refresh Azure tokens with `az login`

3. **CI/CD Considerations**
   - Use service principals (not user accounts)
   - Store credentials in secret management
   - Don't use local cloudctl configs in CI
   - Implement least-privilege access

---

## Testing

### Run Test Suite

```bash
# All tests
make test

# With coverage
make test-cov

# Specific test file
pytest tests/test_cloudctl_skill.py -v

# Multi-cloud tests
./test_multicloud.sh
```

### Test Coverage

- 48 total tests
- >85% code coverage
- Unit tests: Context, switching, validation
- Security tests: Credential safety, secret detection
- Integration tests: Multi-cloud operations
- Async tests: Event loop handling

---

## Troubleshooting

### "No active context found"

```bash
# List available organizations
cloudctl org list

# Switch to an organization
cloudctl switch myorg

# Verify context
cloudctl status
```

### "Command failed with exit code 1"

```bash
# Run health check
cloudctl health

# Check credentials
cloudctl verify credentials

# Check configuration
cat ~/.config/cloudctl/orgs.yaml
```

### "Token expired"

**AWS**:
```bash
aws sso login
```

**GCP**:
```bash
gcloud auth login
```

**Azure**:
```bash
az login --use-device-code
```

### "Organization not found"

```bash
# Verify organization exists
cloudctl org list

# Check orgs.yaml syntax
cat ~/.config/cloudctl/orgs.yaml

# Ensure organization is in enabled_orgs section
```

---

## Performance

### Context Caching

CloudctlSkill caches cloud context to improve performance:

```yaml
cloudctl:
  enable_caching: true
  cache_ttl_seconds: 300  # 5 minutes
```

**Cache Hit**: ~10ms  
**Cache Miss**: ~500ms-1s (depends on cloud provider)

### Audit Logging Performance Impact

Audit logging adds minimal overhead (~5-10ms per operation).

**Storage**: ~1KB per operation  
**Retention**: ~7 days per file

---

## Related Documentation

- **[Architecture Guide](./ARCHITECTURE.md)** — Detailed system design
- **[API Reference](./API.md)** — Complete tool documentation
- **[Configuration Guide](./CONFIGURATION.md)** — Setup and customization
- **[Troubleshooting](../TROUBLESHOOTING.md)** — Common issues and fixes
- **[Security Model](../docs/SECURITY.md)** — Security implementation details

---

## Support & Contributing

### Documentation
- GitHub: https://github.com/rhyscraig/cloudctl-skill
- Issues: https://github.com/rhyscraig/cloudctl-skill/issues
- Discussions: https://github.com/rhyscraig/cloudctl-skill/discussions

### Contributing
1. Fork repository
2. Create feature branch
3. Write tests (>85% coverage required)
4. Submit pull request

---

## Version History

### v1.2.0 (April 26, 2026)
- ✅ Added Azure support
- ✅ Multi-cloud configuration validation
- ✅ Enhanced health checks
- ✅ Audit logging improvements

### v1.1.0
- Added GCP support
- Context caching implementation
- Token status monitoring

### v1.0.0
- Initial release
- AWS support
- Basic context switching

---

## License

MIT License — See LICENSE file for details

---

**CloudctlSkill** — Enterprise cloud context management for Claude  
*Secure. Multi-cloud. Production-ready.*
