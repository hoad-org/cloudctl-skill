#!/usr/bin/env python3
"""
Safe Configuration Examples

This demonstrates the CORRECT way to handle configuration and credentials
in CloudctlSkill. All credentials stay external to the code.
"""

import asyncio
import os
from pathlib import Path

from cloudctl_skill import CloudctlSkill


async def example_1_environment_variables() -> None:
    """Example 1: Using environment variables for credentials.

    ✅ CORRECT - Credentials never touch the code
    """
    print("=" * 70)
    print("Example 1: Environment Variables")
    print("=" * 70)
    print()

    # Credentials are set in the environment BEFORE running the script
    # export AWS_ACCESS_KEY_ID="EXAMPLE_KEY_..."
    # export AWS_SECRET_ACCESS_KEY="..."
    # export GCLOUD_APPLICATION_CREDENTIALS="$HOME/.config/gcp/..."

    # The script never sees the actual credentials
    # It only knows they're set
    print("✅ Credentials are in environment, not in code")
    print(f"   AWS configured: {bool(os.environ.get('AWS_ACCESS_KEY_ID'))}")
    print(f"   GCP configured: {bool(os.environ.get('GCLOUD_APPLICATION_CREDENTIALS'))}")
    print()

    # CloudctlSkill passes them to the subprocess
    skill = CloudctlSkill()
    print("✅ CloudctlSkill created without touching credentials")
    print()


async def example_2_local_configuration() -> None:
    """Example 2: Using local configuration files.

    ✅ CORRECT - Configuration is local, never in git
    """
    print("=" * 70)
    print("Example 2: Local Configuration")
    print("=" * 70)
    print()

    # 1. Create local config (~/.cloudctl.yaml)
    example_config = """
# ~/.cloudctl.yaml (NOT in git)

cloudctl:
  timeout_seconds: 30
  max_retries: 3
  verify_context_after_switch: true

environment_overrides:
  AWS_REGION: "us-west-2"
  GCLOUD_PROJECT: "my-project"
  # Credentials come from environment, NOT from this file
"""

    print("Local configuration (~/.cloudctl.yaml):")
    print(example_config)

    # 2. Show that credentials are NOT in this file
    print("✅ Configuration contains only safe, non-sensitive settings")
    print("✅ No credentials in the file")
    print("✅ No real organization names")
    print()

    # 3. Load configuration (it's safe)
    skill = CloudctlSkill()
    print(f"✅ Configuration loaded: timeout={skill.config.cloudctl_timeout}s")
    print()


async def example_3_example_configuration() -> None:
    """Example 3: Using .cloudctl.example.yaml as template.

    ✅ CORRECT - Example shows structure, not real values
    """
    print("=" * 70)
    print("Example 3: Example Configuration Template")
    print("=" * 70)
    print()

    example_template = """
# .cloudctl.example.yaml (IN git, shows structure only)

cloudctl:
  timeout_seconds: 30
  max_retries: 3
  verify_context_after_switch: true
  enable_audit_logging: true

environment_overrides:
  AWS_REGION: us-west-2           # Example region
  # GCLOUD_PROJECT: my-project    # Commented example
  # AWS_PROFILE: default          # Commented example
"""

    print("Template configuration (.cloudctl.example.yaml):")
    print(example_template)

    print("✅ Example shows structure only")
    print("✅ No real credentials")
    print("✅ No real organization names")
    print("✅ Safely committed to public git repository")
    print()


async def example_4_what_not_to_do() -> None:
    """Example 4: What NOT to do (anti-patterns).

    ❌ WRONG WAYS - Never do this!
    """
    print("=" * 70)
    print("Example 4: Anti-Patterns (What NOT to Do)")
    print("=" * 70)
    print()

    antipatterns = """
❌ ANTI-PATTERN 1: Hardcoding credentials in code
    api_key = "sk-12345"  # NEVER!

❌ ANTI-PATTERN 2: Real values in configuration
    api_key: "EXAMPLE_AWS_KEY_12345"  # NEVER!
    secret_value: "secret"     # NEVER! Don't hardcode secrets

❌ ANTI-PATTERN 3: Storing credentials in models
    class CloudctlSkill:
        def __init__(self, api_key: str):  # NEVER!
            self.api_key = api_key

❌ ANTI-PATTERN 4: Real values in example files
    # .cloudctl.example.yaml
    api_key: "EXAMPLE_AWS_KEY_12345"  # NEVER!

❌ ANTI-PATTERN 5: Credentials as function parameters
    async def login(api_key: str):  # NEVER!
        pass

❌ ANTI-PATTERN 6: Storing credentials in test fixtures
    @pytest.fixture
    def config():
        return {"api_key": "EXAMPLE_AWS_KEY_12345"}  # NEVER!

❌ ANTI-PATTERN 7: Real values in documentation
    # README.md
    export AWS_ACCESS_KEY_ID="EXAMPLE_AWS_KEY_12345"  # NEVER!

❌ ANTI-PATTERN 8: Committing .cloudctl.yaml
    git add .cloudctl.yaml  # NEVER! It's in .gitignore!
"""

    print(antipatterns)
    print()


