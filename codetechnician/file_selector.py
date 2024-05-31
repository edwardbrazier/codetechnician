"""
This module provides functionality for Retrieval Augmented Generation (RAG):
It selects files to load into the context of the AI.
"""

from dataclasses import dataclass
import os
from typing import List, Union, NewType
import json

from jsonschema import ValidationError, validate

from codetechnician.codebase_watcher import Codebase
from codetechnician.interact import ConversationHistory
from codetechnician.anthropic_interface import setup_client, prompt_ai
from codetechnician.load import load_codebase_xml_
from codetechnician.constants import haiku

FileRelativePath = NewType("FileRelativePath", str)

@dataclass
class MalformedResponse:
    pass

RagResponse = Union[List[FileRelativePath], MalformedResponse]

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

def retrieve_relevant_files(codebases: List[Codebase], 
                            user_message: str,
                            conversation_history: ConversationHistory) -> RagResponse:
    """
    Retrieves a list of relevant code files based on the user's message and conversation history.

    Args:
        codebases (List[Codebase]): The list of codebases to search for relevant files.
        user_message (str): The user's message.
        conversation_history (ConversationHistory): The history of the conversation.
        system_prompt (str): The system prompt for the AI model.

    Returns:
        RagResponse: Either a list of relevant file paths or an error message if the response is malformed.

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
            """
            }
        ]

    response = prompt_ai(client, model, messages, RAG_SYSTEM_PROMPT)

    if response is None:
        return MalformedResponse()
    
    json_data = response.content_string.strip()

    if validate_json_schema(json_data):
        return parse_json_response(json_data)
    else:
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
        return True
    except (json.JSONDecodeError, ValidationError):
        return False


def parse_json_response(json_data: str) -> RagResponse:
    """
    Parses the JSON response from the AI model.

    Args:
        json_data (str): The JSON data to parse.

    Returns:
        RagResponse: Either a list of relevant file paths or an error message if the response is malformed.
    """
    try:
        data = json.loads(json_data)
        file_paths = [FileRelativePath(path) for path in data["files"]]
        return file_paths
    except (json.JSONDecodeError, KeyError):
        return MalformedResponse()
