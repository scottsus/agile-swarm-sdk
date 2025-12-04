import logging
import os
from contextlib import contextmanager
from typing import Any

import logfire
from dotenv import load_dotenv

load_dotenv(".env")

LOGFIRE_TOKEN = os.getenv("LOGFIRE_TOKEN")

if LOGFIRE_TOKEN:
    logfire.configure(
        token=LOGFIRE_TOKEN,
        service_name="starfleet",
        environment="agile-ai-sdk",
    )

    logfire.instrument_pydantic_ai()


class Logger:
    """Logger with logfire for structured logging or fallback to standard logging."""

    def __init__(self):
        self._use_logfire = LOGFIRE_TOKEN is not None
        if not self._use_logfire:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )
            self._logger = logging.getLogger("agile-ai-sdk")

    @contextmanager
    def span(self, name: str, **kwargs: Any):
        """Create a span for tracking an operation.

        Example:
            >>> with logger.span("user.create", email="alice@example.com"):
            ...     # database operations
            ...     pass
        """
        if self._use_logfire:
            with logfire.span(name, **kwargs):
                yield
        else:
            yield

    def info(self, message: str, **kwargs: Any) -> None:
        """Log an info message."""
        if self._use_logfire:
            logfire.info(message, **kwargs)
        else:
            extra_info = ", ".join(f"{k}={v}" for k, v in kwargs.items())
            self._logger.info(f"{message} {extra_info}" if extra_info else message)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log a debug message."""
        if self._use_logfire:
            logfire.debug(message, **kwargs)
        else:
            extra_info = ", ".join(f"{k}={v}" for k, v in kwargs.items())
            self._logger.debug(f"{message} {extra_info}" if extra_info else message)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log a warning message."""
        if self._use_logfire:
            logfire.warn(message, **kwargs)
        else:
            extra_info = ", ".join(f"{k}={v}" for k, v in kwargs.items())
            self._logger.warning(f"{message} {extra_info}" if extra_info else message)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log an error message."""
        if self._use_logfire:
            logfire.error(message, **kwargs)
        else:
            extra_info = ", ".join(f"{k}={v}" for k, v in kwargs.items())
            self._logger.error(f"{message} {extra_info}" if extra_info else message)


logger = Logger()
