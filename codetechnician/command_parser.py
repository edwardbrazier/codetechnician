"""
Contains a parser for interpreting the user's input.
TODO: Needs more docstrings.
"""

from dataclasses import dataclass
from typing import Union

# List of known models
KNOWN_MODELS = ["gpt-4o", "gpt-3.5", "haiku", "sonnet", "opus"]

# Data classes
@dataclass
class Message:
    content: str

@dataclass
class OutputCommand:
    message: Message

@dataclass
class UpdateCommand:
    pass

@dataclass
class ModelInstruction:
    model_name: str
    message: Message

@dataclass
class PlainTextCommand:
    message: Message

@dataclass
class Error:
    error_message: str

CommandType = Union[OutputCommand, UpdateCommand, ModelInstruction, PlainTextCommand, Message]
ParserOutput = Union[CommandType, Error]

# Parser function
def parse_input(input_str: str) -> ParserOutput:
    input_str = input_str.strip()

    # Check for output command
    if input_str.lower().startswith("/o "):
        message_content = input_str[3:].strip()
        return OutputCommand(Message(message_content))

    # Check for update command
    elif input_str.lower().startswith("/u"):
        return UpdateCommand()

    # Check for plain text command
    elif input_str.lower().startswith("/p"):
        message_content = input_str[3:].strip()
        return PlainTextCommand(Message(message_content))

    # Check for model instruction
    elif input_str.lower().startswith("@"): 
        parts = input_str.split(" ", 1)
        model_name = parts[0][1:].lower()
        if model_name in KNOWN_MODELS:
            if len(parts) > 1:
                message_content = parts[1].strip()
                return ModelInstruction(model_name, Message(message_content))
            else:
                return Error("Missing message for model instruction")
        else:
            return Error(f"Invalid model '{model_name}'")

    # Check for invalid command
    elif input_str.startswith("/"):
        # Get the first word of the line
        first_word = input_str.split(" ", 1)[0]
        return Error(f"Invalid command '{first_word}'")

    # Regular message
    else:
        return Message(input_str)

    return Error("Invalid input")