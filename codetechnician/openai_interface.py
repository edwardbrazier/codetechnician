# type: ignore
"""
This module provides functions for interacting with the OpenAI API.
"""

from typing import Optional
from openai import OpenAI

from codetechnician.process_response_json import (
    parse_ai_responses,
)
from codetechnician.printing import console

from codetechnician.ai_response import (
    ParseFailure,
    CodeResponse,
    ChatResponse,
    Usage,
    FileData
)


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

    responses: list[str] = []
    concatenated_responses: str = ""
    usage_tally = Usage(0, 0)
    max_turns = 10
    separator = "\n-------------------------------\n"

    for turns in range(max_turns):
        # The OpenAI API requires that the system prompt be included in the messages list
        messages_inc_system = \
            [{"role": "system", "content": system_prompt}] + messages

        print(f"Sending message list: \n{messages_inc_system}")

        # json mode always seems to start from the beginning of the 
        # json object.
        response_format: str = "json_object" if turns == 0 else "text"

        response = client.chat.completions.create(
            model=model,
            max_tokens=200,
            temperature=0,
            messages=messages_inc_system,
            response_format={"type": response_format}
        )

        choices = response.choices
        usage_tally = Usage(
            response.usage.prompt_tokens, response.usage.completion_tokens
        )

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

            if content_string == "":
                console.print("Received an empty response string.")
                return None
            
            print(f"Received response: \n{content_string}")

            responses.append(content_string)
            
            if content_block.finish_reason == "stop":       
                parse_result: ParseResult = parse_ai_responses(responses)

                if parse_result == ParseFailure.JSON_INVALID or parse_result == ParseFailure.JSON_SCHEMA_INCORRECT:
                    console.print("[bold yellow]AI response is not in the right format.[/bold yellow]")

                    return CodeResponse(
                        content_string=separator.join(responses),
                        file_data_list=[],
                        usage=usage_tally,
                    )
                elif isinstance(parse_result, list):
                    # Parsing succeeded
                    concatenated_responses = separator.join(responses)

                    response_content = CodeResponse(
                        content_string=concatenated_responses,
                        file_data_list=parse_result,
                        usage=usage_tally,
                    )
                    return response_content
            elif content_block.finish_reason == "length":
                console.print("[bold red]AI reached the token limit.[/bold red]")
                return None






                # assume incomplete response and request continuation              

                assistant_message = {  # type: ignore
                    "role": "assistant",
                    "content": content_string,
                }
                request_continuation = { 
                    "role": "user",
                    "content": """
                    Please carefully look at the previous assistant message.
                    The previous assistant message was cut off because it reached the token limit.
                    Please provide a continuation of the previous assistant message,
                    answering the question from the previous usage message.
                    Start exactly where the previous assistant message left off.
                    Only provide the continuation, not the entire previous message 
                    or any other information.
                    Only write JSON. Do not write anything other than valid JSON.
                    """,
                }

                # The last user message might have just been 'keep going'.
                # If so, remove it and just add to the last assistant message.
                if messages[-1] == request_continuation:                    
                    messages = messages[:-1]
                    messages[-1]["content"] += content_string
                    print(f"Amended last assistant message.")
                else: # last user message was substantive

                # type_of_last_message = messages[-1]["role"]

                # if type_of_last_message == "user":
                    messages = messages + [assistant_message, request_continuation]
                    print(f"Added new assistant message.")
                # else: # last message was assistant
                #     messages[-1]["content"] += content_string.rstrip()
                #     # messages = messages + [user_message]
                #     print(f"Amended last assistant message in message history.")
                #     print("Requesting more data from the model...")
    
    print("Reached turn limit.")
    return None



