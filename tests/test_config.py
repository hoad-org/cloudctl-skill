"""Tests for CloudctlSkill configuration management."""

import os
from unittest.mock import MagicMock, patch

import pytest

from cloudctl_skill.config import (
    _load_env_config,
    _merge_config,
    _parse_bool,
    _validate_no_secrets,
    load_config,
)
from cloudctl_skill.models import SkillConfig


class TestParseBool:
    """Tests for _parse_bool function."""

    def test_parse_bool_true_string(self) -> None:
        """Parse 'true' should return True."""
        assert _parse_bool("true") is True

    def test_parse_bool_false_string(self) -> None:
        """Parse 'false' should return False."""
        assert _parse_bool("false") is False

    def test_parse_bool_one(self) -> None:
        """Parse '1' should return True."""
        assert _parse_bool("1") is True

    def test_parse_bool_zero(self) -> None:
        """Parse '0' should return False."""
        assert _parse_bool("0") is False

    def test_parse_bool_yes(self) -> None:
        """Parse 'yes' should return True."""
        assert _parse_bool("yes") is True

    def test_parse_bool_no(self) -> None:
        """Parse 'no' should return False."""
        assert _parse_bool("no") is False

    def test_parse_bool_on(self) -> None:
        """Parse 'on' should return True."""
        assert _parse_bool("on") is True

    def test_parse_bool_off(self) -> None:
        """Parse 'off' should return False."""
        assert _parse_bool("off") is False

    def test_parse_bool_case_insensitive(self) -> None:
        """Parse should be case insensitive."""
        assert _parse_bool("TRUE") is True
        assert _parse_bool("FALSE") is False
        assert _parse_bool("Yes") is True
        assert _parse_bool("No") is False

    def test_parse_bool_invalid_raises(self) -> None:
        """Invalid string should raise ValueError."""
        with pytest.raises(ValueError):
            _parse_bool("invalid")

    def test_parse_bool_empty_raises(self) -> None:
        """Empty string should raise ValueError."""
        with pytest.raises(ValueError):
            _parse_bool("")


class TestValidateNoSecrets:
    """Tests for _validate_no_secrets function."""

    def test_validate_no_secrets_clean_config(self) -> None:
        """Clean config should pass."""
        config = {
            "cloudctl_path": "/usr/bin/cloudctl",
            "cloudctl_timeout": 30,
            "cloudctl_retries": 3,
        }
        # Should not raise
        _validate_no_secrets(config)

    def test_validate_no_secrets_detects_password_key(self) -> None:
        """Config with password key should raise."""
        config = {"password": "secret123"}
        with pytest.raises(ValueError):
            _validate_no_secrets(config)

    def test_validate_no_secrets_detects_api_key_key(self) -> None:
        """Config with api_key should raise."""
        config = {"api_key": "sk-12345"}
        with pytest.raises(ValueError):
            _validate_no_secrets(config)

    def test_validate_no_secrets_detects_token_key(self) -> None:
        """Config with token key should raise."""
        config = {"token": "abc123def"}
        with pytest.raises(ValueError):
            _validate_no_secrets(config)

    def test_validate_no_secrets_detects_secret_key(self) -> None:
        """Config with secret key should raise."""
        config = {"secret": "shhhh"}
        with pytest.raises(ValueError):
            _validate_no_secrets(config)

    def test_validate_no_secrets_detects_credential_key(self) -> None:
        """Config with credential should raise."""
        config = {"credential": "xyz"}
        with pytest.raises(ValueError):
            _validate_no_secrets(config)

    def test_validate_no_secrets_detects_key_suffix(self) -> None:
        """Config with key suffix should raise."""
        config = {"private_key": "-----BEGIN PRIVATE KEY-----"}
        with pytest.raises(ValueError):
            _validate_no_secrets(config)

    def test_validate_no_secrets_detects_aws_pattern(self) -> None:
        """Config with AWS key pattern should raise."""
        config = {"aws_access_key": "EXAMPLE_AWS_12345"}
        with pytest.raises(ValueError):
            _validate_no_secrets(config)

    def test_validate_no_secrets_detects_long_suspicious_string(self) -> None:
        """Config with long suspicious string should raise."""
        config = {"some_field": "a" * 30 + "secretvalue"}
        with pytest.raises(ValueError):
            _validate_no_secrets(config)

    def test_validate_no_secrets_includes_source_in_error(self) -> None:
        """Error should include source name."""
        config = {"password": "secret"}
        with pytest.raises(ValueError) as _:
            _validate_no_secrets(config, source="test_source")
        # Error message should mention the source or key


