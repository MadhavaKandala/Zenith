"""
Zenith MCP Server - Entry Point
Run with: python mcp_server.py
"""

from mcp.server.fastmcp import FastMCP
from friday_tools.tools import register_all_tools
from friday_tools.prompts import register_all_prompts
from friday_tools.resources import register_all_resources
from friday_tools.config import config

mcp = FastMCP(
    name=config.SERVER_NAME,
    instructions=(
        "You are Zenith, a Tony Stark-style local-first AI assistant. "
        "You have access to a set of local tools to help the user. "
        "Be concise, accurate, and a little witty."
    ),
)

register_all_tools(mcp)
register_all_prompts(mcp)
register_all_resources(mcp)


def main():
    mcp.run(transport="sse")


if __name__ == "__main__":
    main()
