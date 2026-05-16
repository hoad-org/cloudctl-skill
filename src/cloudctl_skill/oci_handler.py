"""OCI (Oracle Cloud Infrastructure) handler for CloudctlSkill.

Since the cloudctl binary does not yet support OCI, this module handles
OCI authentication and context management directly via the oci CLI binary.
Zero credentials are stored here — all auth lives in ~/.oci/config.
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

from .models import (
    CloudContext,
    CloudProvider,
    CommandResult,
    CommandStatus,
    TokenStatus,
)

OCI_CONFIG_PATH = Path.home() / ".oci" / "config"
OCI_BIN = "oci"

# Suppress OCI CLI cosmetic key-label warning
os.environ.setdefault("SUPPRESS_LABEL_WARNING", "True")


class OCIHandlerError(Exception):
    """Raised when OCI CLI operations fail."""


def _is_oci_configured() -> bool:
    """Return True if ~/.oci/config exists and is non-empty."""
    return OCI_CONFIG_PATH.exists() and OCI_CONFIG_PATH.stat().st_size > 0


def _read_oci_config(profile: str = "DEFAULT") -> dict[str, str]:
    """Parse ~/.oci/config and return the named profile as a dict."""
    if not _is_oci_configured():
        raise OCIHandlerError("OCI CLI not configured. Run: awsctl oci login")

    cfg: dict[str, str] = {}
    in_section = False
    for line in OCI_CONFIG_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("[") and line.endswith("]"):
            in_section = line[1:-1] == profile
            continue
        if in_section and "=" in line:
            key, _, value = line.partition("=")
            cfg[key.strip()] = value.strip()
    if not cfg:
        raise OCIHandlerError(f"OCI profile '{profile}' not found in ~/.oci/config")
    return cfg


async def _run_oci_async(args: list[str], timeout: int = 30) -> tuple[int, str, str]:
    """Run an oci CLI command asynchronously."""
    cmd = [OCI_BIN] + args
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode or 0, stdout.decode(), stderr.decode()
    except TimeoutError:
        proc.kill()
        return 1, "", "OCI CLI command timed out"


async def get_oci_context(org_name: str, profile: str = "DEFAULT") -> CloudContext:
    """Build a CloudContext for an OCI org by reading ~/.oci/config.

    Args:
        org_name: Name of the OCI organisation (from orgs.yaml).
        profile: OCI CLI profile name (defaults to DEFAULT).

    Returns:
        CloudContext populated from ~/.oci/config.

    Raises:
        OCIHandlerError: If config is missing or auth cannot be verified.
    """
    cfg = _read_oci_config(profile)
    return CloudContext(
        provider=CloudProvider.OCI,
        organization=org_name,
        account_id=cfg.get("tenancy"),
        region=cfg.get("region"),
        role=cfg.get("user"),
        credentials_valid=True,
    )


async def verify_oci_auth(profile: str = "DEFAULT") -> TokenStatus:
    """Verify OCI auth is valid by calling oci iam user get.

    Args:
        profile: OCI CLI profile name.

    Returns:
        TokenStatus indicating validity.
    """
    if not _is_oci_configured():
        return TokenStatus(valid=False)

    try:
        cfg = _read_oci_config(profile)
    except OCIHandlerError:
        return TokenStatus(valid=False)

    user_id = cfg.get("user")
    if not user_id:
        return TokenStatus(valid=False)

    args = ["iam", "user", "get", "--user-id", user_id]
    if profile != "DEFAULT":
        args = ["--profile", profile] + args

    rc, stdout, stderr = await _run_oci_async(args)
    if rc != 0:
        return TokenStatus(valid=False)

    try:
        json.loads(stdout)
        return TokenStatus(valid=True)
    except json.JSONDecodeError:
        return TokenStatus(valid=False)


async def oci_login(org_name: str, profile: str = "DEFAULT") -> CommandResult:
    """Verify OCI auth and return a CommandResult.

    Does NOT launch interactive setup (that's handled by awsctl oci login).
    Just validates the existing configuration is working.

    Args:
        org_name: Organisation name for logging.
        profile: OCI CLI profile name.

    Returns:
        CommandResult with auth status.
    """
    if not _is_oci_configured():
        return CommandResult(
            success=False,
            status=CommandStatus.FAILURE,
            error="OCI CLI not configured.",
            fix="Run: awsctl oci login",
        )

    token_status = await verify_oci_auth(profile)
    if token_status.valid:
        try:
            cfg = _read_oci_config(profile)
        except OCIHandlerError as e:
            return CommandResult(
                success=False,
                status=CommandStatus.FAILURE,
                error=str(e),
                fix="Check ~/.oci/config is valid",
            )
        return CommandResult(
            success=True,
            status=CommandStatus.SUCCESS,
            output=(
                f"OCI auth verified for org '{org_name}'\n"
                f"Region  : {cfg.get('region', 'unknown')}\n"
                f"Tenancy : {cfg.get('tenancy', 'unknown')}"
            ),
        )

    return CommandResult(
        success=False,
        status=CommandStatus.FAILURE,
        error="OCI API key authentication failed.",
        fix="Ensure your API key is uploaded to Oracle Cloud Console and ~/.oci/config is correct. "
        "Run: awsctl oci login",
    )


def is_oci_org(org_config: dict[str, Any]) -> bool:
    """Return True if the org config specifies provider=oci."""
    return str(org_config.get("provider", "")).lower() == "oci"
