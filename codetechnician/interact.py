#!/bin/env python
"""
This script provides an interactive command-line interface for interacting with the Anthropic AI API.
It allows users to send prompts and receive responses from the AI model.
"""

from dataclasses import dataclass, replace
# from enum import Enum
# import sys

from prompt_toolkit import HTML, PromptSession
from typing import Callable, Optional, Union

from codetechnician.printing import print_markdown, console
from codetechnician.constants import (
    # coder_system_prompt_hardcoded_claude,
    # coder_system_prompt_hardcoded_gpt,
    anthropic_models_long,
    openai_models_long,
    ConversationHistory,
    all_models,
)
# from codetechnician import save
from codetechnician import openai_interface
from codetechnician import anthropic_interface
from codetechnician.ai_response import ChatResponse, UsageInfo #  CodeResponse, 
from codetechnician.pure import format_cost, get_model_long_name
from codetechnician.codebase_watcher import (
    Codebase,
    # CodebaseUpdates,
    # CodebaseState,
    # find_codebase_change_contents,
    # num_affected_files,
)
from codetechnician.file_selector import FileSelectorResponse, FileRelativePath, MalformedResponse, FileSelection, retrieve_relevant_files
from codetechnician.load import load_file_xml
from codetechnician.command_parser import (parse_input, Message, OutputCommand, UpdateCommand, ModelInstruction, PlainTextCommand, FileSelectorCommand, ParseError, CostCommand, QuitCommand, ResetCommand, EmptyInput)
from codetechnician import ai_clients

import anthropic
import openai

@dataclass
class MainLoopState:
    """
    Represents the program state at the level of the main loop.
    """
    conversation_history: ConversationHistory
    codebase_contents: Optional[str]
    main_model: str
    cumulative_cost: float
    loaded_files: set[FileRelativePath] # The files that have already been loaded into the conversation history
    file_selector_enabled: bool
    plain_text_enabled: bool

Action = Union[ParseError, QuitCommand, UpdateCommand, Message, PlainTextCommand, OutputCommand, ModelInstruction] 

@dataclass
class PromptUserOutput:
    """
    Represents the output of the prompt user function.
    Attributes:
        action (Optional[Action]): The action to take based on the user's input.
        state_mutation (Callable[[MainLoopState], MainLoopState]): A function that mutates the main loop state based on the user's input.
        update_printer (Callable[[MainLoopState], str]): Prints the updated state of the main loop.
    """
    action: Optional[Action]
    state_mutation: Callable[[MainLoopState], MainLoopState]
    update_printer: Callable[[MainLoopState], Optional[str]]

identity_state: Callable[[MainLoopState], MainLoopState] = lambda x: x
nil_printer: Callable[[MainLoopState], Optional[str]] = lambda s: None

@dataclass
class AIError:
    """
    Represents an error from the AI.
    """
    error_text: str

MessageResult = Union[ChatResponse, AIError]

