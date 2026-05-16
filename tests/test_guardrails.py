"""Tests for CloudctlSkill guardrails module."""

from cloudctl_skill.guardrails import ConfirmationGate, Guardrails, RateLimiter


class TestRateLimiter:
    """Tests for RateLimiter."""

    def test_rate_limiter_allows_operations_under_limit(self) -> None:
        """Operations under rate limit should be allowed."""
        limiter = RateLimiter(max_per_minute=5)
        for _ in range(5):
            assert limiter.check("test_op") is True

    def test_rate_limiter_blocks_operations_over_limit(self) -> None:
        """Operations over rate limit should be blocked."""
        limiter = RateLimiter(max_per_minute=2)
        limiter.check("test_op")
        limiter.check("test_op")
        assert limiter.check("test_op") is False

    def test_rate_limiter_reset(self) -> None:
        """Resetting limiter should clear operations."""
        limiter = RateLimiter(max_per_minute=1)
        limiter.check("op")
        assert limiter.check("op") is False
        limiter.reset()
        assert limiter.check("op") is True

    def test_rate_limiter_custom_limit(self) -> None:
        """Custom rate limit should be respected."""
        limiter = RateLimiter(max_per_minute=10)
        for _ in range(10):
            assert limiter.check("op") is True
        assert limiter.check("op") is False


class TestConfirmationGate:
    """Tests for ConfirmationGate."""

    def test_confirmation_gate_identifies_dangerous_operations(self) -> None:
        """Gate should identify operations requiring confirmation."""
        gate = ConfirmationGate()
        assert gate.requires_confirmation("switch_context") is True
        assert gate.requires_confirmation("delete_resource") is True
        assert gate.requires_confirmation("revoke_credentials") is True
        assert gate.requires_confirmation("get_context") is False

    def test_confirmation_gate_request_confirmation(self) -> None:
        """Requesting confirmation should not raise errors."""
        gate = ConfirmationGate()
        gate.request_confirmation("op_123", "switch_context")  # Should not raise

    def test_confirmation_gate_confirm_operation(self) -> None:
        """Confirming an operation should mark it as confirmed."""
        gate = ConfirmationGate()
        assert gate.confirm("op_123") is True
        assert gate.is_confirmed("op_123") is True

    def test_confirmation_gate_unconfirmed_operation(self) -> None:
        """Unconfirmed operation should not be confirmed."""
        gate = ConfirmationGate()
        assert gate.is_confirmed("op_999") is False

    def test_confirmation_gate_clear_specific(self) -> None:
        """Clearing specific operation should remove it."""
        gate = ConfirmationGate()
        gate.confirm("op_1")
        gate.confirm("op_2")
        gate.clear("op_1")
        assert gate.is_confirmed("op_1") is False
        assert gate.is_confirmed("op_2") is True

    def test_confirmation_gate_clear_all(self) -> None:
        """Clearing all should remove all confirmations."""
        gate = ConfirmationGate()
        gate.confirm("op_1")
        gate.confirm("op_2")
        gate.clear()
        assert gate.is_confirmed("op_1") is False
        assert gate.is_confirmed("op_2") is False

    def test_confirmation_gate_timeout_seconds(self) -> None:
        """Timeout parameter should be stored."""
        gate = ConfirmationGate(timeout_seconds=60)
        assert gate.timeout_seconds == 60


class TestGuardrails:
    """Tests for Guardrails master coordinator."""

    def test_guardrails_init(self) -> None:
        """Guardrails should initialize correctly."""
        rails = Guardrails(max_rate_per_minute=5, confirmation_timeout=300)
        assert rails.rate_limiter.max_per_minute == 5
        assert rails.confirmation_gate.timeout_seconds == 300

    def test_guardrails_check_operation_allowed_safe(self) -> None:
        """Safe operations should be allowed."""
        rails = Guardrails()
        allowed, reason = rails.check_operation("op_123", "get_context")
        assert allowed is True
        assert reason == "Operation allowed"

    def test_guardrails_check_operation_requires_confirmation(self) -> None:
        """Destructive operations without confirmation should be denied."""
        rails = Guardrails()
        allowed, reason = rails.check_operation("op_123", "switch_context")
        assert allowed is False
        assert "Confirmation required" in reason

    def test_guardrails_check_operation_with_confirmation(self) -> None:
        """Destructive operations with confirmation should be allowed."""
        rails = Guardrails()
        rails.confirmation_gate.confirm("op_123")
        allowed, reason = rails.check_operation("op_123", "switch_context", user_confirmed=True)
        assert allowed is True

    def test_guardrails_check_operation_rate_limited(self) -> None:
        """Operations exceeding rate limit should be denied."""
        rails = Guardrails(max_rate_per_minute=1)
        rails.check_operation("op_1", "get_context")
        allowed, reason = rails.check_operation("op_2", "get_context")
        assert allowed is False
        assert "Rate limit exceeded" in reason

    def test_guardrails_reset(self) -> None:
        """Reset should clear all guardrails."""
        rails = Guardrails(max_rate_per_minute=1)
        rails.confirmation_gate.confirm("op_123")
        rails.check_operation("op_1", "get_context")
        rails.reset()
        assert rails.check_operation("op_2", "get_context")[0] is True
        assert rails.confirmation_gate.is_confirmed("op_123") is False

    def test_guardrails_all_operation_types(self) -> None:
        """All dangerous operation types should require confirmation."""
        rails = Guardrails()
        dangerous_ops = [
            "switch_context",
            "delete_resource",
            "revoke_credentials",
            "bulk_modify",
            "logout",
            "reset_credentials",
        ]
        for op_type in dangerous_ops:
            allowed, reason = rails.check_operation("op_123", op_type)
            assert allowed is False, f"{op_type} should require confirmation"
            assert "Confirmation required" in reason