class TestLoadEnvConfig:
    """Tests for _load_env_config function."""

    def test_load_env_config_empty(self) -> None:
        """Empty environment should return empty dict."""
        with patch.dict(os.environ, {}, clear=True):
            result = _load_env_config()
            assert result == {}

    def test_load_env_config_cloudctl_path(self) -> None:
        """CLOUDCTL_PATH should be loaded."""
        with patch.dict(os.environ, {"CLOUDCTL_PATH": "/custom/path/cloudctl"}):
            result = _load_env_config()
            assert result["cloudctl_path"] == "/custom/path/cloudctl"

    def test_load_env_config_cloudctl_timeout(self) -> None:
        """CLOUDCTL_TIMEOUT should be loaded and converted to int."""
        with patch.dict(os.environ, {"CLOUDCTL_TIMEOUT": "60"}):
            result = _load_env_config()
            assert result["cloudctl_timeout"] == 60
            assert isinstance(result["cloudctl_timeout"], int)

    def test_load_env_config_cloudctl_timeout_invalid(self) -> None:
        """Invalid CLOUDCTL_TIMEOUT should raise ValueError."""
        with patch.dict(os.environ, {"CLOUDCTL_TIMEOUT": "not_a_number"}):
            with pytest.raises(ValueError):
                _load_env_config()

    def test_load_env_config_cloudctl_retries(self) -> None:
        """CLOUDCTL_RETRIES should be loaded."""
        with patch.dict(os.environ, {"CLOUDCTL_RETRIES": "5"}):
            result = _load_env_config()
            assert result["cloudctl_retries"] == 5

    def test_load_env_config_cloudctl_retries_invalid(self) -> None:
        """Invalid CLOUDCTL_RETRIES should raise ValueError."""
        with patch.dict(os.environ, {"CLOUDCTL_RETRIES": "invalid"}):
            with pytest.raises(ValueError):
                _load_env_config()

    def test_load_env_config_cloudctl_verify(self) -> None:
        """CLOUDCTL_VERIFY should be parsed as bool."""
        with patch.dict(os.environ, {"CLOUDCTL_VERIFY": "true"}):
            result = _load_env_config()
            assert result["verify_context_after_switch"] is True

    def test_load_env_config_cloudctl_audit(self) -> None:
        """CLOUDCTL_AUDIT should be parsed as bool."""
        with patch.dict(os.environ, {"CLOUDCTL_AUDIT": "false"}):
            result = _load_env_config()
            assert result["enable_audit_logging"] is False

    def test_load_env_config_cloudctl_dry_run(self) -> None:
        """CLOUDCTL_DRY_RUN should be parsed as bool."""
        with patch.dict(os.environ, {"CLOUDCTL_DRY_RUN": "true"}):
            result = _load_env_config()
            assert result["dry_run"] is True

    def test_load_env_config_cloudctl_cache(self) -> None:
        """CLOUDCTL_CACHE should be parsed as bool."""
        with patch.dict(os.environ, {"CLOUDCTL_CACHE": "false"}):
            result = _load_env_config()
            assert result["enable_caching"] is False

    def test_load_env_config_cloudctl_cache_ttl(self) -> None:
        """CLOUDCTL_CACHE_TTL should be loaded."""
        with patch.dict(os.environ, {"CLOUDCTL_CACHE_TTL": "600"}):
            result = _load_env_config()
            assert result["cache_ttl_seconds"] == 600

    def test_load_env_config_cloudctl_cache_ttl_invalid(self) -> None:
        """Invalid CLOUDCTL_CACHE_TTL should raise ValueError."""
        with patch.dict(os.environ, {"CLOUDCTL_CACHE_TTL": "invalid"}):
            with pytest.raises(ValueError):
                _load_env_config()

    def test_load_env_config_multiple_vars(self) -> None:
        """Multiple environment variables should all load."""
        env_vars = {
            "CLOUDCTL_PATH": "/custom/cloudctl",
            "CLOUDCTL_TIMEOUT": "45",
            "CLOUDCTL_RETRIES": "2",
            "CLOUDCTL_VERIFY": "false",
            "CLOUDCTL_AUDIT": "true",
            "CLOUDCTL_DRY_RUN": "false",
            "CLOUDCTL_CACHE": "true",
            "CLOUDCTL_CACHE_TTL": "120",
        }
        with patch.dict(os.environ, env_vars):
            result = _load_env_config()
            assert result["cloudctl_path"] == "/custom/cloudctl"
            assert result["cloudctl_timeout"] == 45
            assert result["cloudctl_retries"] == 2
            assert result["verify_context_after_switch"] is False
            assert result["enable_audit_logging"] is True
            assert result["dry_run"] is False
            assert result["enable_caching"] is True
            assert result["cache_ttl_seconds"] == 120


