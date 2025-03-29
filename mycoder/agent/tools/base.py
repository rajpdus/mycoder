"""
Base classes and functionality for the MyCoder tool system.

This module defines the abstract base Tool class that all specific tools inherit from,
along with utility functions for tool validation and management.
"""

import inspect
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, Union

from pydantic import BaseModel, ValidationError, create_model


class Tool(ABC):
    """
    Base class for all MyCoder tools.
    
    A Tool represents a capability the AI agent can use to interact with
    the external environment or perform specific actions.
    """
    
    name: str
    description: str
    args_schema: Type[BaseModel]
    returns_schema: Optional[Type[BaseModel]] = None
    
    def __init__(self) -> None:
        """Initialize the tool with validation of required attributes."""
        # Validate that required attributes are set
        if not hasattr(self, 'name') or not self.name:
            raise ValueError(f"Tool {self.__class__.__name__} must define a 'name' attribute")
        
        if not hasattr(self, 'description') or not self.description:
            raise ValueError(f"Tool {self.__class__.__name__} must define a 'description' attribute")
        
        if not hasattr(self, 'args_schema') or not self.args_schema:
            raise ValueError(f"Tool {self.__class__.__name__} must define an 'args_schema' attribute")
    
    def validate_args(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Validate the arguments using the args_schema.
        
        Args:
            **kwargs: Arguments to validate against the schema
            
        Returns:
            Dict[str, Any]: Validated arguments
            
        Raises:
            ValidationError: If arguments don't match the schema
        """
        try:
            validated = self.args_schema(**kwargs)
            return validated.model_dump()
        except ValidationError as e:
            # Re-raise with more helpful message
            raise ValidationError(
                e.errors(),
                model=self.args_schema
            )
    
    @abstractmethod
    async def run(self, **kwargs: Any) -> Any:
        """
        Execute the tool with the given arguments.
        
        This is the main method that must be implemented by all tools.
        
        Args:
            **kwargs: Arguments to pass to the tool
            
        Returns:
            Any: Result of the tool execution
            
        Raises:
            ToolExecutionError: If there's an error during execution
        """
        pass
    
    async def execute(self, **kwargs: Any) -> Any:
        """
        Validate arguments and execute the tool.
        
        This is the main public method to call when using a tool.
        
        Args:
            **kwargs: Arguments to pass to the tool
            
        Returns:
            Any: Result of the tool execution
            
        Raises:
            ValidationError: If arguments don't match the schema
            ToolExecutionError: If there's an error during execution
        """
        # Validate arguments against schema
        validated_args = self.validate_args(**kwargs)
        
        # Execute the tool with validated arguments
        return await self.run(**validated_args)
    
    def get_schema_for_llm(self, provider: str = "anthropic") -> Dict[str, Any]:
        """
        Generate a schema representation suitable for the LLM provider.
        
        Args:
            provider: LLM provider name (currently only "anthropic" supported)
            
        Returns:
            Dict[str, Any]: Schema in the format expected by the LLM provider
        """
        # Default schema format (Anthropic)
        schema = {
            "name": self.name,
            "description": self.description,
            "parameters": self._get_parameters_schema(),
        }
        
        return schema
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """
        Get a generic schema representation of the parameters.
        
        Returns:
            Dict[str, Any]: Parameters schema
        """
        return {
            "type": "object",
            "properties": {
                name: self._get_property_schema(field)
                for name, field in self.args_schema.model_fields.items()
            },
            "required": [
                name for name, field in self.args_schema.model_fields.items()
                if field.is_required
            ]
        }
    
    def _get_property_schema(self, field) -> Dict[str, Any]:
        """
        Convert a Pydantic field to a schema property.
        
        Args:
            field: Pydantic field
            
        Returns:
            Dict[str, Any]: Schema property definition
        """
        property_schema = {}
        
        # Get type
        annotation = field.annotation
        
        # Handle optional types
        is_optional = False
        if getattr(annotation, "__origin__", None) is Union:
            args = annotation.__args__
            if type(None) in args:
                is_optional = True
                # Filter out None type
                non_none_args = [arg for arg in args if arg is not type(None)]
                if len(non_none_args) == 1:
                    annotation = non_none_args[0]
        
        # Map Python types to JSON schema types
        if annotation is str:
            property_schema["type"] = "string"
        elif annotation is int:
            property_schema["type"] = "integer"
        elif annotation is float:
            property_schema["type"] = "number"
        elif annotation is bool:
            property_schema["type"] = "boolean"
        elif getattr(annotation, "__origin__", None) is list:
            property_schema["type"] = "array"
            if hasattr(annotation, "__args__") and annotation.__args__:
                item_type = annotation.__args__[0]
                if item_type is str:
                    property_schema["items"] = {"type": "string"}
                elif item_type is int:
                    property_schema["items"] = {"type": "integer"}
                elif item_type is float:
                    property_schema["items"] = {"type": "number"}
                elif item_type is bool:
                    property_schema["items"] = {"type": "boolean"}
                else:
                    property_schema["items"] = {"type": "object"}
        elif getattr(annotation, "__origin__", None) is dict:
            property_schema["type"] = "object"
        else:
            property_schema["type"] = "object"
        
        # Add description from field info if available
        if field.description:
            property_schema["description"] = field.description
        
        return property_schema


def create_tool_from_func(
    func, 
    name: Optional[str] = None,
    description: Optional[str] = None
) -> Type[Tool]:
    """
    Create a Tool class from a function.
    
    This is a factory function that creates a Tool subclass from a given function,
    using type annotations to generate the args_schema.
    
    Args:
        func: The async function to convert to a Tool
        name: Optional name for the tool (defaults to function name)
        description: Optional description (defaults to function docstring)
        
    Returns:
        Type[Tool]: A Tool class that wraps the function
    """
    if not inspect.iscoroutinefunction(func):
        raise ValueError(f"Function {func.__name__} must be an async function (coroutine)")
    
    # Get function signature and annotations
    sig = inspect.signature(func)
    
    # Create args model dynamically
    fields = {}
    for param_name, param in sig.parameters.items():
        annotation = param.annotation
        if annotation is inspect.Parameter.empty:
            annotation = Any
            
        default = ... if param.default is inspect.Parameter.empty else param.default
        fields[param_name] = (annotation, default)
    
    args_model = create_model(f"{func.__name__.title()}Args", **fields)
    
    # Create the tool class
    class FunctionTool(Tool):
        name = name or func.__name__
        description = description or inspect.getdoc(func) or f"Run the {func.__name__} function"
        args_schema = args_model
        
        async def run(self, **kwargs: Any) -> Any:
            return await func(**kwargs)
    
    return FunctionTool 