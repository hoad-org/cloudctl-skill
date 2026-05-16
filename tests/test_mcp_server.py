"""Tests for CloudctlSkill MCP server."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

# Import the MCP module to test the functions
from cloudctl_skill import mcp as mcp_module


class TestMCPToolFunctions:
    """Tests for individual MCP tool functions."""

    @patch("cloudctl_skill.mcp.CloudctlSkill")
    def test_cloudctl_context_success(self, mock_skill_class: MagicMock) -> None:
        """context tool should return cloud context."""
        mock_instance = MagicMock()
        mock_instance.get_context = AsyncMock(return_value={"provider": "aws", "organization": "test-org"})
        mock_skill_class.return_value = mock_instance

        result = mcp_module.cloudctl_context()
        assert isinstance(result, str)
        assert "aws" in result.lower() or "test-org" in result.lower()

    @patch("cloudctl_skill.mcp.CloudctlSkill")
    def test_cloudctl_context_error(self, mock_skill_class: MagicMock) -> None:
        """context tool should handle errors gracefully."""
        mock_instance = MagicMock()
        mock_instance.get_context = AsyncMock(side_effect=Exception("Test error"))
        mock_skill_class.return_value = mock_instance

        result = mcp_module.cloudctl_context()
        assert "Error" in result or "error" in result

    @patch("cloudctl_skill.mcp.CloudctlSkill")
    def test_cloudctl_list_orgs_success(self, mock_skill_class: MagicMock) -> None:
        """list_orgs tool should return organizations."""
        mock_instance = MagicMock()
        mock_instance.list_organizations = AsyncMock(return_value=[{"name": "org1", "provider": "aws"}])
        mock_skill_class.return_value = mock_instance

        result = mcp_module.cloudctl_list_orgs()
        assert isinstance(result, str)
        # Should be valid JSON
        json.loads(result)

    @patch("cloudctl_skill.mcp.CloudctlSkill")
    def test_cloudctl_switch_success(self, mock_skill_class: MagicMock) -> None:
        """switch tool should handle context switching."""
        mock_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.model_dump = MagicMock(return_value={"provider": "aws", "organization": "new-org"})
        mock_instance.switch_context = AsyncMock(return_value=mock_result)
        mock_skill_class.return_value = mock_instance

        result = mcp_module.cloudctl_switch("new-org")
        assert isinstance(result, str)
        # Should be valid JSON
        json.loads(result)

    @patch("cloudctl_skill.mcp.CloudctlSkill")
    def test_cloudctl_health_success(self, mock_skill_class: MagicMock) -> None:
        """health tool should run diagnostics."""
        mock_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.model_dump = MagicMock(return_value={"status": "healthy", "errors": []})
        mock_instance.health_check = AsyncMock(return_value=mock_result)
        mock_skill_class.return_value = mock_instance

        result = mcp_module.cloudctl_health()
        assert isinstance(result, str)
        # Should be valid JSON
        json.loads(result)

    @patch("cloudctl_skill.mcp.CloudctlSkill")
    def test_cloudctl_check_credentials_success(self, mock_skill_class: MagicMock) -> None:
        """check_credentials tool should verify credentials."""
        mock_instance = MagicMock()
        mock_instance.check_all_credentials = AsyncMock(return_value={"org1": True, "org2": False})
        mock_skill_class.return_value = mock_instance

        result = mcp_module.cloudctl_check_credentials()
        assert isinstance(result, str)
        # Should be valid JSON
        json.loads(result)

    @patch("cloudctl_skill.mcp.CloudctlSkill")
    def test_cloudctl_token_status_success(self, mock_skill_class: MagicMock) -> None:
        """token_status tool should get token info."""
        mock_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.model_dump = MagicMock(return_value={"valid": True, "expires_in_seconds": 3600})
        mock_instance.get_token_status = AsyncMock(return_value=mock_result)
        mock_skill_class.return_value = mock_instance

        result = mcp_module.cloudctl_token_status("test-org")
        assert isinstance(result, str)
        # Should be valid JSON
        json.loads(result)

    @patch("cloudctl_skill.mcp.CloudctlSkill")
    def test_cloudctl_verify_credentials_success(self, mock_skill_class: MagicMock) -> None:
        """verify_credentials tool should test access."""
        mock_instance = MagicMock()
        mock_instance.verify_credentials = AsyncMock(return_value=True)
        mock_skill_class.return_value = mock_instance

        result = mcp_module.cloudctl_verify_credentials("test-org")
        assert isinstance(result, str)
        # Should be valid JSON
        json.loads(result)
        assert "true" in result.lower()

    @patch("cloudctl_skill.mcp.CloudctlSkill")
    def test_cloudctl_switch_region_success(self, mock_skill_class: MagicMock) -> None:
        """switch_region tool should change AWS region."""
        mock_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.model_dump = MagicMock(return_value={"region": "us-east-1"})
        mock_instance.switch_region = AsyncMock(return_value=mock_result)
        mock_skill_class.return_value = mock_instance

        result = mcp_module.cloudctl_switch_region("us-east-1")
        assert isinstance(result, str)
        # Should be valid JSON
        json.loads(result)

    @patch("cloudctl_skill.mcp.CloudctlSkill")
    def test_cloudctl_switch_project_success(self, mock_skill_class: MagicMock) -> None:
        """switch_project tool should change GCP project."""
        mock_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.model_dump = MagicMock(return_value={"project": "test-project"})
        mock_instance.switch_project = AsyncMock(return_value=mock_result)
        mock_skill_class.return_value = mock_instance

        result = mcp_module.cloudctl_switch_project("test-project")
        assert isinstance(result, str)
        # Should be valid JSON
        json.loads(result)

    @patch("cloudctl_skill.mcp.CloudctlSkill")
    def test_cloudctl_ensure_access_success(self, mock_skill_class: MagicMock) -> None:
        """ensure_access tool should verify organization access."""
        mock_instance = MagicMock()
        mock_instance.ensure_cloud_access = AsyncMock(return_value={"access": True})
        mock_skill_class.return_value = mock_instance

        result = mcp_module.cloudctl_ensure_access("test-org")
        assert isinstance(result, str)
        # Should be valid JSON
        json.loads(result)

    @patch("cloudctl_skill.mcp.CloudctlSkill")
    def test_cloudctl_validate_switch_success(self, mock_skill_class: MagicMock) -> None:
        """validate_switch tool should check last switch."""
        mock_instance = MagicMock()
        mock_instance.validate_switch = AsyncMock(return_value={"valid": True})
        mock_skill_class.return_value = mock_instance

        result = mcp_module.cloudctl_validate_switch()
        assert isinstance(result, str)
        # Should be valid JSON
        json.loads(result)

    @patch("cloudctl_skill.mcp.CloudctlSkill")
    def test_cloudctl_login_success(self, mock_skill_class: MagicMock) -> None:
        """login tool should start SSO login."""
        mock_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.model_dump = MagicMock(return_value={"logged_in": True})
        mock_instance.login = AsyncMock(return_value=mock_result)
        mock_skill_class.return_value = mock_instance

        result = mcp_module.cloudctl_login("test-org")
        assert isinstance(result, str)
        # Should be valid JSON
        json.loads(result)


class TestMCPServer:
    """Tests for MCP server configuration."""

    def test_mcp_server_exists(self) -> None:
        """MCP server should be initialized."""
        assert mcp_module.mcp is not None
        assert hasattr(mcp_module.mcp, "run")

    def test_mcp_server_name(self) -> None:
        """MCP server should have correct name."""
        assert mcp_module.mcp.name == "cloudctl-skill"

    def test_serve_function_exists(self) -> None:
        """Serve function should exist."""
        assert hasattr(mcp_module, "serve")
        assert callable(mcp_module.serve)


class TestMCPToolAttributes:
    """Tests that MCP tools have proper attributes."""

    def test_all_tools_have_docstrings(self) -> None:
        """All MCP tools should have docstrings."""
        tool_functions = [
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
        for func in tool_functions:
            assert func.__doc__ is not None
            assert len(func.__doc__) > 0
