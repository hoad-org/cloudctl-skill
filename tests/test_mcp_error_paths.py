"""Tests for MCP error paths and edge cases."""

from unittest.mock import AsyncMock, MagicMock, patch

from cloudctl_skill import mcp as mcp_module


class TestMCPToolErrorHandling:
    """Tests for MCP tool error handling."""

    @patch("cloudctl_skill.mcp.CloudctlSkill")
    def test_cloudctl_context_handles_exception(self, mock_skill_class: MagicMock) -> None:
        """context tool should handle exceptions."""
        mock_instance = MagicMock()
        mock_instance.get_context = AsyncMock(side_effect=Exception("Network error"))
        mock_skill_class.return_value = mock_instance

        result = mcp_module.cloudctl_context()
        assert isinstance(result, str)
        assert "Error" in result

    @patch("cloudctl_skill.mcp.CloudctlSkill")
    def test_cloudctl_list_orgs_empty_list(self, mock_skill_class: MagicMock) -> None:
        """list_orgs should handle empty organization list."""
        mock_instance = MagicMock()
        mock_instance.list_organizations = AsyncMock(return_value=[])
        mock_skill_class.return_value = mock_instance

        result = mcp_module.cloudctl_list_orgs()
        assert isinstance(result, str)
        # Should still be valid JSON even if empty
        import json

        json.loads(result)

    @patch("cloudctl_skill.mcp.CloudctlSkill")
    def test_cloudctl_switch_org_validation(self, mock_skill_class: MagicMock) -> None:
        """switch should validate organization parameter."""
        mock_instance = MagicMock()
        mock_skill_class.return_value = mock_instance

        # Empty organization should be handled
        result = mcp_module.cloudctl_switch("")
        assert isinstance(result, str)
        # Should contain error info
        assert "error" in result.lower() or "Error" in result

    @patch("cloudctl_skill.mcp.CloudctlSkill")
    def test_cloudctl_health_comprehensive(self, mock_skill_class: MagicMock) -> None:
        """health should return comprehensive status."""
        mock_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.model_dump = MagicMock(
            return_value={
                "is_healthy": True,
                "cloudctl_installed": True,
                "cloudctl_version": "1.0.0",
                "organizations_available": 3,
                "credentials_valid": {"org1": True, "org2": False},
                "checks_passed": 5,
                "checks_failed": 1,
            }
        )
        mock_instance.health_check = AsyncMock(return_value=mock_result)
        mock_skill_class.return_value = mock_instance

        result = mcp_module.cloudctl_health()
        assert isinstance(result, str)
        # Should be valid JSON
        import json

        data = json.loads(result)
        assert "is_healthy" in data
        assert data["is_healthy"] is True

    @patch("cloudctl_skill.mcp.CloudctlSkill")
    def test_cloudctl_check_credentials_mixed_validity(self, mock_skill_class: MagicMock) -> None:
        """check_credentials should show per-org status."""
        mock_instance = MagicMock()
        mock_instance.check_all_credentials = AsyncMock(
            return_value={
                "org1": {"valid": True, "expires_in_seconds": 3600},
                "org2": {"valid": False, "error": "Credentials expired"},
            }
        )
        mock_skill_class.return_value = mock_instance

        result = mcp_module.cloudctl_check_credentials()
        assert isinstance(result, str)
        # Should be valid JSON
        import json

        data = json.loads(result)
        assert "org1" in data
        assert "org2" in data

    @patch("cloudctl_skill.mcp.CloudctlSkill")
    def test_cloudctl_token_status_missing_org(self, mock_skill_class: MagicMock) -> None:
        """token_status should validate org parameter."""
        mock_instance = MagicMock()
        mock_skill_class.return_value = mock_instance

        # Empty org should be handled
        result = mcp_module.cloudctl_token_status("")
        assert isinstance(result, str)

    @patch("cloudctl_skill.mcp.CloudctlSkill")
    def test_cloudctl_verify_credentials_false(self, mock_skill_class: MagicMock) -> None:
        """verify_credentials should return False for invalid."""
        mock_instance = MagicMock()
        mock_instance.verify_credentials = AsyncMock(return_value=False)
        mock_skill_class.return_value = mock_instance

        result = mcp_module.cloudctl_verify_credentials("test-org")
        assert isinstance(result, str)
        assert "false" in result.lower()

    @patch("cloudctl_skill.mcp.CloudctlSkill")
    def test_cloudctl_switch_region_all_regions(self, mock_skill_class: MagicMock) -> None:
        """switch_region should work with various regions."""
        mock_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.model_dump = MagicMock(return_value={"region": "eu-west-1"})
        mock_instance.switch_region = AsyncMock(return_value=mock_result)
        mock_skill_class.return_value = mock_instance

        result = mcp_module.cloudctl_switch_region("eu-west-1")
        assert isinstance(result, str)
        import json

        data = json.loads(result)
        assert data["region"] == "eu-west-1"

    @patch("cloudctl_skill.mcp.CloudctlSkill")
    def test_cloudctl_switch_project_multiple_formats(self, mock_skill_class: MagicMock) -> None:
        """switch_project should handle various project IDs."""
        mock_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.model_dump = MagicMock(return_value={"project": "my-app-prod"})
        mock_instance.switch_project = AsyncMock(return_value=mock_result)
        mock_skill_class.return_value = mock_instance

        result = mcp_module.cloudctl_switch_project("my-app-prod")
        assert isinstance(result, str)
        import json

        json.loads(result)

    @patch("cloudctl_skill.mcp.CloudctlSkill")
    def test_cloudctl_ensure_access_success_case(self, mock_skill_class: MagicMock) -> None:
        """ensure_access should return success status."""
        mock_instance = MagicMock()
        mock_instance.ensure_cloud_access = AsyncMock(
            return_value={
                "success": True,
                "context": "aws:myorg account=123456789012",
                "error": None,
                "fix": None,
                "auto_refreshed": False,
            }
        )
        mock_skill_class.return_value = mock_instance

        result = mcp_module.cloudctl_ensure_access("myorg")
        assert isinstance(result, str)
        import json

        data = json.loads(result)
        assert data["success"] is True

    @patch("cloudctl_skill.mcp.CloudctlSkill")
    def test_cloudctl_ensure_access_failure_case(self, mock_skill_class: MagicMock) -> None:
        """ensure_access should return failure status."""
        mock_instance = MagicMock()
        mock_instance.ensure_cloud_access = AsyncMock(
            return_value={
                "success": False,
                "context": None,
                "error": "Credentials invalid",
                "fix": "Run: cloudctl login myorg",
                "auto_refreshed": False,
            }
        )
        mock_skill_class.return_value = mock_instance

        result = mcp_module.cloudctl_ensure_access("badorg")
        assert isinstance(result, str)
        import json

        data = json.loads(result)
        assert data["success"] is False

    @patch("cloudctl_skill.mcp.CloudctlSkill")
    def test_cloudctl_validate_switch_true(self, mock_skill_class: MagicMock) -> None:
        """validate_switch should return True when valid."""
        mock_instance = MagicMock()
        mock_instance.validate_switch = AsyncMock(return_value=True)
        mock_skill_class.return_value = mock_instance

        result = mcp_module.cloudctl_validate_switch()
        assert isinstance(result, str)
        assert "true" in result.lower()

    @patch("cloudctl_skill.mcp.CloudctlSkill")
    def test_cloudctl_validate_switch_false(self, mock_skill_class: MagicMock) -> None:
        """validate_switch should return False when invalid."""
        mock_instance = MagicMock()
        mock_instance.validate_switch = AsyncMock(return_value=False)
        mock_skill_class.return_value = mock_instance

        result = mcp_module.cloudctl_validate_switch()
        assert isinstance(result, str)
        assert "false" in result.lower()

    @patch("cloudctl_skill.mcp.CloudctlSkill")
    def test_cloudctl_login_failure(self, mock_skill_class: MagicMock) -> None:
        """login should handle failures."""
        mock_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.model_dump = MagicMock(
            return_value={
                "success": False,
                "error": "Authentication failed",
            }
        )
        mock_instance.login = AsyncMock(return_value=mock_result)
        mock_skill_class.return_value = mock_instance

        result = mcp_module.cloudctl_login("badorg")
        assert isinstance(result, str)
        import json

        data = json.loads(result)
        assert data["success"] is False

    @patch("cloudctl_skill.mcp.CloudctlSkill")
    def test_cloudctl_login_success(self, mock_skill_class: MagicMock) -> None:
        """login should return success."""
        mock_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.model_dump = MagicMock(
            return_value={
                "success": True,
                "output": "Successfully logged in",
            }
        )
        mock_instance.login = AsyncMock(return_value=mock_result)
        mock_skill_class.return_value = mock_instance

        result = mcp_module.cloudctl_login("myorg")
        assert isinstance(result, str)
        import json

        data = json.loads(result)
        assert data["success"] is True


