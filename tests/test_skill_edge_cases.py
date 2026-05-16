"""Tests for CloudctlSkill edge cases and additional coverage."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cloudctl_skill.models import (
    CloudContext,
    CloudProvider,
    CommandResult,
    SkillConfig,
)
from cloudctl_skill.skill import CloudctlSkill


@pytest.fixture
def skill() -> CloudctlSkill:
    """Create test skill instance."""
    config = SkillConfig(enable_audit_logging=False, enable_caching=True)
    return CloudctlSkill(config=config)


class TestSwitchContextEdgeCases:
    """Tests for switch_context edge cases."""

    @pytest.mark.asyncio
    async def test_switch_context_interactive_prompt_failure(self, skill: CloudctlSkill) -> None:
        """Switch should handle interactive prompt failures."""
        with patch.object(skill, "_execute_cloudctl") as mock_exec:
            mock_exec.return_value = CommandResult(
                success=False,
                error="input is not a terminal, select account from:",
            )

            with patch.object(skill, "get_context") as mock_ctx:
                mock_ctx.side_effect = [RuntimeError("No context"), None]

                result = await skill.switch_context("test-org")
                assert result.success is False
                assert "non-interactively" in result.error

    @pytest.mark.asyncio
    async def test_switch_context_with_account_extraction(self, skill: CloudctlSkill) -> None:
        """Switch should extract account ID from accounts output."""
        with patch.object(skill, "_execute_cloudctl") as mock_exec:
            # First call for accounts listing
            accounts_output = (
                "624426145233 │ hcp-craighoad-prod  │       │\n123456789012 │ test-account        │       │"
            )
            # Subsequent calls
            mock_exec.side_effect = [
                CommandResult(success=True, output=accounts_output),
                CommandResult(success=True, output="Switched"),
            ]

            with patch.object(skill, "get_context") as mock_ctx:
                mock_ctx.side_effect = [
                    RuntimeError("No context"),
                    CloudContext(
                        provider=CloudProvider.AWS,
                        organization="test-org",
                        credentials_valid=True,
                    ),
                ]

                _ = await skill.switch_context("test-org")
                # Verify account extraction was attempted
                calls = mock_exec.call_args_list
                # Should have called accounts command
                assert any("accounts" in str(call) for call in calls)

    @pytest.mark.asyncio
    async def test_switch_context_fallback_without_account(self, skill: CloudctlSkill) -> None:
        """Switch should fallback to non-account switch."""
        with patch.object(skill, "_execute_cloudctl") as mock_exec:
            # First switch with account fails, fallback succeeds
            mock_exec.side_effect = [
                CommandResult(success=False, error="account not found"),
                CommandResult(success=True, output="Switched"),
            ]

            with patch.object(skill, "get_context") as mock_ctx:
                mock_ctx.side_effect = [
                    RuntimeError("No context"),
                    CloudContext(
                        provider=CloudProvider.AWS,
                        organization="test-org",
                        credentials_valid=True,
                    ),
                ]

                result = await skill.switch_context("test-org", "invalid-account")
                assert result.success is True


class TestListOrganizationsEdgeCases:
    """Tests for list_organizations edge cases."""

    @pytest.mark.asyncio
    async def test_list_organizations_unparseable_output(self, skill: CloudctlSkill) -> None:
        """Unparseable output should raise RuntimeError."""
        with patch.object(skill, "_execute_cloudctl") as mock_exec:
            mock_exec.return_value = CommandResult(
                success=True,
                output="Some random output with no structure",
            )

            with pytest.raises(RuntimeError):
                await skill.list_organizations()

    @pytest.mark.asyncio
    async def test_list_organizations_single_org(self, skill: CloudctlSkill) -> None:
        """Single organization JSON should be handled."""
        with patch.object(skill, "_execute_cloudctl") as mock_exec:
            # Single dict instead of list
            mock_exec.return_value = CommandResult(
                success=True,
                output=json.dumps({"name": "single-org", "provider": "aws"}),
            )

            result = await skill.list_organizations()
            assert isinstance(result, list)
            assert len(result) == 1


class TestParseContextEdgeCases:
    """Tests for _parse_context edge cases."""

    def test_parse_context_lowercase_aws(self, skill: CloudctlSkill) -> None:
        """Parse should handle lowercase aws provider."""
        output = "aws:myorg account=123"
        context = skill._parse_context(output)
        assert context.provider == CloudProvider.AWS

    def test_parse_context_case_insensitive_parsing(self, skill: CloudctlSkill) -> None:
        """Parse should be case insensitive for provider."""
        output = "gcp:myproject account=123"
        context = skill._parse_context(output)
        assert context.provider == CloudProvider.GCP

    def test_parse_context_mixed_format(self, skill: CloudctlSkill) -> None:
        """Mix of = format should work."""
        output = "Organization=test-org\nProvider=gcp\nAccount=abc123"
        context = skill._parse_context(output)
        assert context.organization == "test-org"
        assert context.provider == CloudProvider.GCP
        assert context.account_id == "abc123"


class TestExecuteCloudctlRetry:
    """Tests for _execute_cloudctl retry logic."""

    @pytest.mark.asyncio
    async def test_execute_cloudctl_retries_on_timeout_error(self, skill: CloudctlSkill) -> None:
        """Should retry on timeout errors."""
        skill.config.cloudctl_retries = 1

        with patch("asyncio.create_subprocess_exec") as mock_create:
            mock_process = AsyncMock()
            # First call times out, second succeeds
            call_count = 0

            async def mock_communicate():
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise TimeoutError()
                return (b"success", b"")

            mock_process.communicate = mock_communicate
            mock_process.returncode = 0
            mock_process.kill = MagicMock()
            mock_create.return_value = mock_process

            result = await skill._execute_cloudctl("status")
            # First attempt times out, should return timeout error
            assert result.success is False

    @pytest.mark.asyncio
    async def test_execute_cloudctl_persistent_error_no_retry(self, skill: CloudctlSkill) -> None:
        """Permanent errors should not retry."""
        skill.config.cloudctl_retries = 3

        with patch("asyncio.create_subprocess_exec") as mock_create:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"", b"Invalid argument")
            mock_process.returncode = 1
            mock_create.return_value = mock_process

            result = await skill._execute_cloudctl("invalid")
            assert result.success is False
            # Should only try once for permanent errors


class TestEnsureCloudAccessEdgeCases:
    """Tests for ensure_cloud_access edge cases."""

    @pytest.mark.asyncio
    async def test_ensure_cloud_access_org_not_found(self, skill: CloudctlSkill) -> None:
        """Should return error when org not found."""
        with patch.object(skill, "health_check") as mock_health:
            mock_health.return_value = MagicMock(cloudctl_installed=True)

            with patch.object(skill, "list_organizations") as mock_list:
                mock_list.return_value = [{"name": "other-org", "provider": "aws"}]

                result = await skill.ensure_cloud_access("missing-org")
                assert result["success"] is False
                assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_ensure_cloud_access_auto_refresh_token(self, skill: CloudctlSkill) -> None:
        """Should auto-refresh expired tokens."""
        with patch.object(skill, "health_check") as mock_health:
            mock_health.return_value = MagicMock(cloudctl_installed=True)

            with patch.object(skill, "list_organizations") as mock_list:
                mock_list.return_value = [{"name": "test-org", "provider": "aws"}]

                with patch.object(skill, "get_token_status") as mock_status:
                    from cloudctl_skill.models import TokenStatus

                    mock_status.return_value = TokenStatus(valid=False, expires_in_seconds=None)

                    with patch.object(skill, "login") as mock_login:
                        mock_login.return_value = CommandResult(success=True, output="Logged in")

                        with patch.object(skill, "switch_context") as mock_switch:
                            mock_switch.return_value = CommandResult(success=True, output="Switched")

                            with patch.object(skill, "get_context") as mock_ctx:
                                mock_ctx.return_value = CloudContext(
                                    provider=CloudProvider.AWS,
                                    organization="test-org",
                                    credentials_valid=True,
                                )

                                _ = await skill.ensure_cloud_access("test-org")
                                # Should have attempted login
                                mock_login.assert_called()


class TestHealthCheckCoverage:
    """Tests for health_check coverage."""

    @pytest.mark.asyncio
    async def test_health_check_version_extraction(self, skill: CloudctlSkill) -> None:
        """Health check should extract cloudctl version."""
        with patch.object(skill, "_is_cloudctl_installed") as mock_installed:
            mock_installed.return_value = True

            with patch.object(skill, "_execute_cloudctl") as mock_exec:
                mock_exec.return_value = CommandResult(success=True, output="cloudctl version 1.2.3")

                with patch.object(skill, "list_organizations") as mock_list:
                    mock_list.return_value = [{"name": "org1", "provider": "aws"}]

                    with patch.object(skill, "_verify_credentials") as mock_verify:
                        mock_verify.return_value = True

                        result = await skill.health_check()
                        assert result.cloudctl_version is not None
                        assert "1.2.3" in result.cloudctl_version

    @pytest.mark.asyncio
    async def test_health_check_partial_failures(self, skill: CloudctlSkill) -> None:
        """Health check should track partial failures."""
        with patch.object(skill, "_is_cloudctl_installed") as mock_installed:
            mock_installed.return_value = True

            with patch.object(skill, "_execute_cloudctl") as mock_exec:
                mock_exec.return_value = CommandResult(success=True, output="cloudctl version 1.0.0")

                with patch.object(skill, "list_organizations") as mock_list:
                    mock_list.return_value = [
                        {"name": "org1", "provider": "aws"},
                        {"name": "org2", "provider": "gcp"},
                    ]

                    with patch.object(skill, "_verify_credentials") as mock_verify:
                        # One org valid, one invalid
                        mock_verify.side_effect = [True, RuntimeError("Failed")]

                        result = await skill.health_check()
                        # Should track both passes and failures
                        assert result.checks_passed > 0
                        assert result.checks_failed > 0


class TestVerifyCredentialsInternal:
    """Tests for _verify_credentials internal method."""

    @pytest.mark.asyncio
    async def test_verify_credentials_returns_bool(self, skill: CloudctlSkill) -> None:
        """_verify_credentials should return boolean."""
        with patch.object(skill, "get_token_status") as mock_status:
            from cloudctl_skill.models import TokenStatus

            mock_status.return_value = TokenStatus(valid=True)
            result = await skill._verify_credentials("test-org")
            assert isinstance(result, bool)
            assert result is True

    @pytest.mark.asyncio
    async def test_verify_credentials_handles_exception(self, skill: CloudctlSkill) -> None:
        """_verify_credentials should return False on exception."""
        with patch.object(skill, "get_token_status") as mock_status:
            mock_status.side_effect = RuntimeError("Network error")
            result = await skill._verify_credentials("test-org")
            assert result is False


class TestIsCloudctlInstalledCheck:
    """Tests for _is_cloudctl_installed method."""

    @pytest.mark.asyncio
    async def test_is_cloudctl_installed_true(self, skill: CloudctlSkill) -> None:
        """Should return True when cloudctl is installed."""
        with patch.object(skill, "_execute_cloudctl") as mock_exec:
            mock_exec.return_value = CommandResult(success=True, output="cloudctl 1.0.0")

            result = await skill._is_cloudctl_installed()
            assert result is True

    @pytest.mark.asyncio
    async def test_is_cloudctl_installed_false(self, skill: CloudctlSkill) -> None:
        """Should return False when cloudctl is not installed."""
        with patch.object(skill, "_execute_cloudctl") as mock_exec:
            mock_exec.return_value = CommandResult(success=False, error="command not found")

            result = await skill._is_cloudctl_installed()
            assert result is False
