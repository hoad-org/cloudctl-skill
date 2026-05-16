# CloudctlSkill Project Configuration

## Repository Overview

This repository contains **CloudctlSkill v2.0.0** — an enterprise-grade Python library for cloud context management with Model Context Protocol (MCP) integration for Claude.

**Key Facts:**
- **Purpose**: Multi-cloud context management (AWS, GCP, Azure, OCI)
- **Model**: Zero-credential architecture (credentials handled externally)
- **Integration**: MCP server for Claude (`/cloudctl` command)
- **Status**: Production-ready, 48+ tests passing, v2.0.0 with OCI support

## When to Use CloudctlSkill

Use CloudctlSkill when:
1. **Switching cloud contexts** in Claude workflows
2. **Managing multi-cloud operations** (AWS, GCP, Azure)
3. **Verifying cloud credentials and access**
4. **Checking current cloud context** (provider, account, region)
5. **Automating cloud operations** without credential management

## Architecture

```
User Request (/cloudctl command in Claude)
    ↓
Claude MCP Server (mcp.py)
    ↓
CloudctlSkill Library (skill.py)
    ↓
cloudctl Binary (handles SSO/authentication)
    ↓
Cloud Provider (AWS/GCP/Azure)
```

**Key Design Principle**: cloudctl binary manages all authentication. CloudctlSkill is a stateless wrapper.

## Configuration Strategy

### ✅ CRITICAL ARCHITECTURE PRINCIPLE

**All configuration belongs in cloudctl, NOT in CloudctlSkill code.**

```
CloudctlSkill Code Repository (Public/Safe)
    ↓ (reads from)
Local Filesystem Only (Private/Secure)
    ├─ ~/.config/cloudctl/orgs.yaml ← ALL organization config here
    ├─ ~/.aws/ ← AWS credentials (AWS CLI manages)
    ├─ ~/.config/gcloud/ ← GCP credentials (gcloud manages)
    └─ ~/.azure/ ← Azure credentials (Azure CLI manages)
```

### Master Configuration: ~/.config/cloudctl/orgs.yaml

All organization definitions stored here (local machine only, never in repo):

```yaml
orgs:
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

  - name: gcp-terrorgems
    provider: gcp
    default_project: asatst-gemini-api-v2
    default_region: us-central1
    allowed_regions:
      - us-central1
      - europe-west1
      - asia-southeast1

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

enabled_orgs:
  - myorg
  - gcp-terrorgems
  - azure-craighoad
```

**IMPORTANT**: 
- ✅ Subscription/Tenant IDs are metadata only (not secrets)
- ✅ Actual credentials managed by cloud CLIs (AWS CLI, gcloud, az)
- ✅ This file NEVER committed to repository
- ✅ Add `.config/cloudctl/` to .gitignore

### CloudctlSkill Configuration: ~/.cloudctl.yaml (Optional)

Defines skill-specific settings (optional, not required):

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
  GCLOUD_PROJECT: my-dev-project
  AZURE_SUBSCRIPTION_ID: 18c17ed4-4932-4ddc-91e6-bef66bb2129b
```

### Skill Registration: ~/.claude/skills/cloudctl/SKILL.md

CloudctlSkill is registered as a legacy skill (not MCP in current Claude version):

```yaml
name: cloudctl
displayName: CloudctlSkill
description: Multi-cloud context management for AWS, GCP, and Azure
```

**Location**: `~/.claude/skills/cloudctl/SKILL.md`

## Development Workflow

### Setup

```bash
# 1. Clone and install
git clone https://github.com/rhyscraig/cloudctl-skill
cd cloudctl-skill
make install-dev

# 2. Set up configuration
cp .cloudctl.example.yaml ~/.cloudctl.yaml
nano ~/.cloudctl.yaml

# 3. Verify cloudctl is installed
cloudctl status
```

### Development

```bash
# Run tests
make test

# Run with coverage
make test-cov

# Format code
make format

# Type check
make type-check

# Lint
make lint
```

### Testing

```bash
# All tests
make test

# Unit tests only
make test-unit

# Security tests only
make test-security

# Integration tests
make test-integration

