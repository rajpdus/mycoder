"""
Model Context Protocol (MCP) module for MyCoder.

This module provides integration with the Model Context Protocol, allowing
the agent to access external context and tools.
"""

from .client import MCPClient, MCPResource, MCPTool

__all__ = [
    "MCPClient",
    "MCPResource",
    "MCPTool",
] 