"""
Constructs for representing the response from the AI.
"""

from enum import Enum
from typing import NamedTuple, Union

class FileData(NamedTuple):
    """
    Represents the data of the files from the AI's response.
    """

    relative_path: str
    contents: str
    changes: str

class ParseFailure(Enum):
    JSON_INVALID = 1
    JSON_SCHEMA_INCORRECT = 2

# Represents the result from attempting to parse a code response from the AI.
# If the ParseResult is None, this means that the output was not valid, 
# which may be because the output was incomplete.
# If the ParseResult equals [], then the output was valid but did not contain 
# data about any files.
ParseResult = Union[ParseFailure, list[FileData]]


class Usage(NamedTuple):
    """
    Represents the number of tokens used by the model for the input and output.
    """

    input_tokens: int
    output_tokens: int

    def __repr__(self):
        return f"Input - {self.input_tokens}; Output - {self.output_tokens}"


def sum_usages(u1: Usage, u2: Usage):
    """
    Overload the + operator to add two Usage tallies.
    """
    assert isinstance(u1, Usage) and isinstance(
        u2, Usage
    ), "Both arguments must be Usage objects"
    return Usage(u1.input_tokens + u2.input_tokens, u1.output_tokens + u2.output_tokens)


class CodeResponse(NamedTuple):
    """
    Represents the response from the AI for a code prompt.
    """

    content_string: str
    file_data_list: list[FileData]
    usage: Usage


class ChatResponse(NamedTuple):
    """
    Represents the response from the AI for a chat prompt.
    """

    content_string: str
    usage: Usage