def prompt_user(
    session: PromptSession[str]
) -> PromptUserOutput:
    """
    Ask the user for input, parse it, and return a command and state mutation function.

    Args:
        session (PromptSession): The prompt session object for interactive input.

    Preconditions:
        - The `session` object is initialized for user input.

    Side effects:
        - Interacts with the user via the command line prompt.

    Exceptions:
        None

    Returns:
        PromptOutcome: A PromptUserOutput containing an action, a state mutation function and a string-printer.
    """
    user_entry: str = session.prompt(HTML(f"<b> >>> </b>"))

    command = parse_input(user_entry)

    if isinstance(command, EmptyInput):
        return PromptUserOutput(None, identity_state, nil_printer)
    elif isinstance(command, ParseError):
        error_printer: Callable[[MainLoopState], Optional[str]] = lambda _: console.print(command.error_message)
        return PromptUserOutput(command, identity_state, error_printer)
    elif isinstance(command, QuitCommand):
        quit_printer: Callable[[MainLoopState], Optional[str]] = lambda _: "Exiting."
        return PromptUserOutput(command, identity_state, quit_printer)
    elif isinstance(command, UpdateCommand):
        return PromptUserOutput(command, identity_state, nil_printer)
    elif isinstance(command, CostCommand):
        cost_printer: Callable[[MainLoopState], Optional[str]] = \
            lambda s: f"Cumulative cost of conversation: [bold green]{s.cumulative_cost} USD[/bold green]"
        return PromptUserOutput(None, identity_state, cost_printer)
    elif isinstance(command, ResetCommand):
        reset_conversation: Callable[[MainLoopState], MainLoopState] = \
            lambda s: replace(s, \
                conversation_history=[],
                loaded_files=set()
            )
        reset_printer: Callable[[MainLoopState], Optional[str]] = lambda _: "Resetting conversation history."
        return PromptUserOutput(None, reset_conversation, reset_printer)
    elif isinstance(command, FileSelectorCommand):
        flip_file_selector: Callable[[MainLoopState], MainLoopState] = \
            lambda s: replace(s, \
                              file_selector_enabled=not s.file_selector_enabled
            )
        file_selector_printer: Callable[[MainLoopState], Optional[str]] = \
            lambda s: "File selector is now " + ("enabled" if s.file_selector_enabled else "disabled") + "."
        return PromptUserOutput(None, flip_file_selector, file_selector_printer)
    elif isinstance(command, ModelInstruction):
        model_short_name = command.model_name
        model_long_optional: Optional[str] = get_model_long_name(model_short_name)
        
        set_model: Callable[[MainLoopState], MainLoopState]

        if model_long_optional is not None:
            set_model = lambda s: replace(s, \
                main_model=model_long_optional
            )
            model_printer: Callable[[MainLoopState], Optional[str]] = \
                lambda s: f"Main model is now {model_short_name}"
            return PromptUserOutput(command, set_model, model_printer)
        else:
            return PromptUserOutput(ParseError("Model not found: " + model_short_name), identity_state, nil_printer)
    elif isinstance(command, PlainTextCommand):
        flip_plain_text: Callable[[MainLoopState], MainLoopState] = \
            lambda s: replace(s, \
                plain_text_enabled=not s.plain_text_enabled
            )
        plain_text_printer: Callable[[MainLoopState], Optional[str]] = \
            lambda s: "Plain text mode is now " + ("enabled" if s.plain_text_enabled else "disabled") + "."
        return PromptUserOutput(None, flip_plain_text, plain_text_printer)               
    elif isinstance(command, OutputCommand):
        return PromptUserOutput(command, identity_state, nil_printer)
    elif isinstance(command, Message): # type: ignore
        return PromptUserOutput(command, identity_state, nil_printer)
    
    return PromptUserOutput(Error, identity_state, nil_printer) # type: ignore

# def client_available(
#     clients: Clients,
#     model: str
# ) -> bool:
#     """
#     Indicates whether there is a client in the Clients object 
#     which will support the given model.
#     The model must be specified with its full name (long form).
#     """
#     assert isinstance(clients, Clients)
#     assert isinstance(model, str)
    
#     if model in anthropic_models_long:
#         if clients.anthropic is not None:
#             return True
#         else:
#             return False
#     elif model in openai_models_long:
#         if clients.openai is not None:
#             return True
#         else:
#             return False
#     else:
#         return False

def select_client(
    clients: ai_clients.Clients,
    model: str
) -> Optional[ai_clients.GenericClient]:
    """
    Returns the relevant client from the Clients object.
    """
    assert isinstance(clients, ai_clients.Clients)
    assert isinstance(model, str)

    if model in anthropic_models_long:
        return clients.anthropic
    elif model in openai_models_long:
        return clients.openai
    else:
        return None

def message_ai_no_codebase(
        clients: ai_clients.Clients,
        model: str,
        conversation_history: ConversationHistory,
        system_prompt_general: str,
        user_message: str,
) -> MessageResult:
    """
    Messages the AI, prints the result and prints the cost estimate.
    This is a wrapper around the prompt_ai() functions in anthropic_interface and openai_interface,
    but this method selects the relevant client based on the model name.

    Leaves printing the result to the console to the calling method.
    """
    assert isinstance(clients, ai_clients.Clients)
    assert isinstance(model, str)
    assert isinstance(conversation_history, list)
    assert isinstance(system_prompt_general, str)
    assert isinstance(user_message, str)
    assert (model in all_models)

    client_optional: Optional[ai_clients.GenericClient] = select_client(clients, model)
    chat_response_optional: Optional[ChatResponse] = None

    if client_optional is None:
        return AIError(f"No client available for model {model}.")
    else:
        client = client_optional

        messages = conversation_history + [
                {"role": "user", "content": user_message}
            ]

        if isinstance(client, anthropic.Client):
            chat_response_optional = anthropic_interface.prompt_ai(client, model, messages, system_prompt_general) 
        elif isinstance(client, openai.OpenAI):
            chat_response_optional = openai_interface.prompt_ai(client, model, messages, system_prompt_general)
        else:
            return AIError(f"Model {model} is not supported.")

    if chat_response_optional is None:
        return AIError(f"No response received from the AI.")
    else:
        return chat_response_optional

