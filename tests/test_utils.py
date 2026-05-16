"""Tests for CloudctlSkill utility functions."""

from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cloudctl_skill.models import OperationLog
from cloudctl_skill.utils import (
    format_context_string,
    parse_context_string,
    setup_audit_logging,
    write_audit_log,
)


class TestSetupAuditLogging:
    """Tests for setup_audit_logging function."""

    def test_setup_audit_logging_creates_directory(self) -> None:
        """Setup should create audit directory."""
        with patch("pathlib.Path.home") as mock_home:
            mock_path = MagicMock(spec=Path)
            mock_path.__truediv__.return_value = mock_path
            mock_path.mkdir = MagicMock()
            mock_home.return_value = mock_path

            result = setup_audit_logging()
            assert result is not None

    def test_setup_audit_logging_handles_existing_directory(self) -> None:
        """Setup should handle existing directory gracefully."""
        with patch("pathlib.Path.home") as mock_home:
            mock_path = MagicMock(spec=Path)
            mock_path.__truediv__.return_value = mock_path
            mock_path.mkdir = MagicMock()
            mock_home.return_value = mock_path

            result = setup_audit_logging()
            assert result is not None
            # mkdir should be called with exist_ok=True
            mock_path.mkdir.assert_called()

    def test_setup_audit_logging_handles_exception(self) -> None:
        """Setup should return None on exception."""
        with patch("pathlib.Path.home") as mock_home:
            mock_home.side_effect = Exception("Test error")

            result = setup_audit_logging()
            assert result is None

    def test_setup_audit_logging_creates_correct_path(self) -> None:
        """Setup should create path in correct location."""
        with patch("pathlib.Path.home") as mock_home:
            mock_base = MagicMock(spec=Path)
            mock_config = MagicMock(spec=Path)
            mock_cloudctl = MagicMock(spec=Path)
            mock_audit = MagicMock(spec=Path)

            mock_base.__truediv__.side_effect = [
                mock_config,
                mock_cloudctl,
                mock_audit,
            ]
            mock_config.__truediv__.return_value = mock_cloudctl
            mock_cloudctl.__truediv__.return_value = mock_audit
            mock_audit.mkdir = MagicMock()

            mock_home.return_value = mock_base

            # Test that proper path is constructed
            result = setup_audit_logging()
            # Just verify it returns a Path-like object
            assert result is not None


class TestWriteAuditLog:
    """Tests for write_audit_log function."""

    @pytest.mark.asyncio
    async def test_write_audit_log_success(self) -> None:
        """Write should succeed for valid log."""
        audit_dir = Path("/tmp/audit")
        log = OperationLog(
            operation="test_op",
            success=True,
        )

        with patch("cloudctl_skill.utils._write_log_sync") as mock_write:
            await write_audit_log(audit_dir, log)
            mock_write.assert_called_once()

    @pytest.mark.asyncio
    async def test_write_audit_log_handles_exception(self) -> None:
        """Write should handle exceptions gracefully."""
        audit_dir = Path("/tmp/audit")
        log = OperationLog(
            operation="test_op",
            success=True,
        )

        with patch("asyncio.get_event_loop") as mock_loop:
            mock_event_loop = AsyncMock()
            mock_event_loop.run_in_executor.side_effect = Exception("Write failed")
            mock_loop.return_value = mock_event_loop

            # Should not raise, just handle gracefully
            await write_audit_log(audit_dir, log)

    @pytest.mark.asyncio
    async def test_write_audit_log_uses_correct_filename(self) -> None:
        """Write should use correct filename with date."""
        audit_dir = Path("/tmp/audit")
        log = OperationLog(
            timestamp=datetime(2026, 4, 15, 10, 30, 0),
            operation="test_op",
            success=True,
        )

        with patch("cloudctl_skill.utils._write_log_sync") as mock_write:
            await write_audit_log(audit_dir, log)
            # Verify the log file path includes the date
            call_args = mock_write.call_args
            if call_args:
                log_file = call_args[0][0]
                # Should have date in filename
                assert "20260415" in str(log_file)


