from pathlib import Path

from pydantic_ai import Agent

from agile_ai_sdk.llm import default
from agile_ai_sdk.models import Event, EventType
from tests.types.evaluations import CodeQualityEvaluation, TaskEvaluation


class LLMJudge:
    """LLM-based evaluation of task completion and code quality.

    This judge uses an LLM to semantically evaluate whether coding tasks
    were completed successfully, providing more robust validation than
    brittle keyword matching or regex patterns.

    Example:
        >>> judge = LLMJudge()
        >>> evaluation = await judge.evaluate_task_completion(
        ...     task="Add a multiply function",
        ...     events=event_collector.events,
        ...     workspace_dir=Path("/tmp/workspace")
        ... )
        >>> assert evaluation.task_completed
        >>> assert evaluation.confidence > 0.8
    """

    def __init__(self):
        """Initialize LLM judge."""

        self.model = "claude-sonnet-4"
        self.agent = Agent(
            default.get_model(),
            output_type=TaskEvaluation,
            system_prompt=self._get_system_prompt(),
        )

    def _get_system_prompt(self) -> str:
        """Get system prompt for judge."""

        return """You are an expert code reviewer evaluating software development tasks.
Your role is to objectively assess whether tasks were completed successfully.
Be precise, fair, and thorough in your evaluations."""

    async def evaluate_task_completion(
        self,
        task: str,
        events: list[Event],
        workspace_dir: Path,
    ) -> TaskEvaluation:
        """Evaluate whether a task was successfully completed.

        This method analyzes the event stream and workspace state to determine
        if the given task was accomplished. It considers what the agent did,
        what errors occurred, test results from the events, and the final code.

        Args:
            task: Original task description (e.g., "Add a multiply function")
            events: List of events from the agent execution
            workspace_dir: Path to workspace with code changes

        Returns:
            TaskEvaluation with completion status, confidence, and reasoning

        Example:
            >>> judge = LLMJudge()
            >>> result = await judge.evaluate_task_completion(
            ...     task="Create a hello world function",
            ...     events=event_collector.events,
            ...     workspace_dir=Path("/tmp/test-workspace")
            ... )
            >>> if result.task_completed:
            ...     print(f"Task completed with {result.confidence:.0%} confidence")
            ... else:
            ...     print(f"Issues found: {result.issues_found}")
        """

        file_tree = self._get_file_tree(workspace_dir)
        file_contents = self._get_key_files(workspace_dir)
        event_summary = self._extract_event_summary(events)

        prompt = f"""Evaluate whether this task was completed successfully:

            Task: {task}

            Agent execution summary:
            {event_summary}

            Workspace structure:
            {file_tree}

            Key files:
            {file_contents}

            Consider:
            1. Does the code accomplish the stated task?
            2. Did the agent take a reasonable approach? (from events)
            3. Did the agent handle errors properly? (from events)
            4. Did tests pass? (extract from events if available)
            5. Is the implementation reasonable and correct?
            6. Are there obvious bugs or issues?

            Provide your evaluation with:
            - task_completed: true/false
            - confidence: 0.0-1.0 (how confident are you?)
            - reasoning: detailed explanation
            - issues_found: list of any problems
            - suggestions: optional improvements
        """

        result = await self.agent.run(prompt)
        return result.output

    async def evaluate_code_quality(self, files: list[Path], criteria: list[str]) -> CodeQualityEvaluation:
        """Evaluate code quality against specific criteria.

        This method checks if the provided files meet the given quality
        criteria, such as "has docstrings", "follows naming conventions",
        or "includes error handling".

        Args:
            files: List of file paths to evaluate
            criteria: List of quality criteria to check

        Returns:
            CodeQualityEvaluation with pass/fail per criterion

        Example:
            >>> judge = LLMJudge()
            >>> result = await judge.evaluate_code_quality(
            ...     files=[Path("src/main.py")],
            ...     criteria=["has docstrings", "includes type hints"]
            ... )
            >>> if result.passes:
            ...     print("All criteria met!")
            ... else:
            ...     print(f"Failed criteria: {result.issues}")
        """

        file_contents_str = "\n\n".join(f"File: {f.name}\n```\n{f.read_text()}\n```" for f in files)

        criteria_str = "\n".join(f"- {c}" for c in criteria)

        prompt = f"""Evaluate code quality:

            Files:
            {file_contents_str}

            Criteria:
            {criteria_str}

            For each criterion, determine if the code meets it.
            Provide overall pass/fail, detailed reasoning, and any issues found.
        """

        agent = Agent(
            default.get_model(),
            output_type=CodeQualityEvaluation,
            system_prompt=self._get_system_prompt(),
        )

        result = await agent.run(prompt)
        return result.output

    def _extract_event_summary(self, events: list[Event]) -> str:
        """Extract a concise summary of events for LLM evaluation.

        This method:
        1. extracts key events (tool calls, errors, test results)
        2. formats them into a readable summary
        3. keeps the summary concise but informative
        """

        summary_parts = []

        tool_calls = [e for e in events if e.type == EventType.TOOL_CALL_START]
        if tool_calls:
            summary_parts.append("Tools used:")
            for event in tool_calls[:10]:
                tool_name = event.data.get("tool_name", "unknown")
                summary_parts.append(f"  - {tool_name}")
            if len(tool_calls) > 10:
                summary_parts.append(f"  ... and {len(tool_calls) - 10} more")

        errors = [e for e in events if e.type == EventType.RUN_ERROR]
        if errors:
            summary_parts.append("\nErrors encountered:")
            for event in errors[:5]:
                error_msg = event.data.get("error", "Unknown error")
                summary_parts.append(f"  - {error_msg[:200]}")

        tool_results = [e for e in events if e.type == EventType.TOOL_CALL_RESULT]
        test_results = []
        for event in tool_results:
            result_data = event.data.get("result", {})
            if isinstance(result_data, dict):
                stdout = result_data.get("stdout", "")
                stderr = result_data.get("stderr", "")
                if "pytest" in stdout or "test" in stdout.lower():
                    test_results.append((result_data.get("returncode", -1), stdout, stderr))

        if test_results:
            summary_parts.append("\nTest execution results:")
            for returncode, stdout, stderr in test_results[:3]:
                status = "PASSED" if returncode == 0 else "FAILED"
                summary_parts.append(f"  Status: {status}")
                if stdout:
                    stdout_preview = stdout[:500]
                    summary_parts.append(f"  Output: {stdout_preview}")
                if stderr and returncode != 0:
                    stderr_preview = stderr[:300]
                    summary_parts.append(f"  Errors: {stderr_preview}")

        text_messages = [e for e in events if e.type == EventType.TEXT_MESSAGE_CONTENT]
        if text_messages:
            summary_parts.append("\nAgent reasoning (sample):")
            for event in text_messages[:5]:
                content = event.data.get("content", "")
                if content and len(content) > 20:
                    summary_parts.append(f"  - {content[:150]}")

        if not summary_parts:
            return "No significant events captured"

        return "\n".join(summary_parts)

    def _get_file_tree(self, workspace_dir: Path) -> str:
        """Get file tree as string."""
        lines = []
        for path in sorted(workspace_dir.rglob("*")):
            if path.is_file() and not self._should_ignore(path):
                rel_path = path.relative_to(workspace_dir)
                indent = "  " * (len(rel_path.parts) - 1)
                lines.append(f"{indent}- {rel_path.name}")
        return "\n".join(lines)

    def _get_key_files(self, workspace_dir: Path, max_files: int = 10) -> dict[str, str]:
        """Get key file contents."""
        files = {}
        python_files = list(workspace_dir.rglob("*.py"))[:max_files]

        for file_path in python_files:
            if not self._should_ignore(file_path):
                rel_path = file_path.relative_to(workspace_dir)
                try:
                    content = file_path.read_text()
                    files[str(rel_path)] = content[:2000]
                except Exception:
                    pass

        return files

    def _should_ignore(self, path: Path) -> bool:
        """Check if path should be ignored."""
        ignore_patterns = ["__pycache__", ".pyc", ".git", ".pytest_cache"]
        return any(pattern in str(path) for pattern in ignore_patterns)
