from agile_ai_sdk.models import Event, EventType

# Color codes
GRAY = "\033[90m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"


def _get_agent_color(agent: str) -> str:
    """Get color code based on agent role."""
    agent_lower = agent.lower()

    if "em" in agent_lower or "engineering_manager" in agent_lower:
        return RED
    elif "planner" in agent_lower:
        return BLUE
    elif "executor" in agent_lower:
        return GREEN
    elif "researcher" in agent_lower or "research" in agent_lower:
        return CYAN
    elif "reviewer" in agent_lower:
        return MAGENTA
    else:
        return YELLOW


def _print_box(content: str, color: str = GRAY) -> None:
    """Print content in a box."""
    lines = content.split("\n")
    max_width = max(len(line) for line in lines) if lines else 0

    print(f"{color}┌{'─' * (max_width + 2)}┐{RESET}")
    for line in lines:
        padding = max_width - len(line)
        print(f"{color}│{RESET} {line}{' ' * padding} {color}│{RESET}")
    print(f"{color}└{'─' * (max_width + 2)}┘{RESET}")
    print()


def print_event(event: Event) -> None:
    """Print an event in a nice format.

    Just here temporarily - will refactor into an actual library later
    """
    agent = event.agent.value if hasattr(event.agent, "value") else str(event.agent)
    agent_color = _get_agent_color(agent)

    if event.type == EventType.RUN_STARTED:
        task = event.data.get("task", "")
        _print_box(f"RUN STARTED\nTask: {task}", GREEN)

    elif event.type == EventType.RUN_FINISHED:
        status = event.data.get("status", "completed")
        _print_box(f"RUN FINISHED\nStatus: {status}", GREEN)

    elif event.type == EventType.RUN_ERROR:
        error = event.data.get("error", "unknown")
        _print_box(f"RUN ERROR\nError: {error}", YELLOW)

    elif event.type == EventType.TEXT_MESSAGE_CONTENT:
        action = event.data.get("action")

        if action == "sent":
            to = event.data.get("to", "unknown")
            to_color = _get_agent_color(to)
            print(f"{agent_color}{agent}{RESET} → {to_color}{to}{RESET}")
            print()

        elif action == "received":
            from_ = event.data.get("from_", event.data.get("from", "unknown"))
            content = event.data.get("content", "")
            from_color = _get_agent_color(from_)
            _print_box(f"{from_} → {agent}\n\n{content}", agent_color)

    elif event.type == EventType.STEP_STARTED:
        status = event.data.get("status", "")
        if status and status != "Agent started":
            print(f"{agent_color}{agent}{RESET}: {GRAY}{status}{RESET}")
            print()

    elif event.type == EventType.TOOL_CALL_START:
        tool = event.data.get("tool", "unknown")
        print(f"{agent_color}{agent}{RESET} {GRAY}calling{RESET} {tool}")
        print()

    elif event.type == EventType.TOOL_CALL_RESULT:
        result = event.data.get("result", "")
        print(f"{GRAY}  → {result}{RESET}")
        print()

    else:
        print(
            f"{GRAY}[{agent}] {event.type.value if hasattr(event.type, 'value') else str(event.type)}: {event.data}{RESET}"
        )
        print()
