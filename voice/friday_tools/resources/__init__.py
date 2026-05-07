"""
MCP Resources — expose static or dynamic data to the client.
"""

from friday_tools.resources import data


def register_all_resources(mcp):
    data.register(mcp)