async def example_5_safe_error_handling() -> None:
    """Example 5: Safe error messages that don't leak secrets.

    ✅ CORRECT - Error messages are generic
    """
    print("=" * 70)
    print("Example 5: Safe Error Handling")
    print("=" * 70)
    print()

    # ✅ CORRECT: Generic error messages
    correct_examples = """
✅ CORRECT: Generic, helpful error messages

    Error: "Authentication failed"
    Fix: "Check CLOUDCTL_PATH and credentials"

    Error: "Organization not found"
    Fix: "Run 'skill.list_organizations()' to see available organizations"

    Error: "Command timeout"
    Fix: "Increase CLOUDCTL_TIMEOUT or check network connection"
"""

    # ❌ WRONG: Credentials leak in error messages
    wrong_examples = """
❌ WRONG: Error messages that leak credentials

    Error: f"Auth failed with API key {api_key}"  # NEVER!
    Error: f"Failed with: {os.environ['AWS_SECRET_ACCESS_KEY']}"  # NEVER!
    Error: f"Command failed: {stderr}"  # stderr might contain credentials!
"""

    print(correct_examples)
    print(wrong_examples)
    print("✅ CloudctlSkill only shows generic, safe error messages")
    print()


async def example_6_safe_testing() -> None:
    """Example 6: Safe testing with fake credentials.

    ✅ CORRECT - Tests use fake data only
    """
    print("=" * 70)
    print("Example 6: Safe Testing")
    print("=" * 70)
    print()

    test_code = """
# ✅ CORRECT: Test with fake credentials

@pytest.fixture
def aws_context():
    return CloudContext(
        provider=CloudProvider.AWS,
        organization="test-org",        # Fake
        account_id="123456789012",      # Fake AWS account ID
        region="us-west-2",
        credentials_valid=True,
    )

@pytest.mark.asyncio
async def test_switch_context():
    skill = CloudctlSkill()
    with patch.object(skill, '_execute_cloudctl') as mock:
        mock.return_value = CommandResult(success=True)
        result = await skill.switch_context("test-org")
        assert result.success is True


# ❌ WRONG: Test with real credentials

@pytest.fixture
def aws_context():
    return CloudContext(
        organization="production-org",          # Real! NEVER!
        account_id="987654321012",             # Real AWS account! NEVER!
        credentials_valid=True,
    )

# This fixture would fail the security test suite!
"""

    print(test_code)
    print("✅ CloudctlSkill test suite uses fake data for all tests")
    print()


async def example_7_credential_rotation() -> None:
    """Example 7: Properly rotating credentials.

    ✅ CORRECT - Credentials are rotated externally
    """
    print("=" * 70)
    print("Example 7: Credential Rotation")
    print("=" * 70)
    print()

    print("✅ Proper credential rotation flow:")
    print()
    print("  1. Credentials stored externally (AWS IAM, GCP Console, etc.)")
    print()
    print("  2. Environment variables set before running:")
    print("     $ export AWS_ACCESS_KEY_ID='new-key'")
    print("     $ export AWS_SECRET_ACCESS_KEY='new-secret'")
    print()
    print("  3. CloudctlSkill uses environment variables (never hardcoded)")
    print()
    print("  4. Old credentials revoked in cloud provider")
    print()
    print("  Result: New credentials active, old ones disabled")
    print()
    print("  ✅ CloudctlSkill code never changes")
    print("  ✅ No commits needed to rotate credentials")
    print("  ✅ No credential history in git")
    print()


async def example_8_checking_configuration() -> None:
    """Example 8: Safely checking configuration.

    ✅ CORRECT - Check configuration without showing secrets
    """
    print("=" * 70)
    print("Example 8: Checking Configuration")
    print("=" * 70)
    print()

    print("✅ CORRECT: Check configuration safely")
    print()

    skill = CloudctlSkill()

    print(f"  cloudctl_path: {skill.config.cloudctl_path}")
    print(f"  timeout: {skill.config.cloudctl_timeout}s")
    print(f"  retries: {skill.config.cloudctl_retries}")
    print(f"  caching: {skill.config.enable_caching}")
    print()

    print("  Environment is NOT shown (it's sensitive)")
    print("  ✅ Configuration shown is non-sensitive only")
    print()

    # Check if environment is configured (without showing the values!)
    print("✅ Credentials configuration check:")
    print(f"  AWS configured: {bool(os.environ.get('AWS_ACCESS_KEY_ID'))}")
    print(f"  GCP configured: {bool(os.environ.get('GCLOUD_APPLICATION_CREDENTIALS'))}")
    print()


async def main() -> None:
    """Run all examples."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  CloudctlSkill: Safe Configuration Examples".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")
    print()

    await example_1_environment_variables()
    await example_2_local_configuration()
    await example_3_example_configuration()
    await example_4_what_not_to_do()
    await example_5_safe_error_handling()
    await example_6_safe_testing()
    await example_7_credential_rotation()
    await example_8_checking_configuration()

    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print()
    print("✅ All credentials stay EXTERNAL to CloudctlSkill")
    print("✅ Configuration files contain NO secrets")
    print("✅ Code never stores or handles credentials")
    print("✅ Environment variables pass credentials to subprocess")
    print("✅ subprocess (cloudctl) handles credentials internally")
    print("✅ CloudctlSkill stays secret-free")
    print()


if __name__ == "__main__":
    asyncio.run(main())
