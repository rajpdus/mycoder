"""
Think tool for internal reasoning.

This tool allows the agent to reason through complex problems
without executing external actions.
"""

from typing import Optional

from pydantic import BaseModel, Field

from .base import Tool


class ThinkArgs(BaseModel):
    """Arguments for the Think tool."""
    
    thought: str = Field(
        description="The agent's internal reasoning or thought process"
    )


class ThinkResult(BaseModel):
    """Result of the Think tool."""
    
    result: str = Field(
        description="Acknowledgment of the thought process"
    )


class Think(Tool):
    """
    Tool for internal reasoning without causing external effects.
    
    This tool allows the agent to work through a complex problem
    by explicitly recording its reasoning steps without executing
    any external actions.
    """
    
    name = "think"
    description = (
        "Use this tool to reason step-by-step through a complex problem "
        "without executing any external actions. Use this for planning, "
        "breaking down problems, exploring alternatives, or any other mental "
        "process that helps you organize your thoughts. The thoughts you "
        "provide will be stored in your memory but won't cause any changes "
        "to the external world."
    )
    args_schema = ThinkArgs
    returns_schema = ThinkResult
    
    async def run(self, thought: str) -> dict:
        """
        Process the agent's thinking without side effects.
        
        Args:
            thought: The agent's internal reasoning
            
        Returns:
            dict: Acknowledgment of the thought process
        """
        return {"result": f"I have processed your thinking: {thought}"} 