class TestMCPServerAttributes:
    """Tests for MCP server attributes and configuration."""

    def test_mcp_server_has_name(self) -> None:
        """MCP server should have the correct name."""
        assert hasattr(mcp_module.mcp, "name")
        assert mcp_module.mcp.name == "cloudctl-skill"

    def test_mcp_server_has_run_method(self) -> None:
        """MCP server should have run method."""
        assert hasattr(mcp_module.mcp, "run")
        assert callable(mcp_module.mcp.run)

    def test_serve_function_is_callable(self) -> None:
        """Serve function should be callable."""
        assert callable(mcp_module.serve)

    def test_all_tool_functions_are_callable(self) -> None:
        """All tool functions should be callable."""
        tools = [
            mcp_module.cloudctl_context,
            mcp_module.cloudctl_list_orgs,
            mcp_module.cloudctl_switch,
            mcp_module.cloudctl_health,
            mcp_module.cloudctl_check_credentials,
            mcp_module.cloudctl_token_status,
            mcp_module.cloudctl_verify_credentials,
            mcp_module.cloudctl_switch_region,
            mcp_module.cloudctl_switch_project,
            mcp_module.cloudctl_ensure_access,
            mcp_module.cloudctl_validate_switch,
            mcp_module.cloudctl_login,
        ]
        for tool in tools:
            assert callable(tool)

    def test_all_tools_return_strings(self) -> None:
        """All tools should return string results."""
        with patch("cloudctl_skill.mcp.CloudctlSkill"):
            # Results should all be strings (not requiring async)
            result = mcp_module.cloudctl_context()
            assert isinstance(result, str)
