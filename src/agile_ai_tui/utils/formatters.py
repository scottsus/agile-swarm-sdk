from agile_ai_sdk.models import AgentRole, Event, EventType, HumanRole
from agile_ai_tui.models import FormattedMessage


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

        if event.type == EventType.RUN_STARTED:
            return cls._format_run_started(event)

        elif event.type == EventType.RUN_FINISHED:
            return cls._format_run_finished(event)

        elif event.type == EventType.RUN_ERROR:
            return cls._format_run_error(event)

        elif event.type == EventType.TEXT_MESSAGE_CONTENT:
            return cls._format_text_message(event)

        elif event.type == EventType.STEP_STARTED:
            return cls._format_step_started(event)

        elif event.type == EventType.STEP_FINISHED:
            return cls._format_step_finished(event)

        elif event.type == EventType.TOOL_CALL_START:
            return cls._format_tool_call_start(event)

        elif event.type == EventType.TOOL_CALL_RESULT:
            return cls._format_tool_call_result(event)

        else:
            return None

    @classmethod
    def _format_run_started(cls, event: Event) -> FormattedMessage:
        task = event.data.get("task", "Unknown task")
        return FormattedMessage(
            sender="System",
            content=f"Starting task: {task}",
            message_type="system",
        )

    @classmethod
    def _format_run_finished(cls, event: Event) -> FormattedMessage:
        return FormattedMessage(
            sender="System",
            content="Task completed successfully",
            message_type="system",
        )

    @classmethod
    def _format_run_error(cls, event: Event) -> FormattedMessage:
        error = event.data.get("error", "Unknown error")
        return FormattedMessage(
            sender="System",
            content=f"Error: {error}",
            message_type="error",
        )

    @classmethod
    def _format_text_message(cls, event: Event) -> FormattedMessage | None:
        if event.data.get("action") == "sent":
            return None

        if event.data.get("action") == "received":
            content = event.data.get("content", "")
            agent_name = cls._get_agent_name(event.agent)
            return FormattedMessage(
                sender=agent_name,
                content=f"[received] {content}",
                message_type="system",
                agent_role=event.agent if isinstance(event.agent, AgentRole) else None,
            )

        content = event.data.get("message", "")
        agent_name = cls._get_agent_name(event.agent)

        return FormattedMessage(
            sender=agent_name,
            content=content,
            message_type="agent",
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
            message_type="system",
            agent_role=event.agent if isinstance(event.agent, AgentRole) else None,
        )

    @classmethod
    def _format_step_finished(cls, event: Event) -> FormattedMessage:
        agent_name = cls._get_agent_name(event.agent)
        step_name = event.data.get("status", "unknown step")

        return FormattedMessage(
            sender=agent_name,
            content=f"Completed {step_name}",
            message_type="system",
            agent_role=event.agent if isinstance(event.agent, AgentRole) else None,
        )

    @classmethod
    def _format_tool_call_start(cls, event: Event) -> FormattedMessage:
        agent_name = cls._get_agent_name(event.agent)
        tool = event.data.get("tool", "unknown tool")

        return FormattedMessage(
            sender=agent_name,
            content=f"Calling tool: {tool}",
            message_type="system",
            agent_role=event.agent if isinstance(event.agent, AgentRole) else None,
        )

    @classmethod
    def _format_tool_call_result(cls, event: Event) -> FormattedMessage:
        agent_name = cls._get_agent_name(event.agent)
        result = event.data.get("result", "")

        max_length = 200
        if len(str(result)) > max_length:
            result = str(result)[:max_length] + "..."

        return FormattedMessage(
            sender=agent_name,
            content=f"Tool result: {result}",
            message_type="system",
            agent_role=event.agent if isinstance(event.agent, AgentRole) else None,
        )

    @classmethod
    def get_agent_display_name(cls, agent: AgentRole) -> str:
        """Get display name for an agent role."""

        return cls.AGENT_DISPLAY_NAMES.get(agent, str(agent))
