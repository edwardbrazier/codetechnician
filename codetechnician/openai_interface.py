# type: ignore
"""
This module provides functions for interacting with the OpenAI API.
"""

from typing import Optional
from openai import OpenAI
import requests

from codetechnician.parseaicode import (
    parse_ai_responses,
    CodeResponse,
    ChatResponse,
    Usage,
    sum_usages,
)
from codetechnician.printing import console


def setup_client(api_key: str):
    """
    Set up the AI client.
    """
    assert isinstance(api_key, str), "api_key must be a string"
    client = OpenAI()
    return client


def prompt_ai(
    client,
    model: str,
    messages: list[dict[str, str]],
    system_prompt: str,
) -> Optional[ChatResponse]:
    """
    Generate an AI response to the given prompt using the OpenAI API.
    This is a general-purpose interaction with the AI, not specific to code generation.

    Args:
        client: The OpenAI client instance.
        model (str): The name of the OpenAI model to use.
        messages (list[dict[str, str]]): The list of messages to send to the AI.
        system_prompt (str): The system prompt to provide to the AI.

    Preconditions:
        - client is a valid OpenAI client instance.
        - model is a valid model name supported by the OpenAI API.
        - messages is a non-empty list of message dictionaries with "role" and "content" keys.
        - system_prompt is a non-empty string.

    Side effects:
        - Sends a request to the OpenAI API.
        - Prints to the console if something goes wrong.

    Exceptions:
        - ...

    Returns:
        Optional[str]: The AI-generated response string, or None if an error occurred.
        guarantees: The returned value is either a non-empty string or None.
    """

    # The OpenAI API requires that the system prompt be included in the messages list
    messages_inc_system = [
        {"role": "system", "content": system_prompt},
        *messages,
    ]

    # try:
    response = client.chat.completions.create(
        model=model,
        max_tokens=4000,
        temperature=0,
        messages=messages_inc_system,
    )

    choices = response.choices
    content_string: str = ""

    if len(choices) == 0:
        console.print("Received an empty list of contents blocks.")
        return None
    else:
        content_block = choices[0]

        # Strip trailing whitespace from last message
        # so that if we pass it back, Anthropic will accept it
        # as an assistant message.
        content_string: str = content_block.message.content

        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens

        if content_string == "":
            console.print("Received an empty response string.")
            return None
        else:
            return ChatResponse(
                content_string=content_string,
                usage=Usage(prompt_tokens, completion_tokens),
            )


def gather_ai_code_responses(
    client,
    model: str,
    messages: list[dict[str, str]],
    system_prompt: str,
) -> Optional[CodeResponse]:
    """
    Generate a series of AI code responses to the given prompt using the OpenAI API until the stop signal is received.

    Args:
        client: The OpenAI client instance.
        model (str): The name of the AI model to use.
        messages (list[dict[str, str]]): The list of messages to send to the AI.
        system_prompt (str): The system prompt to provide to the AI.

    Preconditions:
        - client is a valid OpenAI client instance.
        - Each message must have a 'role' and 'content' key.
        - Elements in messages alternate betwen user prompts and assistant responses.
        - Message list is not empty.
        - First message is user prompt. (Last message may be either user prompt or (partial) assistant response.)

    Side effects:
        - Sends multiple requests to the OpenAI API.

    Exceptions:
        - ...

    Returns:
        Optional[ResponseContent]: A ResponseContent object containing the concatenated responses and the list of FileData objects if the responses are successfully parsed, or None if an error occurred.
        guarantees: If the program receives a response from the AI, the returned value is a ResponseContent object without any Nones inside it.
    """
    assert isinstance(model, str), "model must be a string"
    assert isinstance(messages, list), "messages must be a list"
    assert len(messages) > 0, "messages must be a non-empty list"
    assert all(
        isinstance(msg, dict) and "role" in msg and "content" in msg for msg in messages
    ), "messages must be a list of dicts with 'role' and 'content' keys"
    assert isinstance(system_prompt, str), "System prompt must be a string"

    return None