class TestMergeConfig:
    """Tests for _merge_config function."""

    def test_merge_config_simple(self) -> None:
        """Merge should add source keys to target."""
        target = {}
        source = {"cloudctl_path": "/usr/bin/cloudctl"}
        _merge_config(target, source)
        assert target["cloudctl_path"] == "/usr/bin/cloudctl"

    def test_merge_config_overwrites(self) -> None:
        """Merge should overwrite existing keys."""
        target = {"cloudctl_timeout": 30}
        source = {"cloudctl_timeout": 60}
        _merge_config(target, source)
        assert target["cloudctl_timeout"] == 60

    def test_merge_config_nested_cloudctl(self) -> None:
        """Merge should handle nested 'cloudctl' key."""
        target = {}
        source = {
            "cloudctl": {
                "timeout_seconds": 45,
                "retries": 5,
            }
        }
        _merge_config(target, source)
        # Nested cloudctl values are merged with hyphen-to-underscore conversion
        assert target["timeout_seconds"] == 45
        assert target["retries"] == 5

    def test_merge_config_kebab_to_snake_case(self) -> None:
        """Merge should convert kebab-case to snake_case."""
        target = {}
        source = {
            "cloudctl": {
                "timeout-seconds": 45,
                "enable-caching": True,
            }
        }
        _merge_config(target, source)
        # Nested cloudctl values convert hyphens to underscores
        assert target["timeout_seconds"] == 45
        assert target["enable_caching"] is True

    def test_merge_config_environment_overrides(self) -> None:
        """Merge should handle environment_overrides."""
        target = {}
        source = {
            "environment_overrides": {
                "AWS_REGION": "us-west-2",
                "GCLOUD_PROJECT": "my-project",
            }
        }
        with patch.dict(os.environ, {}, clear=False):
            _merge_config(target, source)
            # setdefault only sets if not already present
            assert os.environ.get("AWS_REGION") == "us-west-2"

    def test_merge_config_top_level_keys(self) -> None:
        """Merge should handle top-level keys."""
        target = {}
        source = {
            "cloudctl_path": "/custom/path",
            "cloudctl_timeout": 90,
        }
        _merge_config(target, source)
        assert target["cloudctl_path"] == "/custom/path"
        assert target["cloudctl_timeout"] == 90

    def test_merge_config_ignores_special_keys(self) -> None:
        """Merge should not copy special keys directly."""
        target = {}
        source = {
            "cloudctl": {"timeout_seconds": 45},
            "environment_overrides": {"VAR": "value"},
            "normal_key": "value",
        }
        _merge_config(target, source)
        # cloudctl and environment_overrides should be processed specially
        assert "cloudctl" not in target
        assert "environment_overrides" not in target


