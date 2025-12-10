from textual.widgets import Static


class SystemMessage(Static):
    """Widget for displaying system messages and events.

    System messages are used for:
    - Run started/finished notifications
    - Step started/finished updates
    - Internal events
    - Status messages

    These are styled with a dim, unobtrusive appearance to not
    distract from user and agent messages.

    Example:
        >>> widget = SystemMessage("Task completed successfully")
        >>> widget = SystemMessage("Error: Failed to start agent", is_error=True)
    """

    DEFAULT_CSS = """
    SystemMessage {
        width: 100%;
        height: auto;
        margin-bottom: 1;
        padding: 0 2;
        color: $text-muted;
        text-style: dim;
        text-align: center;
    }

    SystemMessage.error {
        color: $error;
        text-style: bold;
        text-align: center;
    }
    """

    def __init__(self, content: str, is_error: bool = False) -> None:
        classes = "error" if is_error else ""
        super().__init__(content, classes=classes)
