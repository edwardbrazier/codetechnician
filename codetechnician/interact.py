#!/bin/env python
"""
This script provides an interactive command-line interface for interacting with the Anthropic AI API.
It allows users to send prompts and receive responses from the AI model.
"""

from enum import Enum
import logging
# import sys

from prompt_toolkit import HTML, PromptSession
from typing import Optional, Union
from rich.logging import RichHandler

from codetechnician.printing import print_markdown, console
from codetechnician.constants import (
    # coder_system_prompt_hardcoded_claude,
    # coder_system_prompt_hardcoded_gpt,
    anthropic_models_long,
    openai_models_long,
    ConversationHistory
)
# from codetechnician import save
from codetechnician import openai_interface
# from codetechnician import anthropic_interface
from codetechnician.ai_response import ChatResponse, UsageInfo #  CodeResponse, 
from codetechnician.pure import format_cost
from codetechnician.codebase_watcher import (
    Codebase,
    CodebaseUpdates,
    # CodebaseState,
    # find_codebase_change_contents,
    # num_affected_files,
)
from codetechnician.file_selector import FileSelectorResponse, FileRelativePath, MalformedResponse, FileSelection, retrieve_relevant_files
from codetechnician.load import load_file_xml

logger = logging.getLogger("rich")

logging.basicConfig(
    level="WARNING",
    format="%(message)s",
    handlers=[
        RichHandler(show_time=False, show_level=False, show_path=False, markup=True)  # type: ignore
    ],
)

class UserPromptOutcome(Enum):
    CONTINUE = 1
    STOP = 0

PromptOutcome = Union[ConversationHistory, UserPromptOutcome, CodebaseUpdates]