def print_chat_response(
    chat_response: ChatResponse
) -> None:
    """
    Prints the chat response to the console.
    """
    assert isinstance(chat_response, ChatResponse)
    
    print_markdown(console, chat_response.content_string)  # type: ignore
    usage = chat_response.usage  # type: ignore
    console.print(format_cost(usage))  # type: ignore

def message_ai(
    client,  # type: ignore
    state: MainLoopState,
    user_message: Optional[str],
    apply_file_selector: bool,
    output_dir_notnone: str,
    force_overwrite: bool,
    user_system_prompt_code: str,
    system_prompt_general: str,
    codebases: list[Codebase],
    file_extensions: list[str],
) -> tuple[Optional[str], Optional[UsageInfo]]: # BAD. DEFINE A NEW TYPE FOR THIS.
    """
    Send a message to the AI and return its response.

    Args:
        client: The client instance for the main AI.
        state (MainLoopState): The current state of the main loop.
        user_message (Optional[str]): The user's message to send to the AI, if any.
        apply_file_selector (bool): Whether to apply the file selector AI to choose relevant files.
        output_dir_notnone (str): The output directory for generated files when using the /o command.
        force_overwrite (bool): Whether to force overwrite of output files if they already exist.
        user_system_prompt_code (str): The user's part of the system prompt to use for code generation,
                                    additional to the hardcoded coder system prompt.
        system_prompt_general (str): The system prompt to use for general conversation.
        codebases (list[Codebase]): A list of Codebases being watched.
        file_extensions (list[str]): A list of file extensions to watch for in the codebases.

    Preconditions:
        - The `client` is a valid client instance for the AI API.
        - The `state` object contains the current conversation history and other relevant data.
        - If `user_message` is provided, it is a non-empty string.
        - `output_dir_notnone` is a valid directory path.
        - `user_system_prompt_code` and `system_prompt_general` are non-empty strings.
        - `codebases` is a list of valid Codebase objects.
        - `file_extensions` is a list of valid file extension strings.

    Side effects:
        - Sends a request to the AI API.
        - Prints progress and results to the console.
        - May write generated files to the output directory if using the /o command.
        (TODO: CHANGE THIS. THAT'S BEST SEPARATE INTO ANOTHER FUNCTION.)

    Exceptions:
        None

    Returns:
        tuple[Optional[str], Optional[UsageInfo]]: A tuple containing the AI's response string (if any) 
                                                   and usage information (if any).
    """
    if user_message is None:
        return None, None

    relevant_files: list[FileRelativePath] = []
    selector_usage: Optional[UsageInfo] = None

    if apply_file_selector:
        console.print(f"Asking file selection AI for a list of relevant files.")
        selector_response: FileSelectorResponse = retrieve_relevant_files(codebases, user_message, state.conversation_history)  # type: ignore

        if isinstance(selector_response, MalformedResponse):
            console.print("Malformed response from file selector.")
        else:
            assert isinstance(selector_response, FileSelection)
            relevant_files = selector_response.files
            console.print(f"[bold green]Relevant files:[/bold green] [white not bold](according to {selector_response.usage_data.model_name})[/white not bold]")
            for file_path in relevant_files:
                console.print(f"- {file_path}")
            selector_usage = selector_response.usage_data
            console.print(format_cost(selector_usage))
            console.line()

            already_loaded_files = set(relevant_files) & state.loaded_files
            console.print(f"[bold green]The following files are already in the conversation history:[/bold green]")
            for file_path in already_loaded_files:
                console.print(f"- {file_path}")
            
            files_to_load = set(relevant_files) - already_loaded_files
            console.print(f"[bold green]Loading these remaining files:[/bold green]")
            for file_path in files_to_load:
                console.print(f"- {file_path}")
    else:
        files_to_load = set()

    context: Optional[str] = None

    if len(files_to_load) > 0:
        try:
            context = "Here are the relevant files from the codebase. Read them carefully.\n\n"
            for file_path in files_to_load:
                file_contents = load_file_xml(file_path)
                if file_contents:
                    context += file_contents + "\n\n"
                else:
                    console.print(f"[yellow]Skipping file {file_path} due to loading issues.[/yellow]")
        except Exception as e:
            console.print(f"[red]Error loading relevant files: {e}[/red]")
            console.print("Using content from all files from all specified codebases.")
            context = state.codebase_contents
    else:
        context = state.codebase_contents

    new_messages: list[dict[str, str]]

    if context is not None:
        new_messages = [
                {"role": "user", "content": context + user_message}
            ]
    else:
        new_messages = [
                {"role": "user", "content": user_message}
            ]

    messages = state.conversation_history + new_messages
    chat_response_optional: Optional[ChatResponse] = None

    if state.main_model in anthropic_models_long:
        chat_response_optional = None
        # chat_response_optional = anthropic_interface.prompt_ai(client, state.main_model, messages, system_prompt_general)  # type: ignore
    elif state.main_model in openai_models_long:
        chat_response_optional = openai_interface.prompt_ai(client, state.main_model, messages, system_prompt_general)  # type: ignore
    else:
        console.print(f"[bold red]Unsupported model: {state.main_model}[/bold red]")
        return None, None

    if chat_response_optional is None:
        console.print("[bold red]Failed to get a response from the AI.[/bold red]")
        return None, None
    else:
        print_markdown(console, chat_response_optional.content_string)  # type: ignore
        response_string = chat_response_optional.content_string  # type: ignore
        usage = chat_response_optional.usage  # type: ignore
        console.print(format_cost(UsageInfo(usage, state.main_model)))  # type: ignore
        return response_string, UsageInfo(usage, state.main_model)

