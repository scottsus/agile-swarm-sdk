# Agile AI SDK

SDK for autonomous AI engineering teams in agile workflows.

Just a side project still under construction 🏗️ but feel free to poke around.

## Vision

Question: Would AI agents be more effective in a typical agile setting?

We explore whether imposing human-like constraints (agile ceremonies, defined roles, review processes) makes AI agent teams
more, or less, effective at complex, multi-step tasks.

If this really works, it might just justify all the bureaucracy in big tech companies.

## Features

- 🤖 **Multi-Agent System**: EM, Planner, Developer, and Senior Reviewer agents
- 🔄 **Async-Native**: Fire-and-forget execution with event streaming
- 📦 **Pure Library**: Lightweight wrapper over Pydantic AI
- 🎯 **Agent Autonomy**: Persistent agents with self-managing context
- 🔧 **Flexible**: Use programmatically or via TUI

## Installation

```bash
# Minimal (library only)
pip install agile-ai-sdk

# With TUI
pip install agile-ai-sdk[tui]

# Don't be stingy it won't cost a few $
export ANTHROPIC_API_KEY="sk-ant-..."
```

## Quick Start

### SDK Version

```python
from agile_ai import AgentTeam
import asyncio

async def main():
    team = AgentTeam()

    async for event in team.execute("Add a /health endpoint to my FastAPI app"):
        print(f"[{event.agent}] {event.type}: {event.data}")

        if event.type == "task.completed":
            print(f"✅ Done! PR: {event.data['pr_url']}")
            break

asyncio.run(main())
```

### TUI version

```bash
# run like claude code
agile-ai

# or use the shorthand
agi
```

## Contributing

This project is <1 week old, not accepting contributions atm, but lmk if it sounds interesting ✨
