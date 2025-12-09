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

### FastAPI Integration (Recommended)

Build a web backend where users can send messages and stream real-time agent events:

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import asyncio
from agile_ai_sdk import AgentTeam

app = FastAPI()
team = AgentTeam()
subscribers: list[asyncio.Queue] = []

# Broadcast all events to SSE subscribers
@team.on_any_event
async def broadcast(event):
    for queue in subscribers:
        try:
            await asyncio.wait_for(queue.put(event), timeout=1.0)
        except asyncio.TimeoutError:
            subscribers.remove(queue)

await team.start()  # Call this on app startup


@app.post("/message")
async def post_message(message: str):
    """Send a message to the agent team (non-blocking)"""
    await team.drop_message(message)
    return {"status": "queued"}


@app.get("/stream")
async def stream_events():
    """Server-Sent Events stream of all agent events"""
    queue = asyncio.Queue(maxsize=100)
    subscribers.append(queue)

    async def event_generator():
        try:
            while True:
                event = await queue.get()
                yield f"data: {event.model_dump_json()}\n\n"
        finally:
            subscribers.remove(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
```

**Frontend (React):**

```tsx
import { useState, useEffect } from "react";

function useAgentStream() {
  const [events, setEvents] = useState([]);

  useEffect(() => {
    const eventSource = new EventSource("/stream");

    eventSource.onmessage = (e) => {
      const event = JSON.parse(e.data);
      setEvents((prev) => [...prev, event]);
    };

    return () => eventSource.close();
  }, []);

  const sendMessage = async (message: string) => {
    await fetch("/message", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
  };

  return { events, sendMessage };
}

function AgentChat() {
  const { events, sendMessage } = useAgentStream();
  const [input, setInput] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(input);
    setInput("");
  };

  return (
    <div>
      <div className="events">
        {events.map((event, i) => (
          <div key={i}>
            [{event.agent}] {event.type}
          </div>
        ))}
      </div>
      <form onSubmit={handleSubmit}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Send a message to the agent team..."
        />
        <button type="submit">Send</button>
      </form>
    </div>
  );
}
```

### TUI Version

```bash
# Run like claude code
agile-ai

# Or use the shorthand
agi
```

## Event Logging

### Log Directory Structure

All runs use the unified format `run_YYYY-MM-DD_HH:MM/`:

```
.agile/runs/run_2025-12-08_19:41/
├── metadata.json         # Run info and results
├── events.jsonl          # Event stream (one JSON per line)
├── workspace/            # Final workspace snapshot (optional)
└── journal.json          # Agent conversation history (optional)
```

### Event Stream Format

Events are logged in JSONL format (one JSON object per line):

```json
{"timestamp": "2025-12-06T14:30:22.123456Z", "type": "RUN_STARTED", "agent": "engineering_manager", "data": {"task": "Add /health endpoint"}}
{"timestamp": "2025-12-06T14:30:23.456789Z", "type": "STEP_STARTED", "agent": "developer", "data": {"step": 1}}
{"timestamp": "2025-12-06T14:30:45.789012Z", "type": "RUN_FINISHED", "agent": "engineering_manager", "data": {"result": "success"}}
```

## Contributing

This project is <1 week old, not accepting contributions atm, but lmk if it sounds interesting ✨
