"""
Contains a parser for interpreting the user's input.

The parser supports the following commands:
- Output command (/o): Instructs the AI to generate code output.
- Update command (/u): Triggers an update of the codebase state.
- Plain text command (/p): Toggle plain text mode.
- File selector command (/fs): Toggles the file selector functionality.
- Model instruction (@<model>): Specifies the AI model to use for the interaction.
- Cost command (/c): Displays the cumulative cost of the conversation so far.

If the input does not match any known command, it is treated as a regular message.

Functions:
    parse_input(input_str: str) -> ParserOutput:
        Parses the user's input string and returns the corresponding command or message.

Classes:
    Message: Represents a regular message.
    OutputCommand: Represents an output command with an associated message.
    UpdateCommand: Represents an update command.
    ModelInstruction: Represents a model instruction with the model name and message.
    PlainTextCommand: Represents a plain text command with an associated message.
    FileSelectorCommand: Represents a file selector command.
    CostCommand: Represents a command to display the cumulative cost of the conversation.
    Error: Represents an error with an error message.
"""

from dataclasses import dataclass
from typing import Optional, Union

# List of known models
KNOWN_MODELS = ["gpt-4o", "gpt-3.5", "haiku", "sonnet", "opus"]

# Data classes

@dataclass
class AbstractMessage:
    message: str

@dataclass
class Message(AbstractMessage):
    """Represents a regular message."""

    pass


@dataclass
class OutputCommand(AbstractMessage):
    """Represents an output command with an associated message."""

    pass


@dataclass
class PlainTextCommand:
    """Represents a command to toggle plain text mode."""

    pass


@dataclass
class UpdateCommand:
    """Represents an update command."""

    pass


@dataclass
class ModelInstruction:
    """Represents a model instruction with the model name and message."""

    model_name: str
    message: Optional[Message] = None


@dataclass
class FileSelectorCommand:
    """Represents a file selector command."""

    pass


@dataclass
class CostCommand:
    """Represents a command to display the cumulative cost of the conversation."""

    pass


@dataclass
class QuitCommand:
    """Represents a command to quit the program."""

    pass


@dataclass
class ResetCommand:
    """Represents a command to reset the conversation history."""

    pass


@dataclass
class ParseError:
    """Represents an error with an error message."""

    error_message: str

@dataclass
class EmptyInput:
    """Represents an empty input."""

    pass

CommandType = Union[
    OutputCommand,
    UpdateCommand,
    ModelInstruction,
    PlainTextCommand,
    FileSelectorCommand,
    CostCommand,
    QuitCommand,
    ResetCommand,
    Message,
    EmptyInput
]
ParserOutput = Union[CommandType, ParseError]


# Parser function
def parse_input(input_str: str) -> ParserOutput:
    """
    Parse the user's input string and return the corresponding command or message.

    Args:
        input_str (str): The user's input string to parse.

    Returns:
        ParserOutput: The parsed command or message, or an error if the input is invalid.
    """
    input_str = input_str.strip()

    # Check for empty input
    if input_str == "":
        return EmptyInput()

    # Check for output command
    if input_str.lower().startswith("/o "):
        message_content = input_str[3:].strip()
        return OutputCommand(message=message_content)

    # Check for update command
    elif input_str.lower().startswith("/u"):
        return UpdateCommand()

    # Check for plain text command
    elif input_str.lower().startswith("/p"):
        return PlainTextCommand()

    # Check for file selector command
    elif input_str.lower().startswith("/fs"):
        return FileSelectorCommand()

    # Check for cost command
    elif input_str.lower().startswith("/c"):
        return CostCommand()

    # Check for quit command
    elif input_str.lower().startswith("/q"):
        return QuitCommand()

    # Check for reset command
    elif input_str.lower().startswith("/r"):
        return ResetCommand()

    # Check for model instruction
    elif input_str.lower().startswith("@"):
        parts = input_str.split(" ", 1)
        model_name = parts[0][1:].lower()
        if model_name in KNOWN_MODELS:
            if len(parts) > 1:
                message_content = parts[1].strip()
                return ModelInstruction(model_name, Message(message_content))
            else:
                return ModelInstruction(model_name, None)
        else:
            return ParseError(f"Invalid model '{model_name}'")

    # Check for invalid command
    elif input_str.startswith("/"):
        # Get the first word of the line
        first_word = input_str.split(" ", 1)[0]
        return ParseError(f"Invalid command '{first_word}'")

    # Regular message
    else:
        return Message(input_str)

    return ParseError("Invalid input")