# With coverage
make test-cov
```

## File Organization

```
cloudctl-skill/
├── src/cloudctl_skill/
│   ├── __init__.py          # Package initialization
│   ├── mcp.py               # MCP server for Claude
│   ├── skill.py             # Core CloudctlSkill class
│   ├── models.py            # Pydantic data models
│   ├── config.py            # Configuration loading
│   └── ...                  # Other modules
├── tests/
│   ├── test_cloudctl_skill.py       # Unit tests
│   ├── test_security.py             # Security tests
│   └── ...
├── docs/
│   ├── ARCHITECTURE.md      # Architecture details
│   ├── API.md               # API reference
│   ├── CONFIGURATION.md     # Configuration guide
│   └── ...
├── .claude/
│   ├── SKILL.md             # Integration guide
│   ├── CLAUDE.md            # This file
│   ├── cloudctl.md          # User guide
│   └── skills/cloudctl.json # Skill manifest
├── skill.md                 # Skill definition
├── pyproject.toml           # Python package config
├── requirements.txt         # Dependencies
├── Makefile                 # Development commands
└── pytest.ini               # Test configuration
```

## Key Files

| File | Purpose |
|------|---------|
| `src/cloudctl_skill/mcp.py` | MCP server - handles JSON-RPC requests from Claude |
| `src/cloudctl_skill/skill.py` | Core logic - context management, switching, validation |
| `src/cloudctl_skill/models.py` | Data models - CloudContext, CommandResult, HealthCheckResult |
| `tests/test_cloudctl_skill.py` | Unit tests - 30 core tests |
| `tests/test_security.py` | Security tests - credential safety validation |
| `.claude/SKILL.md` | Integration guide for Claude |
| `.claude/cloudctl.md` | Complete user guide |
| `skill.md` | Skill definition with examples |
| `COMPREHENSIVE_TEST_REPORT.md` | Test results and validation |
| `TROUBLESHOOTING.md` | Debugging guide |
| `docs/ARCHITECTURE.md` | System architecture |
| `docs/CONFIGURATION.md` | Configuration reference |

## Security Model

CloudctlSkill follows **defense-in-depth security** with zero configuration in code:

### Code Repository (Public/Safe)
✅ **Zero configuration** — No org names, IDs, or settings  
✅ **No credentials** — Never stored or handled  
✅ **No sensitive data** — Only generic code  
✅ **Stateless wrapper** — Calls cloudctl, returns results  
✅ **Safe to open-source** — No secrets to protect  

### Local Machine (Private/Secure)
✅ **Organization config** — `~/.config/cloudctl/orgs.yaml`  
✅ **AWS credentials** — `~/.aws/` (AWS CLI manages)  
✅ **GCP credentials** — `~/.config/gcloud/` (gcloud manages)  
✅ **Azure credentials** — `~/.azure/` (Azure CLI manages)  
✅ **Audit logs** — `~/.config/cloudctl/audit/` (JSONL format)  

### Code Quality
✅ **Pydantic validation** — All inputs/outputs validated  
✅ **Immutable models** — Frozen dataclasses  
✅ **Async safety** — No blocking operations  
✅ **Pre-commit hooks** — Prevent credential commits  
✅ **48 security tests** — Comprehensive coverage  

**Golden Rule**: The `cloudctl` binary handles all authentication. CloudctlSkill code reads from local filesystem only.

## Testing Strategy

### Test Coverage

| Category | Tests | Status |
|----------|-------|--------|
| Models & Data | 9 | ✅ Pass |
| Configuration | 5 | ✅ Pass |
| Context Operations | 4 | ✅ Pass |
| Credentials | 2 | ✅ Pass |
| Health Checks | 1 | ✅ Pass |
| Multi-Cloud | 3 | ✅ Pass |
| Error Handling | 1 | ✅ Pass |
| Integration | 2 | ✅ Pass |
| Async Operations | 1 | ✅ Pass |
| Security | 14 | ✅ Pass |
| **Total** | **48** | **✅ 100%** |

### Running Tests

```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=cloudctl_skill --cov-report=html

# Specific test suite
pytest tests/test_cloudctl_skill.py -v
pytest tests/test_security.py -v

# Async tests only
pytest tests/ -v -m asyncio

# With markers
pytest tests/ -m "not slow"
```

## CI/CD & Deployment

### Pre-commit Hooks

The repository includes pre-commit hooks to prevent credential leakage:
- No AWS keys allowed in commits
- No private keys in source
- No credential assignments
- Configuration files validated

### GitHub Actions

Tests run on:
- Python 3.12+
- All major cloud providers supported
- 100% test pass requirement

## Documentation

### User Documentation
- **`.claude/SKILL.md`** — How Claude should use CloudctlSkill
- **`.claude/cloudctl.md`** — Complete user guide with examples
- **`skill.md`** — Skill definition and capabilities

### Developer Documentation
- **`docs/ARCHITECTURE.md`** — System design and components
- **`docs/API.md`** — Complete API reference
- **`docs/CONFIGURATION.md`** — Configuration options

### Reports & Guides
- **`COMPREHENSIVE_TEST_REPORT.md`** — Full test results
- **`TROUBLESHOOTING.md`** — Debugging guide

## Troubleshooting

### Common Issues

**"cloudctl-skill not found"**
```bash
pip install cloudctl-skill
```

**"/cloudctl command not visible"**
- Fully close and reopen Claude
- Check settings.json has MCP registration
- Verify cwd parameter points to correct directory

**"No active context found"**
```bash
cloudctl login
cloudctl switch <org>
```

**Tests failing**
```bash
# Run with verbose output
pytest tests/ -vvv

