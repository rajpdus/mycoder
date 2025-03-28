"""
Tools package for MyCoder agent.

This package contains tools that enable the agent to interact with the world,
including file operations, shell commands, and user interactions.
"""

from typing import List, Set

from mycoder.agent.tools.base import Tool, create_tool_from_func
from mycoder.agent.tools.browser import Browser
from mycoder.agent.tools.fetch import Fetch
from mycoder.agent.tools.file_ops import ListDirTool, ReadFileTool, WriteFileTool
from mycoder.agent.tools.session import Session
from mycoder.agent.tools.shell import RunCommandTool
from mycoder.agent.tools.sleep import Sleep
from mycoder.agent.tools.sub_agent import SubAgent
from mycoder.agent.tools.text_editor import TextEditor
from mycoder.agent.tools.think import Think
from mycoder.agent.tools.user import UserMessageTool, UserPromptTool
from mycoder.settings.config import Settings

# Export individual tools for direct imports
__all__ = [
    "Tool",
    "create_tool_from_func",
    "Browser",
    "Fetch",
    "ListDirTool", 
    "ReadFileTool", 
    "WriteFileTool",
    "RunCommandTool",
    "Session",
    "Sleep",
    "SubAgent",
    "TextEditor",
    "Think",
    "UserMessageTool",
    "UserPromptTool",
    "get_default_tools",
    "get_tools_by_categories",
    "load_mcp_tools",
]

# Organize tools by category
TOOLS_BY_CATEGORY = {
    "file": [ListDirTool, ReadFileTool, WriteFileTool, TextEditor],
    "shell": [RunCommandTool],
    "user": [UserMessageTool, UserPromptTool],
    "web": [Browser, Fetch],
    "utility": [Session, Sleep, Think],
    "agent": [SubAgent],
    "mcp": []  # MCP tools are loaded dynamically from settings
}


def get_default_tools() -> List[type]:
    """
    Get all available tool classes.
    
    Returns:
        List[type]: List of tool classes
    """
    tools = []
    for category_tools in TOOLS_BY_CATEGORY.values():
        tools.extend(category_tools)
    return tools


def get_tools_by_categories(categories: Set[str]) -> List[type]:
    """
    Get tool classes in the specified categories.
    
    Args:
        categories: Set of category names
        
    Returns:
        List[type]: List of tool classes
    """
    tools = []
    for category in categories:
        if category in TOOLS_BY_CATEGORY:
            tools.extend(TOOLS_BY_CATEGORY[category])
    return tools


def load_mcp_tools(settings: Settings) -> List[Tool]:
    """
    Load MCP tools based on settings.
    
    This function dynamically imports and initializes MCP tools if they're
    configured in the settings.
    
    Args:
        settings: Application settings
        
    Returns:
        List[Tool]: Initialized MCP tools, or empty list if MCP is not configured
    """
    # Skip if no MCP servers are configured
    if not settings.mcp.servers:
        return []
    
    try:
        # Dynamic import to avoid circular imports
        from mycoder.agent.mcp.tools import get_mcp_tools
        return get_mcp_tools(settings.mcp)
    except ImportError:
        import logging
        logger = logging.getLogger("mycoder.tools")
        logger.warning("MCP tools package not available")
        return []
