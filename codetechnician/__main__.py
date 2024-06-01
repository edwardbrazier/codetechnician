"""
This module provides a command-line interface for interacting with the Anthropic AI model.
It allows users to provide context from local files or directories, set various options,
and engage in a conversational session with the model.
"""

import click
import os
import sys

from prompt_toolkit import PromptSession
from typing import Optional

from codetechnician.interact import *
from codetechnician import constants
from codetechnician.load import load_codebase_state, load_codebase_xml_, load_config, load_file_xml  # type: ignore
from codetechnician.codebase_watcher import Codebase
from codetechnician.pure import get_size, get_model_long_name
from codetechnician.file_selector import retrieve_relevant_files, FileSelectorResponse, FileSelection, MalformedResponse, FileRelativePath # type: ignore
from codetechnician.ai_clients import Clients, initialise_ai_clients


@click.command()
@click.option(
    "-s",
    "--source",
    "sources",
    type=click.Path(exists=True),
    help="Pass files or directories to the model as context. "
    "Repeat this option and its argument any number of times. "
    "The files and directories will only be loaded once. ",
    multiple=True,
    required=False,
)
@click.option(
    "-e",
    "--file-extensions",
    "file_extensions",
    help="File name extensions of files to look at in the codebase, separated by commas without spaces, e.g. py,txt,md "
    "Only use this option once, even for multiple codebases.",
    required=False,
)
@click.option(
    "-m",
    "--model",
    "model",
    help="Set the model. Supported: Anthropic's Claude series ('haiku', 'sonnet', 'opus'). OpenAI: gpt-4o",
    required=False,
)
@click.option(
    "-ml",
    "--multiline",
    "multiline",
    is_flag=True,
    help="Use the multiline input mode. "
    "To submit a multiline input in Bash on Windows, press Escape and then Enter.",
    required=False,
)
@click.option(
    "-o",
    "--output-dir",
    "output_dir",
    type=click.Path(exists=True),
    help="The output directory for generated files when using the /o command. "
    "Defaults to the current working directory.",
    required=False,
)
@click.option(
    "-f",
    "--force",
    "force",
    is_flag=True,
    help="Force overwrite of output files if they already exist.",
    required=False,
)
@click.option(
    "-csp",
    "--coder-system-prompt",
    "coder_system_prompt_user",
    type=click.Path(exists=True),
    help="""
    Path to the file containing the Coder System Prompt. 
    Defaults to '~/.codetechnician_coder_system_prompt.txt'. 
    This is additional to a hardcoded coder system prompt which tells the AI how to format its output for parsing when it is asked to write code into some files.""",
    required=False,
)
@click.option(
    "-gsp",
    "--general-system-prompt",
    "general_system_prompt",
    type=click.Path(exists=True),
    help="""
    Path to the file containing the General System Prompt, used when asking for chat-style responses. 
    Defaults to '~/.codetechnician_general_system_prompt.txt'.""",
    required=False,
)
@click.version_option(version=constants.VERSION, prog_name="codetechnician")
def main(
    sources: list[str],
    model: Optional[str],
    multiline: bool,
    file_extensions: Optional[str],
    output_dir: Optional[str],
    force: bool,
    coder_system_prompt_user: Optional[str],
    general_system_prompt: Optional[str],
) -> None:
    """
    Command-line interface to AIs for programming.
    Supports chat conversations.
    Also supports code output from the AI to multiple files at once.

    Write '/q' to end the chat.\n
    Write '/o <instructions>' to ask the AI for code, which the application will output to the selected output directory.
    '<instructions>' represents your instructions to the AI.
    For example:\n
    >>> /o improve the commenting in load.py\n
    Write '/p <instructions>' to render the AI's response as plain text.
    (This is a workaround in case the AI outputs malformed Markdown.)
    Write '/u' to check for changes in the watched codebases and prepend the contents of added or modified files to the next message.
    (At the moment this only works if there is a single codebase.)
    """

    console.print("[bold]CodeTechnician[/bold]")

    if multiline:
        session: PromptSession[str] = PromptSession(multiline=True)  # type: ignore
    else:
        session: PromptSession[str] = PromptSession()

    try:
        config = load_config(config_file=str(constants.CONFIG_FILE))  # type: ignore
    except FileNotFoundError:
        console.print("[red bold]Configuration file not found[/red bold]")
        sys.exit(1)

    config["non_interactive"] = False

    # Do not emit markdown in non-interactive mode, as ctrl character formatting interferes in several contexts including json output.
    if config["non_interactive"]:
        config["markdown"] = False

    config["json_mode"] = False

    # If the config specifies a model and the command line parameters do not specify a model, then
    # use the one from the config file.
    if model:
        model_long_optional = get_model_long_name(model)

        # First check whether the provided model is valid
        if model_long_optional is None:
            console.print(f"[red bold]Invalid model: {model}[/red bold]")
            sys.exit(1)
        else:
            config["model"] = model_long_optional
    elif "model" not in config:
        config["model"] = constants.gpt_4o

    console.print(f"Model in use: [green bold]{config['model']}[/green bold]")

    codebases: list[Codebase] = []
    codebase_initial_contents: str = ""
    extensions: list[str] = []

    # Source code location from command line option
    if sources:

        if file_extensions is not None and file_extensions != "":
            console.line()
            console.print(
                f"Looking only at source files with extensions: [green bold]{file_extensions}[/green bold]"
            )
            extensions = [ext.strip() for ext in file_extensions.split(",")]

        # For each of the sources, determine if it's a file or directory,
        # load the appropriate codebase state, and add it to the list of codebases.
        for source in sources:
            if os.path.isfile(source):
                console.print(f"File location: [green bold]{source}[/green bold]")

                try:
                    codebase_state = load_codebase_state(source, extensions)
                    codebases.append(Codebase(source, codebase_state))
                    console.print("Loaded [green bold]1[/green bold] file.")
                except ValueError as e:
                    console.print(f"Error reading file: {e}")

                codebase_initial_contents += load_file_xml(source)
            elif os.path.isdir(source):
                console.print(f"Codebase location: [green bold]{source}[/green bold]")

                try:
                    codebase_state = load_codebase_state(source, extensions)
                    codebases.append(Codebase(source, codebase_state))
                    num_files = len(codebase_state.files)
                    console.print(
                        "Loaded [green bold]{}[/green bold] files.".format(num_files)
                    )
                except ValueError as e:
                    console.print(f"Error reading codebase: {e}")

                codebase_initial_contents += load_codebase_xml_(codebases, extensions)
            else:
                console.print(f"[red bold]Invalid source: {source}[/red bold]")

            codebase_contents_desc = get_size(codebase_initial_contents)
            console.print(
                f"Codebase contents size: [green bold]{codebase_contents_desc}[/green bold]"
            )

            file_selector_input_limit_bytes = 200_000 * 5  # Assuming 5 bytes per token
            file_selector_input_limit_mb = file_selector_input_limit_bytes / (1024 * 1024)
            console.print(
                f"Input size limit for file selector model is approximately [green bold]{file_selector_input_limit_mb:.2f} MB[/green bold]"
            )

            if len(codebase_initial_contents) > file_selector_input_limit_bytes:
                console.print(
                    "[yellow]Codebase size is larger than input limit for the file selector model. May not be able to supply the codebase to the AI.[/yellow]"
                )
        

    if coder_system_prompt_user is None:
        coder_system_prompt_user = os.path.expanduser(
            "~/.codetechnician_coder_system_prompt.txt"
        )
    if general_system_prompt is None:
        general_system_prompt = os.path.expanduser(
            "~/.codetechnician_general_system_prompt.txt"
        )

    console.line()

    try:
        with open(coder_system_prompt_user, "r") as f:
            user_system_prompt_code = f.read()

        console.print(
            f"Coder System Prompt loaded from [bold green]{coder_system_prompt_user}[/bold green]"
        )
    except FileNotFoundError:
        console.print("Coder System Prompt file not found. Using default.")
        user_system_prompt_code = ""

    try:
        with open(general_system_prompt, "r") as f:
            system_prompt_general = f.read()
    except FileNotFoundError:
        console.print("General System Prompt file not found. Using default.")
        system_prompt_general = constants.general_system_prompt_default

    conversation_history: ConversationHistory = []

    api_key: Optional[str] = os.environ.get("ANTHROPIC_API_KEY")

    if api_key is None:
        console.print(
            "[bold red]Please set the ANTHROPIC_API_KEY environment variable.[/bold red]"
        )
        sys.exit(1)

    if output_dir is not None:
        output_dir_notnone: str = output_dir
    else:
        output_dir_notnone: str = os.getcwd()

    console.print(
        f"Code files from the AI will be written to this folder: [bold green]{output_dir_notnone}[/bold green]\n"
    )

    # if config["model"] in constants.anthropic_models_long:
    #     sys.exit(1)
    #     # client = anthropic_interface.setup_client(api_key)
    # elif config["model"] in constants.openai_models_long:
    #     client = openai_interface.setup_client(api_key)
    # else:
    #     console.print(f"Model not supported: {model}")
    #     sys.exit(1)

    # Initialise as many AI clients as possible.
    clients: Clients = initialise_ai_clients()

    initial_state = MainLoopState(
        conversation_history=conversation_history,
        codebase_contents=codebase_initial_contents,
        main_model=config["model"], # type: ignore
        cumulative_cost=0.0,
        loaded_files=set(),
        file_selector_enabled=True,
        plain_text_enabled=False,
    )

    main_loop(
        clients,
        initial_state,
        session,
        output_dir_notnone,
        force,
        user_system_prompt_code,
        system_prompt_general,
        codebases,
        extensions,
    )


if __name__ == "__main__":
    main()