def prompt_user(
    client,  # type: ignore
    codebase_contents: Optional[str],
    conversation_history: ConversationHistory,
    session: PromptSession[str],
    config: dict,  # type: ignore
    output_dir_notnone: str,
    force_overwrite: bool,
    user_system_prompt_code: str,
    system_prompt_general: str,
    codebases: list[Codebase],
    file_extensions: list[str],
) -> PromptOutcome:
    """
    Ask the user for input, build the request and perform it.

    Args:
        client: The client instance.
        context (Optional[str]): The XML representation of the codebase or changes to the codebase, if provided.
        conversation_history (ConversationHistory): The history of the conversation so far.
        session (PromptSession): The prompt session object for interactive input.
        config (dict): The configuration dictionary containing settings for the API request.
        output_dir_notnone (str): The output directory for generated files when using the /o command.
        force_overwrite (bool): Whether to force overwrite of output files if they already exist.
        user_system_prompt_code (str): The user's part of the system prompt to use for code generation,
                                    additional to the hardcoded coder system prompt.
        system_prompt_general (str): The system prompt to use for general conversation.
        codebases (list[Codebase]): A list of Codebases being watched.
        file_extensions (list[str]): A list of file extensions to watch for in the codebases.

    Preconditions:
        - The `conversation_history` list is initialized and contains the conversation history.
        - The `console` object is initialized for logging and output.
        - The conversation history does not contain more than one User message in a row
            or more than one Assistant message in a row, and it ends with an Assistant message if
            it is not empty.
        - If there is a codebase_xml, then conversation_history is empty.
        - If the model is an OpenAI model, then the client is an OpenAI client.
        - If the model is an Anthropic model, then the client is an Anthropic client.

    Side effects:
        - Modifies the `conversation_history` list by appending new messages from the user and the AI model.
        - Prints the AI model's response to the console.
        - Writes generated files to the output directory when using the /o command.

    Exceptions:
        - EOFError: Raised when the user enters "/q" to quit the program.
        - KeyboardInterrupt: Raised when the user enters an empty prompt or when certain errors occur during the API request.

    Returns:
        None
    """
    user_entry: str = ""

    model: str = config["model"]  # type: ignore

    user_entry = session.prompt(HTML(f"<b> >>> </b>"))

    if user_entry.lower().strip() == "/q":
        return UserPromptOutcome.STOP
    if user_entry.lower() == "":
        return UserPromptOutcome.CONTINUE

    render_markdown: bool = True
    user_instruction: str = user_entry

    # if user_entry.lower().strip().startswith("/p"):
    #     render_markdown = False
    #     user_instruction = (user_entry.strip())[2:].strip()

    # if user_entry.lower().strip() == "/u":
    #     codebase_locations: list[str] = [codebase.location for codebase in codebases]
    #     codebase_states: list[CodebaseState] = [
    #         codebase.state for codebase in codebases
    #     ]
    #     codebase_updates: CodebaseUpdates = find_codebase_change_contents(
    #         codebase_locations, file_extensions, codebase_states
    #     )

    #     if num_affected_files(codebase_updates) == 0:
    #         console.print("No changes were identified in the codebase.")
    #     else:
    #         console.print(codebase_updates.change_descriptive.change_descriptions)
    #         console.print(
    #             "Details of the changes will be prepended to your next message to the AI."
    #         )

        # return codebase_updates

    # There are two cases:
    # One is that the user wants the AI to talk to them.
    # The other is that the user wants the AI to send code to some files.

    # The user wants the AI to output code to files
    # if user_entry.lower().strip().startswith("/o"):
    #     # Remove the "/o" from the message
    #     user_instruction = (user_entry.strip())[2:].strip()

    #     console.print(f"Asking file selection AI for a list of relevant files.")
    #     selector_response: FileSelectorResponse = retrieve_relevant_files(codebases, user_instruction, conversation_history) # type: ignore
    #     relevant_files: list[FileRelativePath] = []

    #     if isinstance(selector_response, MalformedResponse):
    #         console.print("Malformed response from file selector.")
    #     else:
    #         assert isinstance(selector_response, FileSelection)
    #         relevant_files = selector_response.files
    #         console.print(f"[bold green]Relevant files:[/bold green]")
    #         for file_path in relevant_files:
    #             console.print(f"- {file_path}")
    #         console.print(format_cost(selector_response.usage_data))

    #     context: Optional[str] = None

    #     if len(relevant_files) > 0:
    #         try:
    #             console.print("Loading relevant files...")
    #             context = "Here are the relevant files from the codebase. Read them carefully.\n\n"
    #             for file_path in relevant_files:
    #                 file_contents = load_file_xml(file_path)
    #                 if file_contents:
    #                     context += file_contents + "\n\n"
    #                 else:
    #                     console.print(f"[yellow]Skipping file {file_path} due to loading issues.[/yellow]")
    #         except Exception as e:
    #             console.print(f"[red]Error loading relevant files: {e}[/red]")
    #             console.print("Using content from all files from all specified codebases.")
    #             context = (
    #                 "Here is a codebase. Read it carefully.\n\n"
    #                 "\n\nCodebase:\n" + codebase_initial_contents + "\n\n"
    #             )
    #     else:
    #         console.print("Using content from all files from all specified codebases.")
    #         context = (
    #             "Here is a codebase. Read it carefully.\n\n"
    #             "\n\nCodebase:\n" + codebase_initial_contents + "\n\n"
    #         )

    #     # The Anthropic documentation says that Claude performs better when
    #     # the input data comes first and the instructions come last.
    #     new_messages: list[dict[str, str]] = [
    #         {
    #             "role": "user",
    #             # The following is still ok if context_data is empty,
    #             # which should happen if it's not the first turn of
    #             # the conversation.
    #             "content": context
    #             + user_instruction
    #             + "\nAlways provide a change description!",
    #         },
    #     ]

    #     messages = conversation_history + new_messages

    #     if model in anthropic_models_long:
    #         response_content: Optional[CodeResponse] = anthropic_interface.gather_ai_code_responses(client, model, messages, coder_system_prompt_hardcoded_claude + user_system_prompt_code)  # type: ignore
    #     elif model in openai_models_long:
    #         response_content: Optional[CodeResponse] = openai_interface.gather_ai_code_responses(client, model, messages, coder_system_prompt_hardcoded_gpt + user_system_prompt_code)  # type: ignore
    #     else:
    #         console.print(f"[bold red]Unsupported model: {model}[/bold red]")
    #         return UserPromptOutcome.CONTINUE

    #     if response_content is None:
    #         console.print("[bold red]Failed to get a response from the AI.[/bold red]")
    #         return UserPromptOutcome.CONTINUE
    #     else:
    #         try:
    #             save.save_ai_output(response_content, output_dir_notnone, force_overwrite)  # type: ignore
    #             console.print("[bold green]Finished saving AI output.[/bold green]")
    #         except Exception as e:
    #             console.print(f"[bold red]Error processing AI response: {e}[/bold red]")

    #         # Remove dummy assistant message from end of conversation history
    #         conversation_ = messages[:-1]
    #         # Add assistant message onto the conversation history
    #         conversation_contents = conversation_ + [
    #             {"role": "assistant", "content": response_content.content_string}  # type: ignore
    #         ]

    #         console.print(format_cost(response_content.usage, model))  # type: ignore

    #         return conversation_contents
    # else:
    if True:
        # User is conversing with AI.
        user_prompt: str = user_instruction

        console.print(f"Asking file selector AI for a list of relevant files.")
        selector_response: FileSelectorResponse = retrieve_relevant_files(codebases, user_prompt, conversation_history) # type: ignore
        relevant_files: list[FileRelativePath] = []

        if isinstance(selector_response, MalformedResponse):
            console.print("Malformed response from file selector.")
        else:
            assert isinstance(selector_response, FileSelection)
            relevant_files = selector_response.files
            console.print(f"[bold green]Relevant files:[/bold green]")
            for file_path in relevant_files:
                console.print(f"- {file_path}")
            console.print(format_cost(selector_response.usage_data))

        context: Optional[str] = None

        full_codebase_context: Optional[str]
        
        if codebase_contents is not None:
            full_codebase_context = (
                    "Here is a codebase. Read it carefully.\n\n"
                    "\n\nCodebase:\n" + codebase_contents + "\n\n"
                )
        else:
            full_codebase_context = None

        if len(relevant_files) > 0:
            try:
                console.print("Loading relevant files...")
                context = "Here are the relevant files from the codebase. Read them carefully.\n\n"
                for file_path in relevant_files:
                    file_contents = load_file_xml(file_path)
                    if file_contents:
                        context += file_contents + "\n\n"
                    else:
                        console.print(f"[yellow]Skipping file {file_path} due to loading issues.[/yellow]")
                console.print("Finished loading relevant files.")
            except Exception as e:
                console.print(f"[red]Error loading relevant files: {e}[/red]")
                console.print("Using content from all files from all specified codebases.")
                context = full_codebase_context
        else:
            console.print("Using content from all files from all specified codebases.")
            context = full_codebase_context

        new_messages: list[dict[str, str]]

        if context is not None:
            new_messages = [
                    {"role": "user", "content": context + user_prompt}
                ]
        else:
            new_messages = [
                    {"role": "user", "content": user_prompt}
                ]

        messages = conversation_history + new_messages
        chat_response_optional: Optional[ChatResponse] = None

        if model in anthropic_models_long:
            chat_response_optional = None
            # chat_response_optional = anthropic_interface.prompt_ai(client, model, messages, system_prompt_general)  # type: ignore
        elif model in openai_models_long:
            chat_response_optional = openai_interface.prompt_ai(client, model, messages, system_prompt_general)  # type: ignore
        else:
            console.print(f"[bold red]Unsupported model: {model}[/bold red]")
            return UserPromptOutcome.CONTINUE

        if chat_response_optional is None:
            console.print("[bold red]Failed to get a response from the AI.[/bold red]")
            return UserPromptOutcome.CONTINUE
        else:
            if render_markdown:
                print_markdown(console, chat_response_optional.content_string)  # type: ignore
            else:
                console.print(chat_response_optional.content_string)  # type: ignore

            response_string = chat_response_optional.content_string  # type: ignore
            usage = chat_response_optional.usage  # type: ignore
            console.print(format_cost(UsageInfo(usage, model)))  # type: ignore
            chat_history = messages + [
                {"role": "assistant", "content": response_string}
            ]
            return chat_history
