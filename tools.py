"""Register tools and make their imports visible to the agent graph."""

from file_tools import inspect_file
from math_tools import calculate
from retrieve_tools import wikipedia_retrieve

# The manager gives each specialist only the tools listed for its role.
tools = {
    "research": [wikipedia_retrieve],
    "calculator": [calculate],
    "files": [inspect_file],
    "reasoning": [],
}
