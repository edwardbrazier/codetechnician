"""
Utility functions for working with strings, files, and calculating expenses.
"""

from codetechnician.ai_response import UsageInfo
from codetechnician.constants import opus, sonnet, haiku, gpt_4o, all_models


def get_size(contents: str) -> str:
    """
    Get the size of a string in kilobytes (KB) and format it as a string.

    Args:
        contents (str): The string to calculate the size for.

    Preconditions:
        - contents is a valid string

    Side effects:
        None

    Exceptions:
        None

    Returns:
        str: The size of the string in kilobytes, formatted as a string with 2 decimal places.
        guarantees: The returned value will be a non-empty string.
    """
    size = len(contents) / 1024
    return f"{size:.2f} KB"


def calculate_cost(usage_info: UsageInfo) -> float:
    """
    Calculate the cost of a message based on the token usage and model name.

    Args:
        usage_info (UsageInfo): The usage info for the message.

    Preconditions:
        - usage_info is a valid UsageInfo object.

    Side effects:
        None

    Exceptions:
        None

    Returns:
        float: The cost of the message in USD.
        guarantees: The returned value will be a non-negative float.
    """
    assert isinstance(usage_info, UsageInfo), "usage_info must be a UsageInfo object"
    assert usage_info.model_name in all_models, "model_name must be one from constants.all_models"

    usage = usage_info.usage
    model_name = usage_info.model_name

    pricing = {haiku: (0.25, 1.25), sonnet: (3.0, 15.0), opus: (15.0, 75.0), gpt_4o: (5.0, 15.0) }

    input_cost_per_million, output_cost_per_million = pricing[model_name]

    input_cost = usage.input_tokens * input_cost_per_million / 1_000_000
    output_cost = usage.output_tokens * output_cost_per_million / 1_000_000

    total_cost = input_cost + output_cost
    return total_cost


def format_cost(usage_info: UsageInfo) -> str:
    """
    Format the cost and token usage into a colored string.

    Args:
        usage_info (UsageInfo): The token usage for the message.

    Preconditions:
        - usage_info is a valid UsageInfo object.

    Side effects:
        None

    Exceptions:
        None

    Returns:
        str: The formatted cost string.
        guarantees: The returned value will be a non-empty string.
    """
    assert isinstance(usage_info, UsageInfo), "usage_info must be a UsageInfo object"

    cost = calculate_cost(usage_info)
    usage = usage_info.usage
    return f"[bold green]Tokens used in this message:[/bold green] Input - {usage.input_tokens}; Output - {usage.output_tokens} [bold green]Cost:[/bold green] ${cost:.4f} USD"
