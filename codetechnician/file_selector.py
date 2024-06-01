"""
This module provides functionality for Retrieval Augmented Generation (RAG):
It selects files to load into the context of the AI.
"""

from dataclasses import dataclass
import os
from typing import List, Optional, Union, NewType
import json

from jsonschema import ValidationError, validate

from codetechnician.codebase_watcher import Codebase
from codetechnician.constants import ConversationHistory
from codetechnician.anthropic_interface import setup_client, prompt_ai
from codetechnician.load import load_codebase_xml_
from codetechnician.constants import haiku
from codetechnician.ai_response import UsageInfo, ChatResponse
from codetechnician.printing import console

FileRelativePath = NewType("FileRelativePath", str)

@dataclass
class MalformedResponse:
    pass

@dataclass
class FileSelection:
    files: list[FileRelativePath]
    usage_data: UsageInfo

# Represents files that the file selector specified
FileSelectorResponse = Union[FileSelection, MalformedResponse]

# Represents files to load
FileSelectionOutcome = Union[FileSelection, MalformedResponse]

RAG_SYSTEM_PROMPT = """Output only JSON, in this format: 
{
  "files": [
    "./documents/document.pdf",
    "./images/image.jpg",
    "./presentations/presentation.pptx",
    "./spreadsheets/spreadsheet.xlsx",
    "./scripts/script.py",
    "./archives/archive.zip"
  ]
}"""

def get_message_list_size(messages: ConversationHistory) -> int:
    return sum([len(message["content"]) for message in messages])

def retrieve_relevant_files(codebases: List[Codebase],  # type: ignore
                            user_message: str,
                            conversation_history: ConversationHistory) -> FileSelectorResponse: # type: ignore
    """
    Retrieves a list of relevant code files based on the user's message and conversation history.

    Args:
        codebases (List[Codebase]): The list of codebases to search for relevant files.
        user_message (str): The user's message.
        conversation_history (ConversationHistory): The history of the conversation.
        system_prompt (str): The system prompt for the AI model.

    Returns:
        FileSelectorResponse: Either a list of files and token usage information or an error message if the response is malformed.

    Side Effects:
        Interacts with an AI model (Anthropic's Haiku) to determine the relevant files.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key is None:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set.")
    
    client = setup_client(api_key)
    model = haiku

    codebase_xml = load_codebase_xml_(codebases, [])

    messages = \
        conversation_history + \
        [
            {"role": "user", 
            "content": f"""
                Here is the codebase:\n\n{codebase_xml}\n\n
                User message:\n{user_message}\n\n
                Which files from the codebase would be most relevant for answering the user's message? Provide the file paths in JSON format.
                These must be relative paths, exactly as they are listed in the provided context.
            """
            }
        ]
    
    message_list_size = get_message_list_size(messages)

    console.print(f"Message list size for file selector is: {message_list_size/1024:.2f} KB")

    response: Optional[ChatResponse] = prompt_ai(client, model, messages, RAG_SYSTEM_PROMPT)

    if response is None:
        console.print("No response from the AI")
        return MalformedResponse()
    
    json_data = response.content_string.strip()

    if validate_json_schema(json_data):
        parse_output = parse_json_response(json_data) 
        if isinstance(parse_output, list):
            return FileSelection(files=parse_output, usage_data=response.usage)
        else:
            assert isinstance(parse_output, MalformedResponse)
            console.print(f"Malformed response failed parsing:\n{json_data}")
            return parse_output
    else:
        console.print(f"Malformed response failed schema validation:\n{json_data}")
        return MalformedResponse()


def validate_json_schema(json_data: str) -> bool:
    """
    Validates the JSON data against the expected schema.

    Args:
        json_data (str): The JSON data to validate.

    Returns:
        bool: True if the JSON data matches the schema, False otherwise.
    """
    schema = {
        "type": "object",
        "properties": {
            "files": {
                "type": "array",
                "items": {"type": "string"}
            }
        },
        "required": ["files"]
    }

    try:
        data = json.loads(json_data)
        validate(data, schema)
        console.print(f"Passed validation:\n{json_data}")
        return True
    except (json.JSONDecodeError, ValidationError):
        return False


def parse_json_response(json_data: str) -> Union[list[FileRelativePath], MalformedResponse]:
    """
    Parses the JSON response from the AI model.

    Args:
        json_data (str): The JSON data to parse.

    Returns:
        FileSelectorResponse: Either a list of relevant file paths or an error message if the response is malformed.
    """
    try:
        data = json.loads(json_data)
        # Format the file paths so that they don't differ in e.g. preceding '.'
        file_paths = [FileRelativePath(os.path.normpath(path)) for path in data["files"]]

        return file_paths
    except (json.JSONDecodeError, KeyError):
        return MalformedResponse()
