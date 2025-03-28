"""
User interaction tools for MyCoder.

This module provides tools for interacting with the user, such as asking for input
and displaying structured messages.
"""

from typing import Optional, Union

from pydantic import BaseModel, Field
from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Prompt

from mycoder.agent.tools.base import Tool
from mycoder.utils.errors import ToolExecutionError

# Initialize console for rich output
console = Console()


class UserPromptArgs(BaseModel):
    """Arguments for the user_prompt tool."""
    
    message: str = Field(
        description="The message to display to the user"
    )
    default: Optional[str] = Field(
        default=None,
        description="Default value to use if the user doesn't provide input"
    )
    password: bool = Field(
        default=False,
        description="Whether to hide the user's input (for sensitive information)"
    )
    choices: Optional[list[str]] = Field(
        default=None,
        description="Optional list of choices to present to the user"
    )


class UserMessageArgs(BaseModel):
    """Arguments for the user_message tool."""
    
    content: str = Field(
        description="The content to display to the user"
    )
    format: str = Field(
        default="markdown",
        description="Format of the content (plain or markdown)"
    )
    level: str = Field(
        default="info",
        description="Message level (info, warning, error, success)"
    )


class UserPromptTool(Tool):
    """
    Tool to prompt the user for input.
    
    This tool displays a message to the user and waits for their input.
    """
    
    name = "user_prompt"
    description = "Ask the user for input with an optional message and return their response"
    args_schema = UserPromptArgs
    
    async def run(
        self, 
        message: str, 
        default: Optional[str] = None, 
        password: bool = False,
        choices: Optional[list[str]] = None
    ) -> str:
        """
        Display a message to the user and get their input.
        
        Args:
            message: The message to display to the user
            default: Optional default value to use if no input is provided
            password: Whether to hide the user's input (for passwords)
            choices: Optional list of valid choices to present to the user
            
        Returns:
            str: The user's input
            
        Raises:
            ToolExecutionError: If there's an error getting user input
        """
        try:
            # Format prompt message (add default if provided)
            prompt_message = message
            if default is not None:
                prompt_message = f"{message} [default: {default}]"
            
            # Display choices if provided
            if choices is not None:
                choice_str = ", ".join(choices)
                prompt_message = f"{prompt_message}\nChoices: {choice_str}"
            
            # Get user input
            if password:
                response = Prompt.ask(prompt_message, console=console, password=True, default=default)
            else:
                response = Prompt.ask(prompt_message, console=console, default=default, choices=choices)
            
            return response
            
        except (KeyboardInterrupt, EOFError) as e:
            # Handle user cancellation
            console.print("[yellow]Input cancelled by user[/yellow]")
            raise ToolExecutionError(
                message="User cancelled input",
                tool_name=self.name,
                original_error=e
            ) from e
        except Exception as e:
            raise ToolExecutionError(
                message="Error getting user input",
                tool_name=self.name,
                original_error=e
            ) from e


class UserMessageTool(Tool):
    """
    Tool to display a message to the user.
    
    This tool is used to display information, warnings, or other messages
    to the user in a formatted way.
    """
    
    name = "user_message"
    description = "Display a message to the user with optional formatting"
    args_schema = UserMessageArgs
    
    async def run(
        self, 
        content: str, 
        format: str = "markdown", 
        level: str = "info"
    ) -> bool:
        """
        Display a message to the user.
        
        Args:
            content: The content to display
            format: Format of the content ("plain" or "markdown")
            level: Message level ("info", "warning", "error", "success")
            
        Returns:
            bool: True if the message was displayed successfully
            
        Raises:
            ToolExecutionError: If there's an error displaying the message
        """
        try:
            # Map level to color
            color_map = {
                "info": "blue",
                "warning": "yellow",
                "error": "red",
                "success": "green",
            }
            color = color_map.get(level.lower(), "white")
            
            # Display the message with appropriate formatting
            if format.lower() == "markdown":
                # Use rich's Markdown renderer
                md = Markdown(content)
                console.print(md)
            else:
                # Use plain text with appropriate color
                console.print(content, style=color)
            
            return True
            
        except Exception as e:
            raise ToolExecutionError(
                message="Error displaying message to user",
                tool_name=self.name,
                original_error=e
            ) from e 