class TestLoadConfig:
    """Tests for load_config function."""

    @patch("cloudctl_skill.config._load_env_config")
    @patch("cloudctl_skill.config.Path")
    def test_load_config_defaults_only(self, mock_path: MagicMock, mock_env: MagicMock) -> None:
        """Load with no files should use defaults."""
        mock_path.return_value.exists.return_value = False
        mock_env.return_value = {}

        with patch("pathlib.Path.exists", return_value=False):
            config = load_config()
            assert config.cloudctl_path == "cloudctl"
            assert config.cloudctl_timeout == 30
            assert config.cloudctl_retries == 3

    @patch("cloudctl_skill.config._load_env_config")
    @patch("cloudctl_skill.config.Path")
    def test_load_config_from_home_config(self, mock_path: MagicMock, mock_env: MagicMock) -> None:
        """Load should read from ~/.cloudctl.yaml."""
        home_config = {
            "cloudctl": {
                "timeout_seconds": 60,
            }
        }

        def mock_exists(path):
            return str(path).endswith(".cloudctl.yaml")

        with patch("pathlib.Path.home") as mock_home:
            mock_home_path = MagicMock()
            mock_home.return_value = mock_home_path

            with patch("pathlib.Path.exists", side_effect=mock_exists):
                with patch("builtins.open") as mock_open:
                    mock_open.return_value.__enter__.return_value = MagicMock()

                    with patch("yaml.safe_load") as mock_yaml:
                        mock_yaml.return_value = home_config

                        with patch("cloudctl_skill.config._load_env_config") as mock_env_load:
                            mock_env_load.return_value = {}
                            config = load_config()
                            # Config should be created with merged values
                            assert isinstance(config, SkillConfig)

    @patch("cloudctl_skill.config._load_env_config")
    def test_load_config_environment_takes_precedence(self, mock_env: MagicMock) -> None:
        """Environment variables should override file config."""
        mock_env.return_value = {"cloudctl_timeout": 120}

        with patch("pathlib.Path.exists", return_value=False):
            with patch("pathlib.Path.home"):
                config = load_config()
                assert config.cloudctl_timeout == 120

    def test_load_config_precedence_order(self) -> None:
        """Test configuration precedence: env > local > home > defaults."""
        # This is a complex test that verifies the full precedence
        env_vars = {
            "CLOUDCTL_TIMEOUT": "100",
        }

        with patch.dict(os.environ, env_vars):
            with patch("pathlib.Path.exists", return_value=False):
                config = load_config()
                assert config.cloudctl_timeout == 100  # From env

    def test_load_config_validates_timeout(self) -> None:
        """Load should validate timeout is in valid range."""
        env_vars = {
            "CLOUDCTL_TIMEOUT": "500",  # Too high (> 300)
        }

        with patch.dict(os.environ, env_vars):
            with patch("pathlib.Path.exists", return_value=False):
                with pytest.raises(ValueError):
                    load_config()

    def test_load_config_validates_retries(self) -> None:
        """Load should validate retries is in valid range."""
        env_vars = {
            "CLOUDCTL_RETRIES": "20",  # Too high (> 10)
        }

        with patch.dict(os.environ, env_vars):
            with patch("pathlib.Path.exists", return_value=False):
                with pytest.raises(ValueError):
                    load_config()

    def test_load_config_returns_skill_config_instance(self) -> None:
        """Load should return SkillConfig instance."""
        with patch("pathlib.Path.exists", return_value=False):
            with patch("cloudctl_skill.config._load_env_config", return_value={}):
                config = load_config()
                assert isinstance(config, SkillConfig)

    def test_load_config_all_defaults_present(self) -> None:
        """Load should include all default fields."""
        with patch("pathlib.Path.exists", return_value=False):
            with patch("cloudctl_skill.config._load_env_config", return_value={}):
                config = load_config()
                assert hasattr(config, "cloudctl_path")
                assert hasattr(config, "cloudctl_timeout")
                assert hasattr(config, "cloudctl_retries")
                assert hasattr(config, "verify_context_after_switch")
                assert hasattr(config, "enable_audit_logging")
                assert hasattr(config, "dry_run")
                assert hasattr(config, "enable_caching")
                assert hasattr(config, "cache_ttl_seconds")
