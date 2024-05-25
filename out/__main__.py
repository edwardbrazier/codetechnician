
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

from codetechnician.ai_functions import setup_client
from codetechnician.interact import *
from codetechnician import constants
from codetechnician.load import load_codebase_state, load_codebase_xml_, load_config, load_file_xml  # type: ignore
from codetechnician.codebase_watcher import Codebase, amend_codebase_records


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
    help="Set the model. In ascending order of capability, the options are: 'haiku', 'sonnet', 'opus'",
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
    Defaults to '~/.claudecli_coder_system_prompt.txt'. 
    This is additional to a hardcoded coder system prompt which tells Claude how to format its output in XML when it is asked to write code into some files.""",
    required=False,
)
@click.option(
    "-gsp",
    "--general-system-prompt",
    "general_system_prompt",
    type=click.Path(exists=True),
    help="""
    Path to the file containing the General System Prompt, used when asking for chat-style responses. 
    Defaults to '~/.claudecli_general_system_prompt.txt'.""",
    required=False,
)
@click.version_option(version=constants.VERSION, prog_name='codetechnician')
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
    Command-line interface to the Anthropic Claude AI.
    Supports chat conversations.
    Also supports code output from Claude to multiple files at once.

    Write '/q' to end the chat.\n
    Write '/o <instructions>' to ask Claude for code, which the application will output to the selected output directory.
    '<instructions>' represents your instructions to Claude.
    For example:\n
    >>> /o improve the commenting in load.py\n
    Write '/p <instructions>' to render Claude's response as plain text.
    (This is a workaround in case Claude outputs malformed Markdown.)
    Write '/u' to check for changes in the watched codebases and prepend the contents of added or modified files to the next message. 
    (At the moment this only works if there is a single codebase.)
    """

    console.print("[bold]CodeTechnician[/bold]")

    # ---- Remaining code unchanged. ----
    