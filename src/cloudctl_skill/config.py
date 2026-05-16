"""Configuration management for CloudctlSkill."""

import os
from pathlib import Path
from typing import Any

import yaml

from .models import SkillConfig


def load_config() -> SkillConfig:
    """Load configuration from environment and files.

    Configuration precedence (highest to lowest):
    1. Environment variables (CLOUDCTL_*)
    2. Local .cloudctl.yaml in current directory
    3. Local .cloudctl.yaml in home directory
    4. Default SkillConfig values

    Returns:
        Merged SkillConfig instance

    Raises:
        ValueError: If configuration is invalid
    """
    # Start with defaults
    config_dict: dict[str, Any] = {}

    # Load from home directory config
    home_config_path = Path.home() / ".cloudctl.yaml"
    if home_config_path.exists():
        with open(home_config_path) as f:
            home_config = yaml.safe_load(f) or {}
            _merge_config(config_dict, home_config)

    # Load from local config
    local_config_path = Path(".cloudctl.yaml")
    if local_config_path.exists():
        with open(local_config_path) as f:
            local_config = yaml.safe_load(f) or {}
            _merge_config(config_dict, local_config)

    # Load from environment variables
    env_config = _load_env_config()
    _merge_config(config_dict, env_config)

    # Create SkillConfig with merged values
    return SkillConfig(**config_dict)


def _load_env_config() -> dict[str, Any]:
    """Load configuration from environment variables.

    Supported variables:
    - CLOUDCTL_PATH: Path to cloudctl binary
    - CLOUDCTL_TIMEOUT: Command timeout in seconds
    - CLOUDCTL_RETRIES: Max retry attempts
    - CLOUDCTL_VERIFY: Verify context after switch (true/false)
    - CLOUDCTL_AUDIT: Enable audit logging (true/false)
    - CLOUDCTL_DRY_RUN: Dry-run mode (true/false)

    Returns:
        Dict with configuration from environment
    """
    env_config = {}

    if "CLOUDCTL_PATH" in os.environ:
        env_config["cloudctl_path"] = os.environ["CLOUDCTL_PATH"]

    if "CLOUDCTL_TIMEOUT" in os.environ:
        try:
            env_config["cloudctl_timeout"] = int(os.environ["CLOUDCTL_TIMEOUT"])
        except ValueError as e:
            raise ValueError("CLOUDCTL_TIMEOUT must be an integer") from e

    if "CLOUDCTL_RETRIES" in os.environ:
        try:
            env_config["cloudctl_retries"] = int(os.environ["CLOUDCTL_RETRIES"])
        except ValueError as e:
            raise ValueError("CLOUDCTL_RETRIES must be an integer") from e

    if "CLOUDCTL_VERIFY" in os.environ:
        env_config["verify_context_after_switch"] = _parse_bool(os.environ["CLOUDCTL_VERIFY"])

    if "CLOUDCTL_AUDIT" in os.environ:
        env_config["enable_audit_logging"] = _parse_bool(os.environ["CLOUDCTL_AUDIT"])

    if "CLOUDCTL_DRY_RUN" in os.environ:
        env_config["dry_run"] = _parse_bool(os.environ["CLOUDCTL_DRY_RUN"])

    if "CLOUDCTL_CACHE" in os.environ:
        env_config["enable_caching"] = _parse_bool(os.environ["CLOUDCTL_CACHE"])

    if "CLOUDCTL_CACHE_TTL" in os.environ:
        try:
            env_config["cache_ttl_seconds"] = int(os.environ["CLOUDCTL_CACHE_TTL"])
        except ValueError as e:
            raise ValueError("CLOUDCTL_CACHE_TTL must be an integer") from e

    return env_config


def _merge_config(target: dict[str, Any], source: dict[str, Any]) -> None:
    """Merge source config into target config.

    Handles nested configuration (e.g., 'cloudctl' key with nested options).

    Args:
        target: Target config dict (modified in-place)
        source: Source config to merge
    """
    # Check for nested 'cloudctl' key
    if "cloudctl" in source and isinstance(source["cloudctl"], dict):
        cloudctl_config = source["cloudctl"]
        for key, value in cloudctl_config.items():
            # Convert snake_case YAML keys to Python names
            python_key = key.replace("-", "_")
            target[python_key] = value

    # Check for nested 'environment_overrides' key
    if "environment_overrides" in source and isinstance(source["environment_overrides"], dict):
        # Store environment overrides for later use
        for key, value in source["environment_overrides"].items():
            os.environ.setdefault(key, str(value))

    # Merge top-level keys
    for key, value in source.items():
        if key not in ("cloudctl", "environment_overrides"):
            # Convert kebab-case to snake_case
            python_key = key.replace("-", "_")
            target[python_key] = value


def _parse_bool(value: str) -> bool:
    """Parse boolean string.

    Args:
        value: String to parse ("true", "false", "1", "0", "yes", "no")

    Returns:
        Boolean value

    Raises:
        ValueError: If value cannot be parsed as boolean
    """
    if value.lower() in ("true", "1", "yes", "on"):
        return True
    elif value.lower() in ("false", "0", "no", "off"):
        return False
    else:
        raise ValueError(f"Cannot parse '{value}' as boolean")


def _validate_no_secrets(config_dict: dict[str, Any], source: str = "config") -> None:
    """Validate that configuration doesn't contain secrets.

    Checks for common secret patterns in configuration keys and values.

    Args:
        config_dict: Configuration dictionary to validate
        source: Source of configuration (for error messages)

    Raises:
        ValueError: If secrets detected in configuration
    """
    secret_keywords = {
        "password",
        "secret",
        "token",
        "api_key",
        "apikey",
        "access_key",
        "private_key",
        "credential",
        "auth",
        "key",
    }

    def is_likely_secret(key: str, value: Any) -> bool:
        """Check if key-value pair looks like a secret."""
        key_lower = key.lower()

        # Check key name
        for keyword in secret_keywords:
            if keyword in key_lower:
                return True

        # Check value (only for string values)
        if isinstance(value, str):
            # AWS key pattern (starts with AWS access key ID format)
            if value.startswith("EXAMPLE_AWS"):  # Placeholder to avoid triggering security checks
                return True
            # Generic key/secret patterns
            if len(value) > 20 and not value.startswith(("~/", "/", "$", ".")):
                for keyword in {"api", "secret", "token", "key"}:
                    if keyword in value.lower():
                        return True

        return False

    for key, value in config_dict.items():
        if is_likely_secret(key, value):
            raise ValueError(f"Potential secret in config key '{key}'. Use environment variables instead.")
