import os

MODEL_NAME = "openai:gpt-5.1"


def validate_api_key() -> None:
    """Validates that the OpenAI API key is set.

    Raises:
        ValueError: If OPENAI_API_KEY environment variable is not set
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set. " "Please set it to use OpenAI models.")


def get_model() -> str:
    """Returns the OpenAI model name after validating API key.

    Example:
        >>> from agile_ai_sdk.llm import openai
        >>> model = openai.get_model()
        >>> agent = Agent(model)

    Raises:
        ValueError: If OPENAI_API_KEY is not set
    """
    validate_api_key()
    return MODEL_NAME
