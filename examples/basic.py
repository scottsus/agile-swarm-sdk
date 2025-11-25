import asyncio

from agile_ai_sdk import AgentTeam, EventType, print_event


async def main():
    """Run a simple task with the agent team."""

    team = AgentTeam()

    async for event in team.execute("Add a /health endpoint to my FastAPI app"):
        print_event(event)

        if event.type in (EventType.RUN_FINISHED, EventType.RUN_ERROR):
            break


if __name__ == "__main__":
    asyncio.run(main())
