"""
Tool management system for MyCoder.

This module provides the ToolManager class which is responsible for registering,
storing, and retrieving tools for use by the agent.
"""

import logging
from typing import Any, Dict, List, Optional, Set, Type, Union

from mycoder.agent.tools.base import Tool
from mycoder.utils.errors import ToolNotFoundError, ToolExecutionError
from mycoder.utils.logging import get_logger


class ToolManager:
    """
    Manages the collection of tools available to the agent.
    
    The ToolManager is responsible for:
    - Registering tools
    - Validating tool names for uniqueness
    - Retrieving tools by name
    - Formatting tool schemas for LLM providers
    - Executing tools with appropriate error handling
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize a new ToolManager.
        
        Args:
            logger: Optional logger to use. If not provided, a new one will be created.
        """
        self.tools: Dict[str, Tool] = {}
        self.logger = logger or get_logger("mycoder.agent.tool_manager")
    
    def register_tool(self, tool_class: Type[Tool]) -> None:
        """
        Register a tool class.
        
        This instantiates the tool class and adds it to the available tools.
        
        Args:
            tool_class: The Tool class to register
            
        Raises:
            ValueError: If a tool with the same name is already registered
        """
        # Instantiate the tool
        tool = tool_class()
        
        # Check for name collisions
        if tool.name in self.tools:
            raise ValueError(f"A tool with name '{tool.name}' is already registered")
        
        # Register the tool
        self.tools[tool.name] = tool
        self.logger.debug(f"Registered tool: {tool.name}")
    
    def register_tools(self, tool_classes: List[Type[Tool]]) -> None:
        """
        Register multiple tool classes at once.
        
        Args:
            tool_classes: List of Tool classes to register
            
        Raises:
            ValueError: If any tools have name collisions
        """
        for tool_class in tool_classes:
            self.register_tool(tool_class)
    
    def get_tool(self, name: str) -> Tool:
        """
        Get a registered tool by name.
        
        Args:
            name: Name of the tool to retrieve
            
        Returns:
            Tool: The requested tool
            
        Raises:
            ToolNotFoundError: If no tool with the given name is registered
        """
        tool = self.tools.get(name)
        if tool is None:
            raise ToolNotFoundError(f"No tool found with name '{name}'")
        return tool
    
    def has_tool(self, name: str) -> bool:
        """
        Check if a tool with the given name is registered.
        
        Args:
            name: Name of the tool to check
            
        Returns:
            bool: True if the tool exists, False otherwise
        """
        return name in self.tools
    
    def get_all_tools(self) -> List[Tool]:
        """
        Get all registered tools.
        
        Returns:
            List[Tool]: List of all registered tools
        """
        return list(self.tools.values())
    
    def get_tool_names(self) -> Set[str]:
        """
        Get the names of all registered tools.
        
        Returns:
            Set[str]: Set of tool names
        """
        return set(self.tools.keys())
    
    def get_tool_schemas_for_llm(self, provider: str = "anthropic") -> List[Dict[str, Any]]:
        """
        Get schemas for all tools in the format expected by a specific LLM provider.
        
        Args:
            provider: LLM provider name (e.g., "anthropic", "openai")
            
        Returns:
            List[Dict[str, Any]]: List of tool schemas
        """
        return [tool.get_schema_for_llm(provider) for tool in self.tools.values()]
    
    async def execute_tool(
        self, name: str, arguments: Dict[str, Any], handle_errors: bool = True
    ) -> Union[Any, Dict[str, str]]:
        """
        Execute a tool with the given arguments.
        
        Args:
            name: Name of the tool to execute
            arguments: Arguments to pass to the tool
            handle_errors: If True, catches and formats errors instead of raising them
            
        Returns:
            Union[Any, Dict[str, str]]: 
                Either the result of the tool execution, or an error object
                if handle_errors is True and an error occurred
            
        Raises:
            ToolNotFoundError: If the tool doesn't exist (only if handle_errors is False)
            ToolExecutionError: If there's an error during execution (only if handle_errors is False)
            ValidationError: If the arguments don't match the schema (only if handle_errors is False)
        """
        try:
            # Get the tool
            tool = self.get_tool(name)
            
            # Execute the tool
            self.logger.debug(f"Executing tool '{name}' with arguments: {arguments}")
            result = await tool.execute(**arguments)
            self.logger.debug(f"Tool '{name}' execution completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing tool '{name}': {e}")
            
            if handle_errors:
                # Format error as a result dict
                return {
                    "error": f"Error executing tool '{name}': {str(e)}",
                    "error_type": type(e).__name__
                }
            else:
                # Wrap in ToolExecutionError if it's not already one
                if not isinstance(e, ToolExecutionError):
                    raise ToolExecutionError(
                        message=f"Failed to execute tool",
                        tool_name=name,
                        original_error=e
                    ) from e
                raise 