# CloudctlSkill Integration Guide

## For Claude Sessions (Code & Desktop)

This repository contains the **CloudctlSkill v2.0.0** — enterprise cloud context management for AWS, GCP, Azure, and OCI with zero credential handling.

### How Claude Should Use This Skill

1. **Via `/cloudctl` command**: Registered as MCP (Model Context Protocol) server in Claude
2. **No credential management**: cloudctl binary handles all SSO/authentication
3. **Master config**: `~/.cloudctl.yaml` defines your organizations

### When to Use the CloudctlSkill

Use the `/cloudctl` command when:
- Switching cloud contexts: `/cloudctl switch prod`
- Checking current context: `/cloudctl context`
- Listing organizations: `/cloudctl list orgs`
- Verifying credentials: `/cloudctl check credentials`
- Running diagnostics: `/cloudctl health`
- Checking token status: `/cloudctl token status myorg`
- Switching regions/projects: `/cloudctl switch region us-east-1`

### Available Commands

**Quick reference**:
```
/cloudctl context              # Current cloud context (provider, org, account, region)
/cloudctl list orgs            # List all configured organizations
/cloudctl switch <org>         # Switch to organization (via SSO)
/cloudctl health               # System diagnostics (5 health checks)
/cloudctl check credentials    # Verify all credentials are valid
/cloudctl token status <org>   # Get token validity for organization
/cloudctl verify credentials <org>  # Verify access to specific org
/cloudctl switch region <region>    # Switch AWS region
/cloudctl switch project <project>  # Switch GCP project
/cloudctl login <org>          # Initiate SSO login
/cloudctl ensure access <org>  # Ensure access with auto-recovery
/cloudctl validate switch      # Validate context switch success
```

### Configuration

**Master config**: `~/.cloudctl.yaml`
- Defines your organizations (AWS, GCP, Azure)
- Specifies regions and projects
- Sets timeout and retry behavior
- Enables audit logging

**Example**:
```yaml
cloudctl:
  timeout_seconds: 30
  max_retries: 3
  verify_context_after_switch: true
  enable_audit_logging: true

environment_overrides:
  AWS_REGION: us-west-2
  GCLOUD_PROJECT: my-project
```

### Security Model

**CloudctlSkill is secret-safe by design:**

✅ **No credentials in code** — Code never touches credentials  
✅ **No credentials in config** — Only organization definitions  
✅ **No credentials in environment** — Optional, managed by user  
✅ **SSO-managed** — cloudctl binary handles all authentication  
✅ **Defense-in-depth** — Immutable models, input validation, audit logging  

**Key principle**: The `cloudctl` binary handles all authentication (SSO, credential refresh, token management). CloudctlSkill just provides Claude commands to use it.

### Integration for Claude Desktop

The `/cloudctl` skill is registered as:
- **MCP Server** in `~/.claude/settings.json`
- **Skill Manifest** in `~/.claude/skills/cloudctl.json`
- **CLI Integration** via `python3 -m cloudctl_skill.mcp`

Claude Desktop will automatically discover `/cloudctl` when:
1. cloudctl-skill is installed: `pip install cloudctl-skill`
2. MCP server is registered in settings.json
3. cloudctl binary is in PATH: `which cloudctl`

### Testing the Skill

```bash
# Verify installation
pip show cloudctl-skill

# Verify cloudctl binary
which cloudctl
cloudctl status

# Test in Claude
/cloudctl health
/cloudctl context
/cloudctl list orgs
```

### Troubleshooting

**"/cloudctl command not found"**
- Ensure cloudctl-skill is installed: `pip install cloudctl-skill`
- Fully close and reopen Claude (not just minimize)
- Settings.json must have MCP server registration with `cwd` parameter
- Verify: `cat ~/.claude/settings.json | grep cloudctl`

**"No active context found"**
- cloudctl doesn't have valid credentials configured
- Solution: `cloudctl login` then `cloudctl switch <org>`

**"Organization not found"**
- Organization name doesn't match configuration
- See available orgs: `/cloudctl list orgs`
- Use exact name from list in switch command

**"Authentication failed"**
- cloudctl couldn't authenticate to the organization
- Test directly: `cloudctl status` and `cloudctl switch <org>`
- If that works, Claude will work too

**"cloudctl: command not found"**
- cloudctl binary isn't installed
- Install for your cloud provider (AWS CLI, gcloud, az)
- Verify: `which cloudctl` and `cloudctl status`

### Integration with Code Sessions

CloudctlSkill integrates seamlessly with your development workflow:

**Before committing**:
- Verify you're in correct cloud context: `/cloudctl context`
- Check credentials: `/cloudctl check credentials`

**When switching contexts**:
- Use `/cloudctl switch <org>` instead of manual env vars
- Automatic region/project setup via `switch region` and `switch project`

**For multi-cloud work**:
- Switch between AWS/GCP/Azure: `/cloudctl list orgs` then `/cloudctl switch`
- No credential re-entry needed—SSO handles it

### Best Practices

1. **Run health check regularly**: `/cloudctl health`
2. **Verify context after switching**: `/cloudctl context`
3. **Never manually export credentials**: CloudctlSkill handles auth
4. **Use SSO for login**: `/cloudctl login <org>` not manual token entry
5. **Check token validity**: `/cloudctl token status <org>` before long operations

## For Developers

The skill source code is in `src/` with:
- **mcp.py** — MCP server implementation (method routing)
- **skill.py** — CloudctlSkill core (context management, switching, validation)
- **models.py** — Pydantic data models (CloudContext, CommandResult, etc.)
- **config.py** — Configuration loading (environment, YAML, defaults)

Tests: `pytest tests/` (54 tests total, 48 core tests passing, 88.9% success)

Architecture:
- Async/await throughout for non-blocking I/O
- Pydantic v2 frozen models for immutability
- MCP (Model Context Protocol) for Claude integration
- Context file fallback when cloudctl unavailable
- Environment variable management for session-level switches

## Related Files

- **`.claude/cloudctl.md`** — Complete Claude user guide
- **`skill.md`** — Skill documentation with examples
- **`COMPREHENSIVE_TEST_REPORT.md`** — Full test results and validation
- **`TROUBLESHOOTING.md`** — Detailed debugging guide
- **`docs/ARCHITECTURE.md`** — System architecture
- **`docs/API.md`** — API reference
- **`docs/CONFIGURATION.md`** — Configuration guide

---

**Ready to use?** Type `/cloudctl health` to get started!
