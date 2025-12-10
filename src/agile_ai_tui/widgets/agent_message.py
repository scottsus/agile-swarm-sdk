from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Markdown, Static

from agile_ai_sdk.models import AgentRole


class AgentMessage(Vertical):
    """Widget for displaying agent messages with markdown support.

    Agent messages support full markdown rendering including:
    - Headers, lists, quotes
    - Code blocks with syntax highlighting
    - Inline code, bold, italic
    - Links

    Example:
        >>> widget = AgentMessage(
        ...     "I'll add the endpoint. Here's the code:\\n\\n```python\\nprint('hello')\\n```",
        ...     AgentRole.DEV
        ... )
    """

    DEFAULT_CSS = """
    AgentMessage {
        width: 100%;
        height: auto;
        margin-bottom: 1;
    }

    AgentMessage .message-container {
        width: auto;
        max-width: 80%;
        height: auto;
        padding: 1 2;
        background: $success-darken-3;
        border: solid $success;
    }

    AgentMessage .header {
        width: 100%;
        height: auto;
        padding: 0 0 1 0;
    }

    AgentMessage .sender {
        color: $success;
        text-style: bold;
        width: auto;
        height: auto;
    }

    AgentMessage .content {
        color: $text;
        margin-top: 1;
        width: auto;
        height: auto;
    }

    AgentMessage .role {
        color: $success-lighten-2;
        text-style: dim;
    }

    AgentMessage Markdown {
        width: 100%;
        height: auto;
        margin: 0;
        padding: 0;
        background: transparent;
    }
    """

    AGENT_DISPLAY_NAMES = {
        AgentRole.EM: "Engineering Manager",
        AgentRole.PLANNER: "Planner",
        AgentRole.DEV: "Developer",
        AgentRole.SENIOR_REVIEWER: "Senior Reviewer",
        AgentRole.CODE_ACT: "CodeAct Agent",
    }

    def __init__(self, content: str, agent_role: AgentRole) -> None:
        super().__init__()
        self.content = content
        self.agent_role = agent_role
        self.agent_name = self.AGENT_DISPLAY_NAMES.get(agent_role, str(agent_role))

    def compose(self) -> ComposeResult:
        """Create child widgets."""

        with Vertical(classes="message-container"):
            yield Static(f"[{self.agent_name}]", classes="sender")
            yield Markdown(self.content)
