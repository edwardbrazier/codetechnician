from dataclasses import dataclass
import os
from typing import Optional, Union
import anthropic
import openai

import codetechnician.openai_interface as openai_interface
import codetechnician.anthropic_interface as anthropic_interface

@dataclass
class Clients:
    openai: Optional[openai.OpenAI]
    anthropic: Optional[anthropic.Client]

GenericClient = Union[openai.OpenAI, anthropic.Client]

def initialise_ai_clients() -> Clients:
    openai_client = openai_interface.setup_client()
    
    anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")

    if anthropic_api_key is None:
        anthropic_client = None
    else:
        anthropic_client = anthropic_interface.setup_client(anthropic_api_key)
    
    return Clients(openai_client, anthropic_client)