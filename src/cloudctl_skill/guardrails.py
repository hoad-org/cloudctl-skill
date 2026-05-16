"""Safety guardrails for CloudctlSkill.

This module implements confirmation gates and rate limiting for destructive operations.
Provides independent testability following the 3-pillar architecture pattern.
"""

import logging
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple rate limiter for operations.

    Tracks operations per minute to prevent abuse.
    """

    def __init__(self, max_per_minute: int = 10) -> None:
        """Initialize rate limiter.

        Args:
            max_per_minute: Maximum operations allowed per minute
        """
        self.max_per_minute = max_per_minute
        self.operations: list[float] = []

    def check(self, operation_name: str) -> bool:
        """Check if operation is within rate limit.

        Args:
            operation_name: Name of operation (for logging)

        Returns:
            True if operation is allowed, False if rate limited
        """
        now = time.time()
        # Remove operations older than 60 seconds
        self.operations = [op_time for op_time in self.operations if now - op_time < 60]

        if len(self.operations) >= self.max_per_minute:
            logger.warning(
                f"Rate limit exceeded for {operation_name}: " f"{len(self.operations)}/{self.max_per_minute} per minute"
            )
            return False

        self.operations.append(now)
        logger.debug(f"Rate limit check passed for {operation_name}")
        return True

    def reset(self) -> None:
        """Reset rate limiter."""
        self.operations = []


class ConfirmationGate:
    """Gate requiring explicit confirmation for dangerous operations.

    Ensures destructive operations are intentional, not accidental.
    """

    def __init__(self, timeout_seconds: int = 300) -> None:
        """Initialize confirmation gate.

        Args:
            timeout_seconds: Confirmation expires after this duration
        """
        self.timeout_seconds = timeout_seconds
        self.confirmed_operations: dict[str, datetime] = {}

    def requires_confirmation(self, operation_type: str) -> bool:
        """Check if operation type requires confirmation.

        Dangerous operations:
        - Switch context (changes active organization/account)
        - Delete resources
        - Revoke credentials
        - Bulk operations (>10 items)

        Args:
            operation_type: Type of operation

        Returns:
            True if confirmation required
        """
        destructive_ops = {
            "switch_context",
            "delete_resource",
            "revoke_credentials",
            "bulk_modify",
            "logout",
            "reset_credentials",
        }
        return operation_type in destructive_ops

    def request_confirmation(self, operation_id: str, operation_type: str) -> None:
        """Request confirmation for an operation.

        In production with Claude, this would prompt the user.
        Here we track that confirmation was requested.

        Args:
            operation_id: Unique ID for this operation
            operation_type: Type of operation requiring confirmation
        """
        if not self.requires_confirmation(operation_type):
            return

        logger.info(f"Confirmation requested for {operation_type} (ID: {operation_id})")

    def confirm(self, operation_id: str) -> bool:
        """Confirm a pending operation.

        Args:
            operation_id: ID of operation to confirm

        Returns:
            True if confirmation successful
        """
        self.confirmed_operations[operation_id] = datetime.now()
        logger.info(f"Operation {operation_id} confirmed")
        return True

    def is_confirmed(self, operation_id: str) -> bool:
        """Check if operation has valid confirmation.

        Confirmation expires after timeout_seconds.

        Args:
            operation_id: ID of operation to check

        Returns:
            True if operation is confirmed and not expired
        """
        if operation_id not in self.confirmed_operations:
            logger.warning(f"Operation {operation_id} has no confirmation")
            return False

        confirmed_at = self.confirmed_operations[operation_id]
        age = datetime.now() - confirmed_at

        if age > timedelta(seconds=self.timeout_seconds):
            logger.warning(f"Confirmation for {operation_id} expired")
            del self.confirmed_operations[operation_id]
            return False

        return True

    def clear(self, operation_id: str | None = None) -> None:
        """Clear confirmation(s).

        Args:
            operation_id: If provided, clear specific operation; otherwise clear all
        """
        if operation_id:
            self.confirmed_operations.pop(operation_id, None)
        else:
            self.confirmed_operations.clear()


class Guardrails:
    """Master guardrails coordinator.

    Combines rate limiting and confirmation gates for comprehensive safety.
    Independent component testable without CLI or config layers.
    """

    def __init__(self, max_rate_per_minute: int = 10, confirmation_timeout: int = 300) -> None:
        """Initialize guardrails.

        Args:
            max_rate_per_minute: Max operations per minute
            confirmation_timeout: Confirmation timeout in seconds
        """
        self.rate_limiter = RateLimiter(max_per_minute=max_rate_per_minute)
        self.confirmation_gate = ConfirmationGate(timeout_seconds=confirmation_timeout)

    def check_operation(self, operation_id: str, operation_type: str, user_confirmed: bool = False) -> tuple[bool, str]:
        """Check if operation is allowed.

        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        # Check rate limit first
        if not self.rate_limiter.check(operation_type):
            return False, "Rate limit exceeded. Please wait before retrying."

        # Check confirmation requirement
        if self.confirmation_gate.requires_confirmation(operation_type):
            if not user_confirmed:
                return False, f"Confirmation required for {operation_type}"
            if not self.confirmation_gate.is_confirmed(operation_id):
                return False, "Confirmation expired or not found"

        return True, "Operation allowed"

    def reset(self) -> None:
        """Reset all guardrails."""
        self.rate_limiter.reset()
        self.confirmation_gate.clear()
