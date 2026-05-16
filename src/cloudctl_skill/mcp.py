"""MCP (Model Context Protocol) server for CloudctlSkill.

This module implements the MCP server protocol, exposing CloudctlSkill
functionality to Claude and other MCP clients via FastMCP.

The server exposes the following tools:
- cloudctl_context: Get current cloud context
- cloudctl_list_orgs: List configured organizations
- cloudctl_switch: Switch to a different organization
- cloudctl_health: Run health diagnostics
- cloudctl_check_credentials: Verify all credentials
- cloudctl_token_status: Get token status for organization
- cloudctl_verify_credentials: Verify access to organization
- cloudctl_switch_region: Switch AWS region
- cloudctl_switch_project: Switch GCP project
- cloudctl_ensure_access: Ensure access with recovery
- cloudctl_validate_switch: Validate last context switch
- cloudctl_login: Initiate SSO login
"""

import json
import logging
import sys

from mcp.server import FastMCP

from cloudctl_skill import CloudctlSkill

# Set up logging (to stderr to not interfere with stdout)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

# Create MCP server using FastMCP
mcp = FastMCP("cloudctl-skill")


@mcp.tool()
async def cloudctl_context() -> str:
    """Get current cloud context.

    Returns the cloud provider, organization, account ID, region, and role.

    Returns:
        Current cloud context details
    """
    try:
        skill = CloudctlSkill()
        result = await skill.get_context()
        return str(result)
    except Exception as e:
        error_msg = f"Error getting context: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg


@mcp.tool()
async def cloudctl_list_orgs() -> str:
    """List all configured organizations.

    Returns:
        JSON array of organizations with their cloud providers
    """
    try:
        skill = CloudctlSkill()
        result = await skill.list_organizations()
        return json.dumps(result, indent=2)
    except Exception as e:
        error_msg = f"Error listing organizations: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg


@mcp.tool()
async def cloudctl_switch(organization: str) -> str:
    """Switch to a different organization.

    Uses the cloudctl binary's SSO mechanism - no manual credential entry needed.

    Args:
        organization: Organization name to switch to

    Returns:
        New context after successful switch
    """
    try:
        skill = CloudctlSkill()
        result = await skill.switch_context(organization)
        return json.dumps(result.model_dump(mode="json"), indent=2)
    except Exception as e:
        error_msg = f"Error switching to {organization}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg


@mcp.tool()
async def cloudctl_health() -> str:
    """Run comprehensive health diagnostics.

    Checks:
    - Is cloudctl installed?
    - How many organizations are configured?
    - Are credentials valid for each organization?
    - Overall system health status

    Returns:
        Health check results with status details
    """
    try:
        skill = CloudctlSkill()
        result = await skill.health_check()
        return json.dumps(result.model_dump(mode="json"), indent=2)
    except Exception as e:
        error_msg = f"Error running health check: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg


@mcp.tool()
async def cloudctl_check_credentials() -> str:
    """Verify all credentials are valid.

    Tests credential validity for all configured organizations.

    Returns:
        Dictionary with credential status for each organization
    """
    try:
        skill = CloudctlSkill()
        result = await skill.check_all_credentials()
        return json.dumps(result, indent=2)
    except Exception as e:
        error_msg = f"Error checking credentials: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg


@mcp.tool()
async def cloudctl_token_status(organization: str) -> str:
    """Get token status for specific organization.

    Args:
        organization: Organization name

    Returns:
        Token validity status with expiration information
    """
    try:
        skill = CloudctlSkill()
        result = await skill.get_token_status(organization)
        return json.dumps(result.model_dump(mode="json"), indent=2)
    except Exception as e:
        error_msg = f"Error getting token status for {organization}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg


@mcp.tool()
async def cloudctl_verify_credentials(organization: str) -> str:
    """Verify access to specific organization.

    Tests that you can authenticate to a specific organization.

    Args:
        organization: Organization name

    Returns:
        true/false for credential validity with error message if failed
    """
    try:
        skill = CloudctlSkill()
        result = await skill.verify_credentials(organization)
        return json.dumps({"valid": result}, indent=2)
    except Exception as e:
        error_msg = f"Error verifying credentials for {organization}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg


@mcp.tool()
async def cloudctl_switch_region(region: str) -> str:
    """Switch AWS region.

    Sets AWS_REGION environment variable for current session.

    Args:
        region: AWS region code (e.g., us-east-1, eu-west-2)

    Returns:
        Confirmation of region switch with new value
    """
    try:
        skill = CloudctlSkill()
        result = await skill.switch_region(region)
        return json.dumps(result.model_dump(mode="json"), indent=2)
    except Exception as e:
        error_msg = f"Error switching to region {region}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg


@mcp.tool()
async def cloudctl_switch_project(project: str) -> str:
    """Switch GCP project.

    Sets GCLOUD_PROJECT and CLOUDSDK_CORE_PROJECT environment variables.

    Args:
        project: GCP project ID

    Returns:
        Confirmation of project switch with new value
    """
    try:
        skill = CloudctlSkill()
        result = await skill.switch_project(project)
        return json.dumps(result.model_dump(mode="json"), indent=2)
    except Exception as e:
        error_msg = f"Error switching to project {project}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg


@mcp.tool()
async def cloudctl_ensure_access(organization: str) -> str:
    """Ensure access to organization with auto-recovery.

    Attempts to ensure you have access to an organization, with automatic
    recovery mechanisms if needed.

    Args:
        organization: Organization name

    Returns:
        Status of access verification with current context and recovery details
    """
    try:
        skill = CloudctlSkill()
        result = await skill.ensure_cloud_access(organization)
        return json.dumps(result, indent=2)
    except Exception as e:
        error_msg = f"Error ensuring access to {organization}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg


@mcp.tool()
async def cloudctl_validate_switch() -> str:
    """Validate context switch operation.

    Confirms that the last context switch was successful.

    Returns:
        Current context after last switch with validation status
    """
    try:
        skill = CloudctlSkill()
        result = await skill.validate_switch()
        return json.dumps(result, indent=2)
    except Exception as e:
        error_msg = f"Error validating switch: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg


@mcp.tool()
async def cloudctl_login(organization: str) -> str:
    """Initiate SSO login for organization.

    Starts the SSO login flow for a specific organization.

    Args:
        organization: Organization name

    Returns:
        Login status with current context after successful login
    """
    try:
        skill = CloudctlSkill()
        result = await skill.login(organization)
        return json.dumps(result.model_dump(mode="json"), indent=2)
    except Exception as e:
        error_msg = f"Error logging in to {organization}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg


def serve() -> None:
    """Run the MCP server."""
    logger.info("CloudctlSkill MCP server starting...")
    mcp.run()


if __name__ == "__main__":
    serve()
