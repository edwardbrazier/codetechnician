# CodeTechnician



## Overview

Command line interface to various AIs, oriented around programming.

This is a developer tool. The distinctive feature of this tool is that it can put codebases into the context for the AI, so that the AI can see all of your code when giving advice, writing new code and writing modifications to the code. It supports both a chat interface and a command for sending the AI's output into multiple source files.

CodeTechnician allows the  AI to write large amounts of code when the user enters single instruction: If fulfilling the user's instruction requires writing a dozen or more pages of code across a number of files, then CodeTechnician will interact with the AI multiple times until it has finished.

The author of this tool is not affiliated in any way with Anthropic, which owns the Claude family of models.
The author of this tool is not affiliated in any way with OpenAI, which owns the GPT family of models.

## How to get an API Key

As of April 2024: To get an API Key to access Claude, go to the Anthropic website and select the 'API' page, which is titled 'Build with Claude'.

For GPT, go to OpenAI's website. (TODO)

## Installation and essential configuration

** As of 26/05/2024, this program only supports GPT-4o. Support for Claude will be added later. See the claudecli repo in the meantime. **

Before you run CodeTechnician, put your Anthropic API key into the environment variable ANTHROPIC_API_KEY. 

There are two ways of running this program:
1. From the Windows exe file ./dist/codetechnician.exe, which depends on some other files in the repository.
2. From the source code, using Python. (See [CONTRIBUTING.md](CONTRIBUTING.md))

The supported shells are:
1. Powershell on Windows 11
2. Bash on WSL (Ubuntu)

It is likely that Bash on other Linux flavours will also work.

The Windows Command Prompt is not supported and will not work properly.

### Configuration file

The configuration file *config.yaml* can be found in the default config directory of the user defined by the [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html).

On a Linux/MacOS system it is defined by the $XDG_CONFIG_HOME variable (check it using `echo $XDG_CONFIG_HOME`). The default, if the variable is not set, should be the `~/.config` folder.

On the first execution of the script, a [template](config.yaml) of the config file is automatically created. If a config file already exists but is missing any fields, default values are used for the missing fields.

## Models

CodeTechnician will support all three models in the Claude 3 series: haiku, sonnet and opus.

Haiku is the fastest and cheapest model. Opus is the most capable. Sonnet is in between.

CodeTechnician also supports GPT-4o.

## Basic usage

Here are some usage examples on Windows in Powershell.

Start from a folder which is not your existing project folder.
First you need [git](https://git-scm.com/downloads).

Here is a simple, generic example:
```
... TODO
```

Now a simple programming-oriented example, again starting from the dist/claudecli directory:
```
... TODO
```


## Multiline input

Add the `--multiline` (or `-ml`) flag in order to toggle multi-line input mode. In this mode use `Alt+Enter` or `Esc+Enter` to submit messages.

## Context

The distinctive feature of CodeTechnician is that it allows you to put entire codebases into the context for the AI.

To provide multiple codebases, use the '-s' option multiple times, like this (Powershell):
```
> .\codetechnician.exe -s .\codebase1\src -s .\codebase2\src -e py,txt -m haiku -o .\out -csp ..\..\codetechnician\coder_system_prompt_default.txt
```

## Markdown rendering

By default, CodeTechnician asks the AI for Markdown and renders its output with some formatting.
This can be turned off for a single message using '/p', or in the configuration file.

## Contributing to this project

Please read [CONTRIBUTING.md](CONTRIBUTING.md)