def main_loop(
    clients: ai_clients.Clients, 
    initial_state: MainLoopState,
    session: PromptSession[str],
    output_dir_notnone: str,
    force_overwrite: bool,
    user_system_prompt_code: str,
    system_prompt_general: str,
    codebases: list[Codebase],
    file_extensions: list[str],
) -> None:
    """
    The main loop of the program, handling user input and AI interaction.

    Args:
        clients (Clients): Instances of clients for interacting with the AIs.
        initial_state (MainLoopState): The initial state of the main loop.
        session (PromptSession): The prompt session object for interactive input.
        output_dir_notnone (str): The output directory for generated files when using the /o command.
        force_overwrite (bool): Whether to force overwrite of output files if they already exist.
        user_system_prompt_code (str): The user's part of the system prompt for code generation.
        system_prompt_general (str): The system prompt for general conversation.
        codebases (list[Codebase]): A list of Codebases being watched.
        file_extensions (list[str]): A list of file extensions to watch for in the codebases.

    Preconditions:
        - The `initial_state` object contains valid initial data for the main loop.
        - The `session` object is initialized for user input.
        - `output_dir_notnone` is a valid directory path.
        - `user_system_prompt_code` and `system_prompt_general` are non-empty strings.
        - `codebases` is a list of valid Codebase objects.
        - `file_extensions` is a list of valid file extension strings.

    Side effects:
        - Interacts with the user via the command line prompt.
        - Sends requests to the AI API.
        - Prints progress and results to the console.
        - May write generated files to the output directory if using the /o command.

    Exceptions:
        None

    Returns:
        None
    """
    # Assert that all the types are correct.
    assert isinstance(clients, ai_clients.Clients)
    assert isinstance(initial_state, MainLoopState)
    assert isinstance(session, PromptSession)
    assert isinstance(output_dir_notnone, str)
    assert isinstance(force_overwrite, bool)
    assert isinstance(user_system_prompt_code, str)
    assert isinstance(system_prompt_general, str)
    assert isinstance(codebases, list)
    assert all(isinstance(codebase, Codebase) for codebase in codebases)
    assert isinstance(file_extensions, list)
    assert all(isinstance(file_extension, str) for file_extension in file_extensions)

    state = initial_state

    while True:
        prompt_outcome = prompt_user(session)

        state = prompt_outcome.state_mutation(state)
        action = prompt_outcome.action
        out_text: Optional[str] = prompt_outcome.update_printer(state)

        if out_text is not None:
            console.print(out_text)

        user_message: str = ""

        if isinstance(action, QuitCommand):
            break
        elif isinstance(action, ParseError) or isinstance(action, CostCommand):
            continue
        elif isinstance(action, UpdateCommand):
            console.print("Updating not yet implemented.")
            continue
        elif isinstance(action, Message) or isinstance(action, OutputCommand) or isinstance(action, ModelInstruction):
            if isinstance(action, ModelInstruction):
                if action.message is None:
                    continue

            user_message = action.message
            
            message_result = message_ai_no_codebase(clients, state.main_model, state.conversation_history, system_prompt_general, user_message)

            if isinstance(message_result, AIError):
                console.print(message_result.error_text)
                continue
            else:
                print_chat_response(message_result)