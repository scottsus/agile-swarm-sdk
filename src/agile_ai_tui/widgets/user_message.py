from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static


class UserMessage(Horizontal):
    """Widget for displaying user messages.

    User messages are styled with a blue theme and right-aligned to
    distinguish them from agent responses.

    Example:
        >>> widget = UserMessage("Add /health endpoint")
    """

    DEFAULT_CSS = """
    UserMessage {
        width: 100%;
        height: auto;
        margin-bottom: 1;
        align: right top;
    }

    UserMessage .message-container {
        width: auto;
        max-width: 80%;
        height: auto;
        padding: 1 2;
        background: $primary;
        border: solid $primary-lighten-1;
        color: $text;
    }

    UserMessage .sender {
        color: $text;
        text-style: bold;
    }

    UserMessage .content {
        width: auto;
        height: auto;
        color: $text;
        margin-top: 1;
    }
    """

    def __init__(self, content: str) -> None:
        super().__init__()
        self.content = content

    def compose(self) -> ComposeResult:
        """Create child widgets."""

        with Vertical(classes="message-container"):
            yield Static("[You]", classes="sender")
            yield Static(self.content, classes="content")