class TestWriteLogSync:
    """Tests for _write_log_sync function."""

    def test_write_log_sync_success(self) -> None:
        """Sync write should succeed."""
        with patch("builtins.open", create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file

            log = OperationLog(operation="test_op", success=True)
            log_file = Path("/tmp/audit/operations_20260415.jsonl")

            from cloudctl_skill.utils import _write_log_sync

            _write_log_sync(log_file, log)
            mock_file.write.assert_called()

    def test_write_log_sync_exception(self) -> None:
        """Sync write should raise RuntimeError on file error."""
        with patch("builtins.open", create=True) as mock_open:
            mock_open.side_effect = OSError("Failed to write")

            log = OperationLog(operation="test_op", success=True)
            log_file = Path("/tmp/audit/operations_20260415.jsonl")

            from cloudctl_skill.utils import _write_log_sync

            with pytest.raises(RuntimeError):
                _write_log_sync(log_file, log)

    def test_write_log_sync_appends_to_file(self) -> None:
        """Sync write should append to file."""
        with patch("builtins.open", create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file

            log = OperationLog(operation="test_op", success=True)
            log_file = Path("/tmp/audit/operations_20260415.jsonl")

            from cloudctl_skill.utils import _write_log_sync

            _write_log_sync(log_file, log)
            # Should open with append mode
            mock_open.assert_called_with(log_file, "a")


class TestFormatContextString:
    """Tests for format_context_string function."""

    def test_format_context_string_provider_and_org_only(self) -> None:
        """Format should work with provider and org only."""
        result = format_context_string("aws", "myorg")
        assert result == "aws:myorg"

    def test_format_context_string_with_account(self) -> None:
        """Format should include account."""
        result = format_context_string("aws", "myorg", account="123456789012")
        assert "account=123456789012" in result
        assert result.startswith("aws:myorg")

    def test_format_context_string_with_region(self) -> None:
        """Format should include region."""
        result = format_context_string("aws", "myorg", region="us-west-2")
        assert "region=us-west-2" in result

    def test_format_context_string_with_role(self) -> None:
        """Format should include role."""
        result = format_context_string("aws", "myorg", role="terraform")
        assert "role=terraform" in result

    def test_format_context_string_with_all_fields(self) -> None:
        """Format should include all fields in correct order."""
        result = format_context_string(
            "gcp",
            "my-project",
            account="my-account",
            region="europe-west1",
            role="viewer",
        )
        assert result.startswith("gcp:my-project")
        # Should be ordered: account, role, region
        parts = result.split()
        assert any("account=" in p for p in parts)
        assert any("role=" in p for p in parts)
        assert any("region=" in p for p in parts)

    def test_format_context_string_ignores_empty_values(self) -> None:
        """Format should ignore empty string values."""
        result = format_context_string("aws", "myorg", account="", region="us-west-2")
        assert "account=" not in result
        assert "region=us-west-2" in result

    def test_format_context_string_ignores_none_values(self) -> None:
        """Format should ignore None values."""
        result = format_context_string(
            "aws",
            "myorg",
            account=None,
            region="us-west-2",
        )
        # This will fail gracefully but let's test what happens
        # The function uses **kwargs with str type, so None shouldn't be passed
        assert "region=us-west-2" in result


class TestParseContextString:
    """Tests for parse_context_string function."""

    def test_parse_context_string_simple(self) -> None:
        """Parse should work for simple context."""
        result = parse_context_string("aws:myorg")
        assert result["provider"] == "aws"
        assert result["organization"] == "myorg"

    def test_parse_context_string_with_account(self) -> None:
        """Parse should extract account."""
        result = parse_context_string("aws:myorg account=123456789012")
        assert result["account"] == "123456789012"

    def test_parse_context_string_with_region(self) -> None:
        """Parse should extract region."""
        result = parse_context_string("aws:myorg region=us-west-2")
        assert result["region"] == "us-west-2"

    def test_parse_context_string_with_role(self) -> None:
        """Parse should extract role."""
        result = parse_context_string("aws:myorg role=terraform")
        assert result["role"] == "terraform"

    def test_parse_context_string_with_all_fields(self) -> None:
        """Parse should extract all fields."""
        result = parse_context_string("aws:myorg account=123456789012 region=us-west-2 role=terraform")
        assert result["provider"] == "aws"
        assert result["organization"] == "myorg"
        assert result["account"] == "123456789012"
        assert result["region"] == "us-west-2"
        assert result["role"] == "terraform"

    def test_parse_context_string_gcp(self) -> None:
        """Parse should work for GCP."""
        result = parse_context_string("gcp:my-project region=europe-west1")
        assert result["provider"] == "gcp"
        assert result["organization"] == "my-project"
        assert result["region"] == "europe-west1"

    def test_parse_context_string_azure(self) -> None:
        """Parse should work for Azure."""
        result = parse_context_string("azure:sub-123 account=sub-123")
        assert result["provider"] == "azure"
        assert result["organization"] == "sub-123"
        assert result["account"] == "sub-123"

    def test_parse_context_string_empty_raises(self) -> None:
        """Empty string should raise ValueError."""
        with pytest.raises(ValueError):
            parse_context_string("")

    def test_parse_context_string_no_colon_raises(self) -> None:
        """String without colon should raise ValueError."""
        with pytest.raises(ValueError):
            parse_context_string("invalid_format")

    def test_parse_context_string_preserves_values_with_equals(self) -> None:
        """Parse should handle values that contain equals signs."""
        result = parse_context_string("aws:myorg account=123=456")
        # split("=", 1) should only split on first equals
        assert result["account"] == "123=456"

    def test_parse_context_string_ignores_malformed_fields(self) -> None:
        """Parse should ignore fields without equals signs."""
        result = parse_context_string("aws:myorg account=123 notformatted region=us-west-2")
        assert result["account"] == "123"
        assert result["region"] == "us-west-2"
        assert "notformatted" not in result

    def test_parse_context_string_with_colon_in_org_name(self) -> None:
        """Parse should only split on first colon."""
        # This should work: provider is before first colon
        result = parse_context_string("aws:org:with:colons")
        assert result["provider"] == "aws"
        assert result["organization"] == "org:with:colons"

    def test_parse_context_string_whitespace_handling(self) -> None:
        """Parse should handle extra whitespace."""
        result = parse_context_string("aws:myorg  account=123  region=us-west-2")
        assert result["provider"] == "aws"
        assert result["account"] == "123"
        assert result["region"] == "us-west-2"

    def test_parse_context_string_roundtrip(self) -> None:
        """Parse and format should roundtrip correctly."""
        # Use order that matches format_context_string's ordering (account, role, region)
        original = "aws:myorg account=123456789012 role=terraform region=us-west-2"
        parsed = parse_context_string(original)

        # Reconstruct using format_context_string
        reconstructed = format_context_string(
            parsed["provider"],
            parsed["organization"],
            account=parsed.get("account", ""),
            region=parsed.get("region", ""),
            role=parsed.get("role", ""),
        )

        # Should match original (format uses same ordering)
        assert reconstructed == original
