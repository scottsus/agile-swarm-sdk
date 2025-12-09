import asyncio
from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Input, Static

from agile_ai_sdk import AgentTeam
from agile_ai_sdk.models import Event
from agile_ai_tui.models import MessageType
from agile_ai_tui.utils import EventFormatter
from agile_ai_tui.widgets import CollapsibleMessage


class ChatMessage(Static):
    """Widget representing a single chat message.

    Supports different message types with appropriate styling:
    - user: User messages (blue)
    - agent: Agent messages (green)
    - system: System messages (dim)
    - error: Error messages (red)

    Example:
        >>> ChatMessage("Add /health", "You", "user")  # Blue user message
        >>> ChatMessage("Working on it", "Dev", "agent")  # Green agent message
        >>> ChatMessage("Task started", "System", "system")  # Dim system message
    """

    def __init__(
        self,
        content: str,
        sender: str = "You",
        message_type: MessageType = MessageType.USER,
    ) -> None:
        super().__init__()
        self.content = content
        self.sender = sender
        self.message_type = message_type
        self.update(self._format())

    def _format(self) -> str:
        """Format message based on type."""

        if self.message_type == MessageType.USER:
            return f"[bold blue]{self.sender}:[/bold blue] {self.content}"
        elif self.message_type == MessageType.AGENT:
            return f"[bold green]{self.sender}:[/bold green] {self.content}"
        elif self.message_type == MessageType.SYSTEM:
            return f"[dim]{self.sender}: {self.content}[/dim]"
        elif self.message_type == MessageType.ERROR:
            return f"[bold red]{self.sender}:[/bold red] {self.content}"
        else:
            return f"[bold]{self.sender}:[/bold] {self.content}"


class ChatScreen(Screen):
    """Main chat interface screen.

    This screen displays a scrollable message history and an input field
    for user messages. In Phase 2, messages are simply echoed back.
    Phase 3 will integrate with the agent team.

    User workflow:
    1. Type message in input field
    2. Press Enter to submit
    3. Message appears as "You: [message]"
    4. Input field clears and refocuses
    5. Press 'q' to quit

    Example:
        User types "Hello" and presses Enter
        -> Message appears as "You: Hello"
        -> Input clears, ready for next message
    """

    def __init__(self) -> None:
        """Initialize chat screen."""

        super().__init__()

        self.team: AgentTeam | None = None
        self._workspace_dir: Path = Path.cwd()
        self._started: bool = False

    CSS = """
    ChatScreen {
        layout: vertical;
    }

    #message-container {
        height: 1fr;
        border: solid $primary;
        padding: 1;
        background: $surface;
    }

    ChatMessage {
        margin-bottom: 1;
    }

    Input {
        dock: bottom;
        height: 3;
        border: solid $accent;
    }
    """

    def compose(self) -> ComposeResult:
        """Create child widgets for the chat screen."""

        yield VerticalScroll(id="message-container")
        yield Input(placeholder="Type a message...", id="user-input")

    async def on_mount(self) -> None:
        """Called when screen is mounted - start agent team and focus input."""

        self.query_one("#user-input", Input).focus()

        try:
            self.team = AgentTeam(log_dir=".agile/runs")
            self.team.on_any_event(self._handle_agent_event)
            await self.team.start(self._workspace_dir)
            self._started = True

        except Exception as e:
            await self._show_error_message(f"Failed to start agent team: {e}")
            self.query_one("#user-input", Input).disabled = True

    async def on_unmount(self) -> None:
        """Called when screen is unmounted - clean up agent team."""

        if self.team and self._started:
            try:
                await asyncio.wait_for(self.team.stop(), timeout=5.0)
            except (asyncio.TimeoutError, Exception):
                pass

        self._started = False

    @on(Input.Submitted)
    async def handle_message_submit(self, event: Input.Submitted) -> None:
        """Handle user message submission.

        Sends the message to the agent team and displays it in the chat.
        """

        message = event.value.strip()

        if not message:
            return

        event.input.value = ""

        container = self.query_one("#message-container", VerticalScroll)
        await container.mount(ChatMessage(message, sender="You", message_type=MessageType.USER))

        container.scroll_end(animate=False)

        if self.team and self._started:
            try:
                await self.team.drop_message(message)
            except Exception as e:
                await self._show_error_message(f"Failed to send message: {e}")
        else:
            await self._show_error_message("Agent team not started")

    async def _handle_agent_event(self, event: Event) -> None:
        """Process a single agent event.

        This is called for every event emitted by the agent team. It formats
        the event and displays it in the UI.
        """

        try:
            formatted = EventFormatter.format_event(event)

            if formatted is None:
                return

            container = self.query_one("#message-container", VerticalScroll)

            if formatted.is_collapsible and formatted.full_content:
                header = f"{formatted.sender}: {formatted.message_type.value.capitalize()}"
                await container.mount(
                    CollapsibleMessage(
                        header=header,
                        preview=formatted.content,
                        full_content=formatted.full_content,
                        message_type=formatted.message_type,
                    )
                )
            else:
                await container.mount(
                    ChatMessage(
                        content=formatted.content,
                        sender=formatted.sender,
                        message_type=formatted.message_type,
                    )
                )
            container.scroll_end(animate=False)

        except Exception as e:
            await self._show_error_message(f"Error handling event: {e}")

    async def _show_error_message(self, error: str) -> None:
        """Display an error message in the UI."""

        try:
            error_widget = ChatMessage(
                content=error,
                sender="System",
                message_type=MessageType.ERROR,
            )

            container = self.query_one("#message-container", VerticalScroll)
            await container.mount(error_widget)

            container.scroll_end(animate=False)

        except Exception:
            pass
