import os

MODEL_NAME = "anthropic:claude-sonnet-4-5"


def validate_api_key() -> None:
    """Validates that the Anthropic API key is set.

    Raises:
        ValueError: If ANTHROPIC_API_KEY environment variable is not set
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is not set. " "Please set it to use Anthropic models.")


def get_model() -> str:
    """Returns the Anthropic model name after validating API key.

    Example:
        >>> from agile_ai_sdk.llm import anthropic
        >>> model = anthropic.get_model()
        >>> agent = Agent(model)

    Raises:
        ValueError: If ANTHROPIC_API_KEY is not set
    """
    validate_api_key()
    return MODEL_NAME
