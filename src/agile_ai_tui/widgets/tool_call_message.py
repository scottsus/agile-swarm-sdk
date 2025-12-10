import json

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static

from agile_ai_sdk.models import AgentRole
from agile_ai_tui.models import ToolCallData


class ToolCallMessage(Vertical):
    """Widget for displaying tool calls with structured layout.

    Tool calls show:
    - Agent name and tool being called
    - Function arguments (formatted JSON or string)
    - Result (if available)
    - Status indicator (running/success/error)

    Example:
        >>> data = ToolCallData(
        ...     tool_name="bash",
        ...     args={"command": "ls"},
        ...     result="file1.py\\nfile2.py",
        ...     status="success"
        ... )
        >>> widget = ToolCallMessage(AgentRole.DEV, data)
    """

    DEFAULT_CSS = """
    ToolCallMessage {
        width: 100%;
        height: auto;
        margin-bottom: 1;
    }

    ToolCallMessage .message-container {
        width: auto;
        max-width: 90%;
        height: auto;
        padding: 1;
        background: $panel;
        border: solid $accent;
    }

    ToolCallMessage .header {
        width: 100%;
        height: auto;
        padding-bottom: 1;
        color: $accent;
        text-style: bold;
    }

    ToolCallMessage .section-title {
        width: 100%;
        height: auto;
        margin-top: 1;
        color: $text-muted;
        text-style: bold;
    }

    ToolCallMessage .args {
        width: 100%;
        height: auto;
        padding: 1;
        background: $surface;
        color: $text;
        margin-top: 1;
    }

    ToolCallMessage .result {
        width: 100%;
        height: auto;
        padding: 1;
        background: $surface;
        color: $text;
        margin-top: 1;
    }

    ToolCallMessage .status-started {
        color: $warning;
    }

    ToolCallMessage .status-success {
        color: $success;
    }

    ToolCallMessage .status-error {
        color: $error;
    }
    """

    AGENT_DISPLAY_NAMES = {
        AgentRole.EM: "EM",
        AgentRole.PLANNER: "Planner",
        AgentRole.DEV: "Dev",
        AgentRole.SENIOR_REVIEWER: "Reviewer",
        AgentRole.CODE_ACT: "CodeAct",
    }

    def __init__(self, agent_role: AgentRole, tool_data: ToolCallData) -> None:
        super().__init__()
        self.agent_role = agent_role
        self.tool_data = tool_data
        self.agent_name = self.AGENT_DISPLAY_NAMES.get(agent_role, str(agent_role))

    def compose(self) -> ComposeResult:
        """Create child widgets."""

        status_class = f"status-{self.tool_data.status}"
        status_icon = {
            "started": "⏳",
            "success": "✓",
            "error": "✗",
        }.get(self.tool_data.status, "?")

        with Vertical(classes="message-container"):
            yield Static(
                f"{status_icon} {self.agent_name} → {self.tool_data.tool_name}",
                classes=f"header {status_class}",
            )

            if self.tool_data.args:
                yield Static("Arguments:", classes="section-title")
                args_str = self._format_args(self.tool_data.args)
                yield Static(args_str, classes="args")

            if self.tool_data.result:
                yield Static("Result:", classes="section-title")
                yield Static(self.tool_data.result, classes="result")

    def _format_args(self, args: dict | str) -> str:
        """Format tool arguments for display."""

        if isinstance(args, str):
            return args

        try:
            return json.dumps(args, indent=2)
        except (TypeError, ValueError):
            return str(args)
