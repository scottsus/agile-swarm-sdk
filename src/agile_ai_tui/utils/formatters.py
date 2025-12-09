from agile_ai_sdk.models import AgentRole, Event, EventType, HumanRole
from agile_ai_tui.models import FormattedMessage, MessageType


class EventFormatter:
    """Formats SDK events for display in the TUI.

    This class converts raw Event objects from the SDK into user-friendly
    FormattedMessage objects. Internal events are filtered out (return None).

    Example:
        >>> event = Event(type=EventType.RUN_STARTED, agent=AgentRole.EM, data={"task": "test"})
        >>> formatted = EventFormatter.format_event(event)
        >>> formatted.sender
        'System'
        >>> formatted.content
        'Starting task: test'
    """

    MAX_PREVIEW_LENGTH = 500

    AGENT_DISPLAY_NAMES = {
        AgentRole.EM: "EM",
        AgentRole.PLANNER: "Planner",
        AgentRole.DEV: "Dev",
        AgentRole.SENIOR_REVIEWER: "Reviewer",
        AgentRole.CODE_ACT: "CodeAct",
    }

    @classmethod
    def format_event(cls, event: Event) -> FormattedMessage | None:
        """Format an event for display.

        Returns:
            FormattedMessage if event should be displayed, None if filtered
        """
        handlers = {
            EventType.RUN_STARTED: cls._format_run_started,
            EventType.RUN_FINISHED: cls._format_run_finished,
            EventType.RUN_ERROR: cls._format_run_error,
            EventType.TEXT_MESSAGE_CONTENT: cls._format_text_message,
            EventType.STEP_STARTED: cls._format_step_started,
            EventType.STEP_FINISHED: cls._format_step_finished,
            EventType.TOOL_CALL_START: cls._format_tool_call_start,
            EventType.TOOL_CALL_RESULT: cls._format_tool_call_result,
        }

        handler = handlers.get(event.type)
        return handler(event) if handler else None

    @classmethod
    def _create_message_with_preview(
        cls,
        content: str,
        sender: str,
        message_type: MessageType,
        agent_role: AgentRole | None = None,
        prefix: str = "",
    ) -> FormattedMessage:
        """Create a FormattedMessage with automatic preview for long content.

        Args:
            content: The message content
            sender: The sender name
            message_type: Type of message (system, agent, error)
            agent_role: Optional agent role
            prefix: Optional prefix to add to short content (e.g., "Error: ", "Tool result: ")
        """
        is_long = len(content) > cls.MAX_PREVIEW_LENGTH

        if is_long:
            preview = content[: cls.MAX_PREVIEW_LENGTH] + "..."
            return FormattedMessage(
                sender=sender,
                content=preview,
                message_type=message_type,
                agent_role=agent_role,
                is_collapsible=True,
                full_content=content,
            )
        else:
            display_content = f"{prefix}{content}" if prefix else content
            return FormattedMessage(
                sender=sender,
                content=display_content,
                message_type=message_type,
                agent_role=agent_role,
            )

    @classmethod
    def _format_run_started(cls, event: Event) -> FormattedMessage:
        task = event.data.get("task", "Unknown task")
        return FormattedMessage(
            sender="System",
            content=f"Starting task: {task}",
            message_type=MessageType.SYSTEM,
        )

    @classmethod
    def _format_run_finished(cls, event: Event) -> FormattedMessage:
        return FormattedMessage(
            sender="System",
            content="Task completed successfully",
            message_type=MessageType.SYSTEM,
        )

    @classmethod
    def _format_run_error(cls, event: Event) -> FormattedMessage:
        error = event.data.get("error", "Unknown error")
        error_str = str(error)

        return cls._create_message_with_preview(
            content=error_str,
            sender="System",
            message_type=MessageType.ERROR,
            prefix="Error: ",
        )

    @classmethod
    def _format_text_message(cls, event: Event) -> FormattedMessage | None:
        action = event.data.get("action")

        if action == "sent":
            return None
        elif action == "received":
            return cls._format_received_message(event)
        else:
            return cls._format_agent_message(event)

    @classmethod
    def _format_received_message(cls, event: Event) -> FormattedMessage:
        """Format a received message event."""
        content = event.data.get("content", "")
        agent_name = cls._get_agent_name(event.agent)
        formatted_content = f"[received] {content}"

        return cls._create_message_with_preview(
            content=formatted_content,
            sender=agent_name,
            message_type=MessageType.SYSTEM,
            agent_role=event.agent if isinstance(event.agent, AgentRole) else None,
        )

    @classmethod
    def _format_agent_message(cls, event: Event) -> FormattedMessage:
        """Format a regular agent message event."""
        content = event.data.get("message", "")
        agent_name = cls._get_agent_name(event.agent)

        return cls._create_message_with_preview(
            content=content,
            sender=agent_name,
            message_type=MessageType.AGENT,
            agent_role=event.agent if isinstance(event.agent, AgentRole) else None,
        )

    @classmethod
    def _get_agent_name(cls, agent: AgentRole | HumanRole) -> str:
        """Get display name for an agent or human role."""

        if isinstance(agent, HumanRole):
            if agent == HumanRole.USER:
                return "You"
            return str(agent)
        elif isinstance(agent, AgentRole):
            return cls.AGENT_DISPLAY_NAMES.get(agent, str(agent))
        else:
            return str(agent)

    @classmethod
    def _format_step_started(cls, event: Event) -> FormattedMessage:
        agent_name = cls._get_agent_name(event.agent)
        step_name = event.data.get("status", "unknown step")

        return FormattedMessage(
            sender=agent_name,
            content=f"Starting {step_name}",
            message_type=MessageType.SYSTEM,
            agent_role=event.agent if isinstance(event.agent, AgentRole) else None,
        )

    @classmethod
    def _format_step_finished(cls, event: Event) -> FormattedMessage:
        agent_name = cls._get_agent_name(event.agent)
        step_name = event.data.get("status", "unknown step")

        return FormattedMessage(
            sender=agent_name,
            content=f"Completed {step_name}",
            message_type=MessageType.SYSTEM,
            agent_role=event.agent if isinstance(event.agent, AgentRole) else None,
        )

    @classmethod
    def _format_tool_call_start(cls, event: Event) -> FormattedMessage:
        agent_name = cls._get_agent_name(event.agent)
        tool = event.data.get("tool", "unknown tool")

        return FormattedMessage(
            sender=agent_name,
            content=f"Calling tool: {tool}",
            message_type=MessageType.SYSTEM,
            agent_role=event.agent if isinstance(event.agent, AgentRole) else None,
        )

    @classmethod
    def _format_tool_call_result(cls, event: Event) -> FormattedMessage:
        agent_name = cls._get_agent_name(event.agent)
        result = event.data.get("result", "")
        result_str = str(result)

        return cls._create_message_with_preview(
            content=result_str,
            sender=agent_name,
            message_type=MessageType.SYSTEM,
            agent_role=event.agent if isinstance(event.agent, AgentRole) else None,
            prefix="Tool result: ",
        )

    @classmethod
    def get_agent_display_name(cls, agent: AgentRole) -> str:
        """Get display name for an agent role."""

        return cls.AGENT_DISPLAY_NAMES.get(agent, str(agent))
