"""Utility functions for CloudctlSkill."""

import asyncio
from pathlib import Path

from .models import OperationLog


def setup_audit_logging() -> Path | None:
    """Setup audit logging directory.

    Creates ~/.config/cloudctl/audit/ if it doesn't exist.

    Returns:
        Path to audit directory, or None if setup failed
    """
    try:
        audit_dir = Path.home() / ".config" / "cloudctl" / "audit"
        audit_dir.mkdir(parents=True, exist_ok=True)
        return audit_dir
    except Exception as e:
        print(f"Warning: Failed to setup audit logging: {e}")
        return None


async def write_audit_log(audit_dir: Path, log: OperationLog) -> None:
    """Write operation log to audit file.

    Writes to ~/.config/cloudctl/audit/operations_YYYYMMDD.jsonl

    Args:
        audit_dir: Path to audit directory
        log: OperationLog to write
    """
    try:
        # Determine log file based on date
        date_str = log.timestamp.strftime("%Y%m%d")
        log_file = audit_dir / f"operations_{date_str}.jsonl"

        # Write log entry (run in executor to avoid blocking)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _write_log_sync, log_file, log)

    except Exception as e:
        print(f"Warning: Failed to write audit log: {e}")


def _write_log_sync(log_file: Path, log: OperationLog) -> None:
    """Synchronous write of log entry.

    Args:
        log_file: Path to log file
        log: OperationLog to write
    """
    try:
        with open(log_file, "a") as f:
            f.write(log.to_jsonl())
            f.write("\n")
    except Exception as e:
        raise RuntimeError(f"Failed to write audit log: {e}") from e


def format_context_string(provider: str, organization: str, **kwargs: str) -> str:
    """Format a context string for display.

    Args:
        provider: Cloud provider name
        organization: Organization name
        **kwargs: Additional context fields (account, region, role, etc.)

    Returns:
        Formatted context string
    """
    parts = [f"{provider}:{organization}"]

    # Order: account, role, region
    for key in ["account", "role", "region"]:
        if key in kwargs and kwargs[key]:
            parts.append(f"{key}={kwargs[key]}")

    return " ".join(parts)


def parse_context_string(context_str: str) -> dict[str, str]:
    """Parse a context string into components.

    Args:
        context_str: Context string (e.g., "aws:myorg account=123")

    Returns:
        Dict with provider, organization, and additional fields

    Raises:
        ValueError: If context string is invalid
    """
    parts = context_str.split()
    if not parts:
        raise ValueError("Empty context string")

    # Parse provider:organization
    provider_org = parts[0]
    if ":" not in provider_org:
        raise ValueError(f"Invalid context format: {provider_org}")

    provider, organization = provider_org.split(":", 1)

    result = {"provider": provider, "organization": organization}

    # Parse optional fields
    for part in parts[1:]:
        if "=" in part:
            key, value = part.split("=", 1)
            result[key] = value

    return result
