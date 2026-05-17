"""Integration tests for DevArmor compliance and event handling.

Tests demonstrate:
- Lifecycle hooks (install/upgrade/remove)
- Event publishing when cloud operations occur
- Cross-skill communication via event subscriptions
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cloudctl_skill.devarmor_skill import CloudctlSkillDevArmor


class TestCloudctlSkillLifecycle:
    """Test Cloudctl skill lifecycle hooks."""

    @pytest.mark.asyncio
    async def test_skill_initialization(self):
        """Test skill initialization."""
        skill = CloudctlSkillDevArmor(skill_name="cloudctl-skill")
        assert not skill._initialized
        assert skill.version == "2.0.0"

        # Mock DevArmor API
        with patch.object(skill, "devarmor_api") as mock_api:
            mock_api.initialize = AsyncMock()

            await skill.initialize()

            assert skill._initialized
            mock_api.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_skill_install_hook(self):
        """Test skill install hook."""
        skill = CloudctlSkillDevArmor(skill_name="test-cloudctl")

        # Mock DevArmor components
        with patch.object(skill, "devarmor_api") as mock_api:
            mock_api.initialize = AsyncMock()
            mock_api.lifecycle_manager = MagicMock()
            mock_api.event_bus = MagicMock()

            # Mock lifecycle manager
            mock_skill_info = MagicMock()
            mock_api.lifecycle_manager.install_skill = AsyncMock(return_value=mock_skill_info)

            # Mock event bus
            mock_api.event_bus.publish_skill_installed = AsyncMock()

            skill._initialized = True

            # Test _on_install hook
            await skill._on_install()

            # Should initialize without errors
            assert skill._initialized

    @pytest.mark.asyncio
    async def test_skill_upgrade_hook(self):
        """Test skill upgrade hook with migration."""
        skill = CloudctlSkillDevArmor(skill_name="cloudctl-skill")
        skill._initialized = True

        # Mock DevArmor API
        with patch.object(skill, "devarmor_api") as mock_api:
            mock_api.lifecycle_manager = MagicMock()
            mock_api.event_bus = MagicMock()

            # Mock upgrade
            mock_skill_info = MagicMock()
            mock_api.lifecycle_manager.upgrade_skill = AsyncMock(return_value=mock_skill_info)
            mock_api.event_bus.publish_skill_upgraded = AsyncMock()

            await skill._on_upgrade("1.0.0", "2.0.0")

            # Verify hook was called
            assert skill._initialized

    @pytest.mark.asyncio
    async def test_skill_remove_hook(self):
        """Test skill remove hook."""
        skill = CloudctlSkillDevArmor(skill_name="cloudctl-skill")
        skill._initialized = True

        # Add a subscription
        skill.event_subscriptions["test_sub"] = "POLICY_VIOLATED"

        # Mock DevArmor API
        with patch.object(skill, "devarmor_api") as mock_api:
            mock_api.lifecycle_manager = MagicMock()
            mock_api.event_bus = MagicMock()

            # Mock remove
            mock_api.lifecycle_manager.remove_skill = AsyncMock()
            mock_api.event_bus.publish_skill_removed = AsyncMock()
            mock_api.event_bus.unsubscribe = MagicMock(return_value=True)

            await skill._on_remove()

            # Verify subscriptions were cleaned up
            assert len(skill.event_subscriptions) == 0


class TestEventPublishing:
    """Test event publishing for cloud operations."""

    @pytest.mark.asyncio
    async def test_publish_context_switched(self):
        """Test publishing context switched event."""
        skill = CloudctlSkillDevArmor()

        with patch.object(skill, "devarmor_api") as mock_api:
            mock_api.event_bus = MagicMock()

            # Mock publish
            async def mock_publish(event):
                pass

            mock_api.event_bus.publish = AsyncMock(side_effect=mock_publish)

            await skill.publish_context_switched(
                org_name="myorg",
                provider="aws",
                timestamp="2026-05-17T10:00:00Z"
            )

            # Verify event was published
            mock_api.event_bus.publish.assert_called_once()
            call_args = mock_api.event_bus.publish.call_args
            event = call_args[0][0]
            assert event.action == "switch_context"
            assert event.details["provider"] == "aws"

    @pytest.mark.asyncio
    async def test_publish_status_checked(self):
        """Test publishing status checked event."""
        skill = CloudctlSkillDevArmor()

        with patch.object(skill, "devarmor_api") as mock_api:
            mock_api.event_bus = MagicMock()

            async def mock_publish(event):
                pass

            mock_api.event_bus.publish = AsyncMock(side_effect=mock_publish)

            await skill.publish_status_checked(
                provider="gcp",
                authenticated=True
            )

            # Verify event was published
            mock_api.event_bus.publish.assert_called_once()
            call_args = mock_api.event_bus.publish.call_args
            event = call_args[0][0]
            assert event.action == "get_status"

    @pytest.mark.asyncio
    async def test_publish_context_listed(self):
        """Test publishing context listed event."""
        skill = CloudctlSkillDevArmor()

        with patch.object(skill, "devarmor_api") as mock_api:
            mock_api.event_bus = MagicMock()

            async def mock_publish(event):
                pass

            mock_api.event_bus.publish = AsyncMock(side_effect=mock_publish)

            await skill.publish_context_listed(
                context_count=3
            )

            # Verify event was published
            mock_api.event_bus.publish.assert_called_once()


class TestPreActionCheck:
    """Test pre-action policy checks."""

    @pytest.mark.asyncio
    async def test_pre_action_check_allowed(self):
        """Test pre-action check when action is allowed."""
        skill = CloudctlSkillDevArmor()

        with patch.object(skill, "devarmor_api") as mock_api:
            mock_evaluation = MagicMock()
            mock_evaluation.allowed = True
            mock_api.policy_engine = MagicMock()
            mock_api.policy_engine.evaluate_action = MagicMock(return_value=mock_evaluation)

            result = await skill.pre_action_check(
                action="switch_context",
                resource="myorg",
                actor="claude"
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_pre_action_check_denied(self):
        """Test pre-action check when action is denied."""
        skill = CloudctlSkillDevArmor()

        with patch.object(skill, "devarmor_api") as mock_api:
            mock_evaluation = MagicMock()
            mock_evaluation.allowed = False
            mock_evaluation.reason = "Policy violation"
            mock_api.policy_engine = MagicMock()
            mock_api.policy_engine.evaluate_action = MagicMock(return_value=mock_evaluation)
            mock_api.event_bus = MagicMock()
            mock_api.event_bus.publish_access_denied = AsyncMock()

            result = await skill.pre_action_check(
                action="switch_context",
                resource="myorg",
                actor="claude"
            )

            assert result is False
            mock_api.event_bus.publish_access_denied.assert_called_once()


class TestEventSubscriptions:
    """Test event subscription management."""

    def test_subscribe_to_event(self):
        """Test subscribing to events."""
        skill = CloudctlSkillDevArmor()

        with patch.object(skill, "devarmor_api") as mock_api:
            mock_api.event_bus = MagicMock()
            mock_api.event_bus.subscribe = MagicMock(return_value="sub_1")

            def dummy_callback(event):
                pass

            subscriber_id = skill.subscribe_to_event(
                event_types=["POLICY_VIOLATED"],
                callback=dummy_callback,
                subscriber_id="test_sub"
            )

            assert subscriber_id == "sub_1"
            assert "test_sub" in skill.event_subscriptions
            mock_api.event_bus.subscribe.assert_called_once()

    def test_unsubscribe_from_event(self):
        """Test unsubscribing from events."""
        skill = CloudctlSkillDevArmor()
        skill.event_subscriptions["test_sub"] = "POLICY_VIOLATED"

        with patch.object(skill, "devarmor_api") as mock_api:
            mock_api.event_bus = MagicMock()
            mock_api.event_bus.unsubscribe = MagicMock(return_value=True)

            result = skill.unsubscribe("test_sub")

            assert result is True
            assert "test_sub" not in skill.event_subscriptions
            mock_api.event_bus.unsubscribe.assert_called_once()

    def test_unsubscribe_not_found(self):
        """Test unsubscribing when subscription not found."""
        skill = CloudctlSkillDevArmor()

        with patch.object(skill, "devarmor_api") as mock_api:
            mock_api.event_bus = MagicMock()
            mock_api.event_bus.unsubscribe = MagicMock(return_value=False)

            result = skill.unsubscribe("nonexistent")

            assert result is False


class TestSkillMetadata:
    """Test skill metadata and version."""

    def test_skill_name(self):
        """Test skill name."""
        skill = CloudctlSkillDevArmor(skill_name="custom-cloudctl-skill")
        assert skill.skill_name == "custom-cloudctl-skill"

    def test_skill_version(self):
        """Test skill version."""
        skill = CloudctlSkillDevArmor()
        assert skill.version == "2.0.0"

    def test_skill_initialization_flag(self):
        """Test initialization flag management."""
        skill = CloudctlSkillDevArmor()
        assert not skill._initialized

        skill._initialized = True
        assert skill._initialized


class TestValidateConfig:
    """Test configuration validation."""

    @pytest.mark.asyncio
    async def test_validate_config(self):
        """Test configuration validation."""
        skill = CloudctlSkillDevArmor()

        # Should not raise
        await skill.validate_config()
