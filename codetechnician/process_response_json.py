"""
Provides functions for converting the text of the AI's response into appropriately robust data types.
"""

import json
from jsonschema import validate, ValidationError # type: ignore
from codetechnician.ai_response import FileData, ParseResult, ParseFailure


AI_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "files": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                    "changes": {"type": "string"}
                },
                "required": ["path", "content", "changes"]
            }
        }
    },
    "required": ["files"]
}


def process_assistant_response(response: str) -> ParseResult:
    """
    Process the assistant's response and extract the file data.

    Args:
        response (str): The assistant's response to process.

    Preconditions:
        - response is a non-empty string.

    Side effects:
        None.

    Exceptions:
        None.

    Returns:
        ParseResult:
        - If the JSON is valid and matches the expected schema, returns a list of FileData objects.
        - If the JSON is valid but does not match the expected schema, returns a JSON_SCHEMA_INVALID.
        - If the JSON is malformed, returns JSON_INVALID.
    """
    assert isinstance(response, str) and response, "response must be a non-empty string"

    try:
        data = json.loads(response)
        validate(data, AI_RESPONSE_SCHEMA)
        file_data_list = [FileData(file["path"], file["content"], file["changes"]) for file in data["files"]]
        return file_data_list
    except json.JSONDecodeError:
        return ParseFailure.JSON_INVALID
    except ValidationError:
        return ParseFailure.JSON_SCHEMA_INCORRECT


def parse_ai_responses(responses: list[str]) -> ParseResult:
    """
    Parse a series of AI responses and combine the file data.
    Assumes that the AI responses are in JSON format.

    Args:
        responses (list[str]): The list of AI responses to parse.

    Preconditions:
        - responses is a non-empty list of non-empty strings.

    Side effects:
        None.

    Exceptions:
        None.

    Returns:
        ParseResult:
        - If the JSON is valid and matches the expected schema, returns a list of FileData objects.
        - If the JSON is valid but does not match the expected schema, returns a JSON_SCHEMA_INVALID.
        - If the JSON is malformed, returns JSON_INVALID.
    """
    assert isinstance(responses, list) and responses, "responses must be a non-empty list"
    assert all(isinstance(r, str) for r in responses), "responses must be a list of strings"
    assert all(r for r in responses), "responses must be a list of non-empty strings"

    concatenated_response = "".join(responses)
    return process_assistant_response(concatenated_response)
