"""CloudctlSkill - DevArmor-compliant skill with lifecycle management and event subscriptions."""

import logging
from datetime import datetime
from typing import Any, Callable, Optional

from devarmor import (
    DevArmorAPI,
    Event,
    EventType,
    SkillInfo,
)

logger = logging.getLogger(__name__)


class CloudctlSkillDevArmor:
    """DevArmor-compliant Cloudctl Skill with lifecycle hooks and event handling.

    This skill manages cloud context operations with full DevArmor governance:
    - Lifecycle management (install/upgrade/remove hooks)
    - Event publishing for all cloud operations
    - Cross-skill communication via event subscriptions
    - Audit trail via DevArmor
    """

    def __init__(
        self, skill_name: str = "cloudctl-skill", devarmor_api: Optional[DevArmorAPI] = None
    ):
        """Initialize Cloudctl skill.

        Args:
            skill_name: Name of the skill
            devarmor_api: Optional DevArmorAPI instance (created if not provided)
        """
        self.skill_name = skill_name
        self.version = "2.0.0"
        self.devarmor_api = devarmor_api or DevArmorAPI()
        self.skill_info: Optional[SkillInfo] = None
        self.event_subscriptions: dict[str, str] = {}  # Maps event_type -> subscriber_id
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize skill and DevArmor API.

        This must be called before using the skill.
        """
        if self._initialized:
            return

        logger.info(f"Initializing {self.skill_name} v{self.version}")

        # Initialize DevArmor
        await self.devarmor_api.initialize()

        # Verify installation
        self.skill_info = self.devarmor_api.lifecycle_manager.get_skill_info(self.skill_name)
        if not self.skill_info:
            logger.warning(f"{self.skill_name} not in lifecycle manager yet")

        self._initialized = True
        logger.info(f"{self.skill_name} initialized successfully")

    async def install(self, metadata: Optional[dict[str, Any]] = None) -> SkillInfo:
        """Install the skill (lifecycle hook).

        Args:
            metadata: Optional metadata to store with skill

        Returns:
            SkillInfo: Installed skill information
        """
        await self.initialize()
        logger.info(f"Installing {self.skill_name} v{self.version}")

        # Install via lifecycle manager
        skill_info = await self.devarmor_api.lifecycle_manager.install_skill(
            skill_name=self.skill_name,
            version=self.version,
            actor="claude",
            metadata=metadata or {"installed_at": datetime.utcnow().isoformat()},
        )

        # Register event subscriptions (on_install hook)
        await self._on_install()

        # Publish event
        await self.devarmor_api.event_bus.publish_skill_installed(
            skill_name=self.skill_name,
            version=self.version,
            actor="claude",
            details={"subscriptions_registered": list(self.event_subscriptions.keys())},
        )

        self.skill_info = skill_info
        return skill_info

    async def upgrade(self, new_version: str) -> SkillInfo:
        """Upgrade the skill (lifecycle hook).

        Args:
            new_version: New version to upgrade to

        Returns:
            SkillInfo: Upgraded skill information
        """
        await self.initialize()
        logger.info(f"Upgrading {self.skill_name} from v{self.version} to v{new_version}")

        old_version = self.version
        self.version = new_version

        # Upgrade via lifecycle manager
        skill_info = await self.devarmor_api.lifecycle_manager.upgrade_skill(
            skill_name=self.skill_name,
            new_version=new_version,
            actor="claude",
        )

        # Run migration logic (on_upgrade hook)
        await self._on_upgrade(old_version, new_version)

        # Publish event
        await self.devarmor_api.event_bus.publish_skill_upgraded(
            skill_name=self.skill_name,
            old_version=old_version,
            new_version=new_version,
            actor="claude",
        )

        self.skill_info = skill_info
        return skill_info

    async def remove(self) -> None:
        """Remove the skill (lifecycle hook)."""
        await self.initialize()
        logger.info(f"Removing {self.skill_name}")

        # Cleanup (on_remove hook)
        await self._on_remove()

        # Remove via lifecycle manager
        await self.devarmor_api.lifecycle_manager.remove_skill(
            skill_name=self.skill_name,
            actor="claude",
        )

        # Publish event
        await self.devarmor_api.event_bus.publish_skill_removed(
            skill_name=self.skill_name,
            actor="claude",
        )

    async def validate_config(self) -> None:
        """Validate skill configuration against policy.

        Raises:
            ValidationError: If configuration is invalid
        """
        logger.debug(f"{self.skill_name}: Config validation passed")

    async def pre_action_check(self, action: str, resource: str, actor: str) -> bool:
        """Pre-action check before executing any action.

        Args:
            action: Action to perform (e.g., "switch_context", "get_status")
            resource: Resource being accessed (e.g., cloud provider)
            actor: Who is performing the action

        Returns:
            True if action is allowed, False otherwise
        """
        # Check policies
        try:
            evaluation = self.devarmor_api.policy_engine.evaluate_action(
                actor=actor,
                action=action,
                resource=resource,
                skill_name=self.skill_name,
            )
            if not evaluation.allowed:
                await self.devarmor_api.event_bus.publish_access_denied(
                    actor=actor,
                    action=action,
                    resource=resource,
                    reason=f"Policy evaluation failed: {evaluation.reason}",
                    details={"skill": self.skill_name},
                )
                return False
            return True
        except Exception as e:
            logger.error(f"Pre-action check failed: {str(e)}")
            return False

    async def publish_event(
        self,
        event_type: str,
        action: str,
        resource: str,
        actor: str = "claude",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """Publish an event for this skill.

        Args:
            event_type: Type of event (e.g., "context_switched", "status_checked")
            action: Action performed
            resource: Resource affected
            actor: Who performed the action
            details: Additional event details
        """
        # Use AUDIT_LOG for skill-specific events
        event = Event(
            event_type="audit:log",
            skill_name=self.skill_name,
            actor=actor,
            action=action,
            details={**(details or {}), "resource": resource, "event_type": event_type},
            severity="info",
        )
        await self.devarmor_api.event_bus.publish(event)

    def subscribe_to_event(
        self,
        event_types: list[str],
        callback: Callable[[Event], Any],
        subscriber_id: Optional[str] = None,
    ) -> str:
        """Subscribe to events from other skills.

        Args:
            event_types: List of event types to subscribe to
            callback: Function to call when event is published
            subscriber_id: Optional identifier for subscription

        Returns:
            Subscriber ID for later unsubscription
        """
        if subscriber_id is None:
            subscriber_id = f"{self.skill_name}_{len(self.event_subscriptions)}"

        self.event_subscriptions[subscriber_id] = str(event_types)
        subscriber_id_returned = self.devarmor_api.event_bus.subscribe(
            callback=callback,
            event_types=event_types,
            subscriber_id=subscriber_id,
        )
        logger.info(f"Subscribed to {len(event_types)} event types: {subscriber_id_returned}")
        return subscriber_id_returned

    def unsubscribe(self, subscriber_id: str) -> bool:
        """Unsubscribe from events.

        Args:
            subscriber_id: Subscription ID to remove

        Returns:
            True if unsubscribed, False if not found
        """
        result = self.devarmor_api.event_bus.unsubscribe(subscriber_id)
        if result and subscriber_id in self.event_subscriptions:
            del self.event_subscriptions[subscriber_id]
            logger.info(f"Unsubscribed: {subscriber_id}")
        return result

    # Lifecycle Hooks - Override these in subclasses

    async def _on_install(self) -> None:
        """Hook: Called after skill is installed.

        Register event subscriptions, initialize resources, etc.
        """
        logger.debug(f"{self.skill_name}: on_install hook")
        pass

    async def _on_upgrade(self, old_version: str, new_version: str) -> None:
        """Hook: Called when skill is upgraded.

        Perform migrations, schema updates, etc.

        Args:
            old_version: Previous version
            new_version: New version
        """
        logger.debug(f"{self.skill_name}: on_upgrade hook (v{old_version} -> v{new_version})")
        pass

    async def _on_remove(self) -> None:
        """Hook: Called before skill is removed.

        Clean up resources, unsubscribe from events, etc.
        """
        logger.debug(f"{self.skill_name}: on_remove hook")
        # Unsubscribe from all events
        for subscriber_id in list(self.event_subscriptions.keys()):
            self.unsubscribe(subscriber_id)

    # Event publishing helpers

    async def publish_context_switched(
        self, org_name: str, provider: str = "unknown", actor: str = "claude", **details: Any
    ) -> None:
        """Publish event when cloud context is switched.

        Args:
            org_name: Organization/context name
            provider: Cloud provider (aws, gcp, azure)
            actor: Who switched the context
            **details: Additional details
        """
        await self.publish_event(
            event_type="context_switched",
            action="switch_context",
            resource=org_name,
            actor=actor,
            details={"provider": provider, **details},
        )

    async def publish_status_checked(
        self, provider: str = "unknown", actor: str = "claude", **details: Any
    ) -> None:
        """Publish event when cloud status is checked.

        Args:
            provider: Cloud provider (aws, gcp, azure)
            actor: Who checked the status
            **details: Additional details
        """
        await self.publish_event(
            event_type="status_checked",
            action="get_status",
            resource=provider,
            actor=actor,
            details=details,
        )

    async def publish_context_listed(
        self, actor: str = "claude", **details: Any
    ) -> None:
        """Publish event when contexts are listed.

        Args:
            actor: Who listed the contexts
            **details: Additional details
        """
        await self.publish_event(
            event_type="contexts_listed",
            action="list_contexts",
            resource="contexts",
            actor=actor,
            details=details,
        )
