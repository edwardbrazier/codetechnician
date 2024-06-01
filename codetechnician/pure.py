"""
Utility functions for working with strings, files, and calculating expenses.
"""

from typing import Optional
from codetechnician.ai_response import UsageInfo, Usage
from codetechnician.constants import opus, sonnet, haiku, gpt_4o, model_mapping, all_models


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

    # assert isinstance(usage, Usage)

    input_cost = usage_info.usage.input_tokens * input_cost_per_million / 1_000_000
    output_cost = usage_info.usage.output_tokens * output_cost_per_million / 1_000_000

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
    return  f"[bold green]Tokens used in this message:[/bold green] " + \
            f"Input - {usage.input_tokens}; " + \
            f"Output - {usage.output_tokens} [bold green] " + \
            f"Cost:[/bold green] ${cost:.4f} USD " + \
            f"([white not bold]{usage_info.model_name})[/white not bold]"

def get_model_long_name(model_short_name: str) -> Optional[str]:
    """
    Get the long name of a model from its short name.

    Args:
        model_short_name (str): The short name of the model (e.g., "haiku", "sonnet", "opus").

    Preconditions:
        - model_short_name is a string

    Side effects:
        None

    Exceptions:
        None

    Returns:
        Optional[str]: The long name of the model if it exists, otherwise None.
        guarantees: The returned value will be a non-None string.
    """
    assert isinstance(model_short_name,str)
    
    if model_short_name in model_mapping.keys():
        return model_mapping.get(model_short_name)
    else:
        return None