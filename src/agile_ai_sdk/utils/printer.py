from agile_ai_sdk import Event, EventType


def print_event(event: Event) -> None:
    """Print an event in a nice format.

    Just here temporarily - will refactor into an actual library later
    """

    agent = event.agent.value if hasattr(event.agent, "value") else str(event.agent)
    event_type = event.type.value if hasattr(event.type, "value") else str(event.type)

    # Color codes
    GRAY = "\033[90m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    # Format based on event type
    if event.type == EventType.RUN_STARTED:
        task = event.data.get("task", "")
        print(f"{GREEN}▶ RUN STARTED{RESET}")
        print(f"{GRAY}  Task: {task}{RESET}\n")

    elif event.type == EventType.RUN_FINISHED:
        status = event.data.get("status", "completed")
        print(f"\n{GREEN}✓ RUN FINISHED{RESET}")
        print(f"{GRAY}  Status: {status}{RESET}")

    elif event.type == EventType.RUN_ERROR:
        error = event.data.get("error", "unknown")
        print(f"\n{YELLOW}✗ RUN ERROR{RESET}")
        print(f"{GRAY}  Error: {error}{RESET}")

    elif event.type == EventType.TEXT_MESSAGE_CONTENT:
        action = event.data.get("action")
        if action == "sent":
            to = event.data.get("to", "unknown")
            content = event.data.get("content", "")
            print(f"{BLUE}→{RESET} {BOLD}{agent}{RESET} {GRAY}to{RESET} {BOLD}{to}{RESET}")
            print(f"{GRAY}  {content}{RESET}")

        elif action == "received":
            from_ = event.data.get("from_", event.data.get("from", "unknown"))
            content = event.data.get("content", "")
            print(f"{CYAN}←{RESET} {BOLD}{agent}{RESET} {GRAY}from{RESET} {BOLD}{from_}{RESET}")
            print(f"{GRAY}  {content}{RESET}")

        else:
            # Generic message (e.g., agent greetings)
            message = event.data.get("message", "")
            if message:
                print(f"{MAGENTA}💬{RESET} {BOLD}{agent}{RESET}: {message}")

    elif event.type == EventType.STEP_STARTED:
        status = event.data.get("status", "")
        if status and status != "Agent started":
            print(f"{CYAN}⚙{RESET}  {BOLD}{agent}{RESET}: {GRAY}{status}{RESET}")

    elif event.type == EventType.TOOL_CALL_START:
        tool = event.data.get("tool", "unknown")
        print(f"{YELLOW}🔧{RESET} {BOLD}{agent}{RESET} {GRAY}calling{RESET} {tool}")

    elif event.type == EventType.TOOL_CALL_RESULT:
        result = event.data.get("result", "")
        print(f"{GRAY}  → {result}{RESET}")

    else:
        # Fallback for unknown event types
        print(f"{GRAY}[{agent}] {event_type}: {event.data}{RESET}")
