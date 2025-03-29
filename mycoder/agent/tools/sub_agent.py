"""
SubAgent tool for MyCoder.

This module provides a tool for spawning subordinate agents to handle tasks concurrently.
"""

import asyncio
import copy
import os
import uuid
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator

from src.mycoder.agent.tools.base import Tool


class SubAgentArgs(BaseModel):
    """Arguments for running a sub-agent."""
    
    prompt: str = Field(..., description="The prompt or instruction for the sub-agent to execute")
    working_dir: str = Field(
        ".",
        description="The working directory for the sub-agent. Defaults to current directory."
    )
    tools: Optional[List[str]] = Field(
        None,
        description="List of tool names the sub-agent should have access to. If None, inherits parent's tools."
    )
    wait: bool = Field(
        False,
        description="Whether to wait for the sub-agent to complete before returning. If False, returns immediately with the agent_id."
    )
    provider: Optional[str] = Field(
        None,
        description="The LLM provider to use for the sub-agent. If None, inherits parent's provider."
    )
    model: Optional[str] = Field(
        None,
        description="The model to use for the sub-agent. If None, inherits parent's model."
    )
    
    @field_validator("working_dir")
    @classmethod
    def validate_working_dir(cls, v):
        """Validate that the working directory exists."""
        if not os.path.exists(v):
            raise ValueError(f"Working directory {v} does not exist")
        if not os.path.isdir(v):
            raise ValueError(f"{v} is not a directory")
        return v


class SubAgentResult(BaseModel):
    """Result of running a sub-agent."""
    
    agent_id: str = Field(..., description="Unique identifier for the sub-agent")
    status: str = Field(..., description="Status of the sub-agent: 'running', 'completed', or 'failed'")
    result: Optional[Any] = Field(None, description="Result of the sub-agent execution if completed")
    error: Optional[str] = Field(None, description="Error message if the sub-agent failed")


class SubAgent(Tool):
    """Tool for spawning and managing sub-agents."""
    
    name = "sub_agent"
    description = "Spawn a subordinate agent to handle a task. Can be used to run tasks concurrently."
    args_schema = SubAgentArgs
    
    # Dictionary to keep track of running agents
    _running_agents: Dict[str, asyncio.Task] = {}
    
    def __init__(self):
        """Initialize the SubAgent tool."""
        super().__init__()
    
    async def run(self, prompt: str, working_dir: str = ".", tools: Optional[List[str]] = None,
                  wait: bool = False, provider: Optional[str] = None, 
                  model: Optional[str] = None) -> Dict[str, Any]:
        """Run a sub-agent with the given prompt and parameters."""
        try:
            # Generate a unique ID for this sub-agent
            agent_id = str(uuid.uuid4())
            
            # Create the task to run the agent
            task = asyncio.create_task(self._run_agent(
                agent_id=agent_id,
                prompt=prompt,
                working_dir=working_dir,
                tools=tools,
                provider=provider,
                model=model
            ))
            
            # Store the task
            self._running_agents[agent_id] = task
            
            # If wait is True, wait for the task to complete
            if wait:
                try:
                    result = await task
                    return {
                        "agent_id": agent_id,
                        "status": "completed",
                        "result": result
                    }
                except Exception as e:
                    return {
                        "agent_id": agent_id,
                        "status": "failed",
                        "error": str(e)
                    }
            
            # If not waiting, return immediately with the agent ID
            return {
                "agent_id": agent_id,
                "status": "running"
            }
        
        except Exception as e:
            return {
                "status": "failed",
                "error": f"Failed to create sub-agent: {str(e)}"
            }
    
    async def _run_agent(self, agent_id: str, prompt: str, working_dir: str,
                         tools: Optional[List[str]], provider: Optional[str],
                         model: Optional[str]) -> Any:
        """
        Execute the agent in a separate task.
        
        This internal method handles the actual execution of the sub-agent.
        """
        try:
            # In a real implementation, this would import and use the Agent class
            # Here we're using a placeholder implementation
            
            # Simulate agent execution with a delay
            await asyncio.sleep(1)
            
            # This is where you would create and run the actual agent
            # For example:
            # from src.mycoder.agent import Agent
            # agent = Agent(
            #     provider=provider,
            #     model=model,
            #     tools=tools,
            # )
            # result = await agent.run(prompt, working_dir=working_dir)
            
            # For now, just return a simulated result
            result = {
                "message": f"Executed sub-agent with prompt: {prompt[:50]}...",
                "tools_used": tools or ["inherited tools"],
                "working_dir": working_dir
            }
            
            # Remove from running agents when done
            if agent_id in self._running_agents:
                del self._running_agents[agent_id]
            
            return result
            
        except Exception as e:
            # Remove from running agents on error
            if agent_id in self._running_agents:
                del self._running_agents[agent_id]
            raise e
    
    async def get_status(self, agent_id: str) -> Dict[str, Any]:
        """Get the status of a running sub-agent."""
        if agent_id not in self._running_agents:
            return {
                "status": "error",
                "error": f"Sub-agent with ID {agent_id} not found"
            }
        
        task = self._running_agents[agent_id]
        
        if task.done():
            try:
                result = task.result()
                return {
                    "agent_id": agent_id,
                    "status": "completed",
                    "result": result
                }
            except Exception as e:
                return {
                    "agent_id": agent_id,
                    "status": "failed",
                    "error": str(e)
                }
        else:
            return {
                "agent_id": agent_id,
                "status": "running"
            }
    
    async def cancel(self, agent_id: str) -> Dict[str, Any]:
        """Cancel a running sub-agent."""
        if agent_id not in self._running_agents:
            return {
                "status": "error",
                "error": f"Sub-agent with ID {agent_id} not found"
            }
        
        task = self._running_agents[agent_id]
        
        if not task.done():
            task.cancel()
            
            try:
                await task
            except asyncio.CancelledError:
                pass
            
            del self._running_agents[agent_id]
            
            return {
                "status": "success",
                "message": f"Sub-agent {agent_id} cancelled"
            }
        else:
            del self._running_agents[agent_id]
            
            return {
                "status": "error",
                "error": f"Sub-agent {agent_id} already completed or failed"
            }
    
    @classmethod
    async def cleanup(cls) -> None:
        """Clean up all running sub-agents."""
        for agent_id, task in list(cls._running_agents.items()):
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        cls._running_agents.clear() 