# Check pytest configuration
cat pytest.ini
```

## Related Resources

- **GitHub Repository**: https://github.com/rhyscraig/cloudctl-skill
- **Issue Tracker**: https://github.com/rhyscraig/cloudctl-skill/issues
- **Discussions**: https://github.com/rhyscraig/cloudctl-skill/discussions

## Multi-Cloud Support

CloudctlSkill supports three major cloud providers with configuration stored entirely in cloudctl, not in the skill code.

### AWS (myorg)
- **Provider**: AWS
- **Config Location**: `~/.config/cloudctl/orgs.yaml`
- **Credentials**: `~/.aws/` (AWS CLI managed)
- **Auth Method**: AWS SSO / IAM roles
- **All 12 Tools**: Fully supported

### GCP (gcp-terrorgems)
- **Provider**: Google Cloud Platform
- **Config Location**: `~/.config/cloudctl/orgs.yaml`
- **Credentials**: `~/.config/gcloud/` (gcloud managed)
- **Auth Method**: gcloud auth / service accounts
- **All 12 Tools**: Fully supported

### Azure (azure-craighoad)
- **Provider**: Microsoft Azure
- **Config Location**: `~/.config/cloudctl/orgs.yaml`
- **Credentials**: `~/.azure/` (Azure CLI managed)
- **Auth Method**: Azure CLI / service principals
- **All 12 Tools**: Fully supported

### Oracle Cloud Infrastructure (oci-craighoad) — New in v2.0.0
- **Provider**: Microsoft Azure
- **Config Location**: `~/.config/cloudctl/orgs.yaml`
- **Credentials**: `~/.azure/` (Azure CLI managed)
- **Auth Method**: Azure CLI / service principals
- **All 12 Tools**: Fully supported

### Verification

Check multi-cloud setup:
```bash
# List all organizations
cloudctl org list

# Should show:
# Configured Organizations (3)
#   myorg [AWS] enabled
#   gcp-terrorgems [GCP] enabled
#   azure-craighoad [AZURE] enabled
```

## When Adding Features to CloudctlSkill

### Do NOT Add Configuration

❌ **NEVER** add organization names to the code  
❌ **NEVER** add subscription/tenant IDs to the code  
❌ **NEVER** add account numbers to the code  
❌ **NEVER** hardcode default regions  
❌ **NEVER** store credentials anywhere  

### DO Add Tests

✅ **ALWAYS** write tests first (TDD)  
✅ **ALWAYS** test with local cloudctl config only  
✅ **ALWAYS** ensure >85% coverage  
✅ **ALWAYS** add security tests if touching credentials  
✅ **ALWAYS** run `make test-cov` before commit  

### DO Update Documentation

✅ **ALWAYS** update `docs/CLOUDCTLSKILL_DOCUMENTATION.md`  
✅ **ALWAYS** update relevant API docs  
✅ **ALWAYS** add examples in `.claude/cloudctl.md`  
✅ **ALWAYS** update this file if architecture changes  

### Process for Adding Features

```bash
# 1. Write tests first
vim tests/test_cloudctl_skill.py

# 2. Implement feature
vim src/cloudctl_skill/skill.py

# 3. Run tests
make test-cov

# 4. Verify no hardcoded config
grep -r "18c17ed4\|bd93c484\|myorg\|gcp-terrorgems" src/

# 5. Format and lint
make lint format type-check

# 6. Update documentation
vim docs/CLOUDCTLSKILL_DOCUMENTATION.md

# 7. Create PR with test results
```

## Contributing

Contributions welcome! When adding features:

1. **Write tests first** (TDD approach)
2. **Ensure all 48 tests pass** (`make test`)
3. **Add security tests** if handling credentials
4. **Add configuration safety tests** if parsing config
5. **Update documentation** (code + markdown)
6. **Run quality checks**: `make lint format type-check`
7. **Create PR with test results**

**Golden Rule**: Code is generic. Configuration lives in cloudctl. Credentials never appear in the repo.

## License

MIT License — See LICENSE file

---

**Documentation**:
- User Guide: `.claude/cloudctl.md`
- Integration Guide: `.claude/SKILL.md`
- Full Documentation: `docs/CLOUDCTLSKILL_DOCUMENTATION.md`
- API Reference: `docs/API.md`
- Architecture: `docs/ARCHITECTURE.md`
- Troubleshooting: `TROUBLESHOOTING.md`

**Questions?** Check the docs or TROUBLESHOOTING.md
