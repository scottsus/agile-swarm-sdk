from agile_ai_sdk.llm import anthropic


def get_model() -> str:
    """Returns the default model for the SDK.

    Currently defaults to Anthropic Claude Sonnet 4.0.

    Example:
        >>> from agile_ai_sdk.llm import default
        >>> agent = Agent(default.get_model())

    Raises:
        ValueError: If the default model's API key is not set
    """
    return anthropic.get_model()
