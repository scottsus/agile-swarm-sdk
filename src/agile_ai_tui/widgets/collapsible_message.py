from textual.app import ComposeResult
from textual.containers import Vertical
from textual.events import Click, Key
from textual.widgets import Static

from agile_ai_tui.models import MessageType


class CollapsibleMessage(Vertical):
    """A message widget that can expand/collapse long content.

    This widget displays a truncated preview by default and allows users to
    expand to see the full content. Useful for tool results, error traces, etc.

    Interaction:
    - Click header to toggle expand/collapse
    - Press Enter or Space when focused to toggle

    Example:
        >>> widget = CollapsibleMessage(
        ...     header="Dev: Tool result",
        ...     preview="Output: Success...",
        ...     full_content="Output: Success\\nFile created\\nTests passed",
        ...     message_type="system"
        ... )
    """

    DEFAULT_CSS = """
    CollapsibleMessage {
        width: 100%;
        height: auto;
        margin-bottom: 1;
        border: solid $panel;
        padding: 0;
    }

    CollapsibleMessage:focus {
        border: solid $accent;
    }

    CollapsibleMessage .header {
        width: 100%;
        height: auto;
        padding: 0 1;
        background: $panel;
    }

    CollapsibleMessage .header:hover {
        background: $primary-darken-1;
    }

    CollapsibleMessage .header-user {
        background: $primary-lighten-2;
    }

    CollapsibleMessage .header-agent {
        background: $success-darken-2;
    }

    CollapsibleMessage .header-system {
        background: $panel;
    }

    CollapsibleMessage .header-error {
        background: $error-darken-2;
    }

    CollapsibleMessage .content {
        width: 100%;
        height: auto;
        padding: 1;
        background: $surface;
    }
    """

    def __init__(
        self,
        header: str,
        preview: str,
        full_content: str,
        message_type: MessageType = MessageType.SYSTEM,
    ) -> None:
        super().__init__()
        self.header_text = header
        self.preview_text = preview
        self.full_content_text = full_content
        self.message_type = message_type
        self.is_expanded = False
        self.can_focus = True

    def compose(self) -> ComposeResult:
        """Create child widgets."""

        header_class = f"header header-{self.message_type.value}"
        indicator = "▼" if self.is_expanded else "▶"

        yield Static(
            f"{indicator} {self.header_text}",
            id="header",
            classes=header_class,
        )
        yield Static(
            self.full_content_text if self.is_expanded else self.preview_text,
            id="content",
            classes="content",
        )

    async def on_click(self, event: Click) -> None:
        """Handle clicks anywhere on the widget to toggle."""
        self.is_expanded = not self.is_expanded
        self._update_display()
        event.stop()

    async def on_key(self, event: Key) -> None:
        """Handle keyboard input to toggle when focused."""
        if event.key in ("enter", "space"):
            self.is_expanded = not self.is_expanded
            self._update_display()
            event.stop()

    def _update_display(self) -> None:
        """Update widget display based on expanded state."""

        header = self.query_one("#header", Static)
        content = self.query_one("#content", Static)

        indicator = "▼" if self.is_expanded else "▶"
        header.update(f"{indicator} {self.header_text}")

        if self.is_expanded:
            content.update(self.full_content_text)
        else:
            content.update(self.preview_text)
