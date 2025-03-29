"""
MCP tools for agent integration.

This module provides tools for interacting with MCP servers.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from src.mycoder.agent.tools.base import Tool
from src.mycoder.utils.errors import ToolExecutionError
from src.mycoder.settings.config import MCPSettings
from .client import MCPClient, MCPResource, MCPTool


class ListMCPServersArgs(BaseModel):
    """Arguments for the list_mcp_servers tool."""
    pass


class ListMCPResourcesArgs(BaseModel):
    """Arguments for the list_mcp_resources tool."""
    
    server: Optional[str] = Field(
        default=None,
        description="Name of the server to list resources from (if not provided, lists from all servers)"
    )


class GetMCPResourceArgs(BaseModel):
    """Arguments for the get_mcp_resource tool."""
    
    uri: str = Field(
        description="URI of the resource to retrieve (in the format scheme://path)"
    )
    server: Optional[str] = Field(
        default=None,
        description="Name of the server to get the resource from (if not provided, tries all servers)"
    )


class ListMCPToolsArgs(BaseModel):
    """Arguments for the list_mcp_tools tool."""
    
    server: Optional[str] = Field(
        default=None,
        description="Name of the server to list tools from (if not provided, lists from all servers)"
    )


class ExecuteMCPToolArgs(BaseModel):
    """Arguments for the execute_mcp_tool tool."""
    
    uri: str = Field(
        description="URI of the tool to execute (in the format scheme://path)"
    )
    params: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Parameters to pass to the tool"
    )
    server: Optional[str] = Field(
        default=None,
        description="Name of the server to execute the tool on (if not provided, tries all servers)"
    )


class ListMCPServersTool(Tool):
    """Tool to list available MCP servers."""
    
    name = "list_mcp_servers"
    description = "List all configured MCP servers"
    
    def __init__(self, mcp_settings: MCPSettings):
        """
        Initialize the tool.
        
        Args:
            mcp_settings: MCP configuration settings
        """
        self.mcp_settings = mcp_settings
        self.logger = logging.getLogger("mycoder.mcp.tools.list_servers")
    
    async def run(self) -> List[Dict[str, str]]:
        """
        List all configured MCP servers.
        
        Returns:
            List[Dict[str, str]]: List of servers with their name and URL
        """
        try:
            servers = []
            for server in self.mcp_settings.servers:
                servers.append({
                    "name": server.name,
                    "url": server.url
                })
            return servers
        except Exception as e:
            self.logger.error(f"Error listing MCP servers: {str(e)}")
            raise ToolExecutionError(
                message=f"Error listing MCP servers: {str(e)}",
                tool_name=self.name
            )


class ListMCPResourcesTool(Tool):
    """Tool to list resources from MCP servers."""
    
    name = "list_mcp_resources"
    description = "List resources available from MCP servers"
    
    def __init__(self, mcp_settings: MCPSettings):
        """
        Initialize the tool.
        
        Args:
            mcp_settings: MCP configuration settings
        """
        self.mcp_settings = mcp_settings
        self.logger = logging.getLogger("mycoder.mcp.tools.list_resources")
    
    async def run(self, server: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List resources from MCP servers.
        
        Args:
            server: Name of the server to list resources from (if not provided, lists from all servers)
            
        Returns:
            List[Dict[str, Any]]: List of resources
            
        Raises:
            ToolExecutionError: If there's an error listing resources
        """
        try:
            resources = []
            
            for mcp_server in self.mcp_settings.servers:
                # Skip if server is specified and doesn't match
                if server and mcp_server.name != server:
                    continue
                
                try:
                    async with MCPClient(mcp_server) as client:
                        server_resources = await client.list_resources()
                        
                        # Add server name to each resource
                        for resource in server_resources:
                            resource["server"] = mcp_server.name
                        
                        resources.extend(server_resources)
                except Exception as e:
                    self.logger.warning(
                        f"Error listing resources from MCP server {mcp_server.name}: {str(e)}"
                    )
                    # Continue with other servers
            
            return resources
        except Exception as e:
            self.logger.error(f"Error listing MCP resources: {str(e)}")
            raise ToolExecutionError(
                message=f"Error listing MCP resources: {str(e)}",
                tool_name=self.name
            )


class GetMCPResourceTool(Tool):
    """Tool to get a resource from an MCP server."""
    
    name = "get_mcp_resource"
    description = "Get a resource from an MCP server"
    
    def __init__(self, mcp_settings: MCPSettings):
        """
        Initialize the tool.
        
        Args:
            mcp_settings: MCP configuration settings
        """
        self.mcp_settings = mcp_settings
        self.logger = logging.getLogger("mycoder.mcp.tools.get_resource")
    
    async def run(self, uri: str, server: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a resource from an MCP server.
        
        Args:
            uri: URI of the resource
            server: Name of the server to get the resource from (if not provided, tries all servers)
            
        Returns:
            Dict[str, Any]: The resource content and metadata
            
        Raises:
            ToolExecutionError: If there's an error getting the resource
        """
        try:
            for mcp_server in self.mcp_settings.servers:
                # Skip if server is specified and doesn't match
                if server and mcp_server.name != server:
                    continue
                
                try:
                    async with MCPClient(mcp_server) as client:
                        resource = await client.get_resource(uri)
                        return {
                            "uri": resource.uri,
                            "content": resource.content,
                            "metadata": resource.metadata,
                            "server": mcp_server.name
                        }
                except ValueError:
                    # Resource not found on this server, try the next one
                    continue
            
            # If we get here, the resource wasn't found on any server
            raise ToolExecutionError(
                message=f"Resource not found: {uri}",
                tool_name=self.name
            )
        except Exception as e:
            self.logger.error(f"Error getting MCP resource: {str(e)}")
            raise ToolExecutionError(
                message=f"Error getting MCP resource: {str(e)}",
                tool_name=self.name
            )


class ListMCPToolsTool(Tool):
    """Tool to list tools from MCP servers."""
    
    name = "list_mcp_tools"
    description = "List tools available from MCP servers"
    
    def __init__(self, mcp_settings: MCPSettings):
        """
        Initialize the tool.
        
        Args:
            mcp_settings: MCP configuration settings
        """
        self.mcp_settings = mcp_settings
        self.logger = logging.getLogger("mycoder.mcp.tools.list_tools")
    
    async def run(self, server: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List tools from MCP servers.
        
        Args:
            server: Name of the server to list tools from (if not provided, lists from all servers)
            
        Returns:
            List[Dict[str, Any]]: List of tools
            
        Raises:
            ToolExecutionError: If there's an error listing tools
        """
        try:
            tools_list = []
            
            for mcp_server in self.mcp_settings.servers:
                # Skip if server is specified and doesn't match
                if server and mcp_server.name != server:
                    continue
                
                try:
                    async with MCPClient(mcp_server) as client:
                        server_tools = await client.list_tools()
                        
                        # Convert tools to dicts and add server name
                        for tool in server_tools:
                            tools_list.append({
                                "uri": tool.uri,
                                "name": tool.name,
                                "description": tool.description,
                                "parameters": tool.parameters,
                                "returns": tool.returns,
                                "server": mcp_server.name
                            })
                except Exception as e:
                    self.logger.warning(
                        f"Error listing tools from MCP server {mcp_server.name}: {str(e)}"
                    )
                    # Continue with other servers
            
            return tools_list
        except Exception as e:
            self.logger.error(f"Error listing MCP tools: {str(e)}")
            raise ToolExecutionError(
                message=f"Error listing MCP tools: {str(e)}",
                tool_name=self.name
            )


class ExecuteMCPToolTool(Tool):
    """Tool to execute a tool on an MCP server."""
    
    name = "execute_mcp_tool"
    description = "Execute a tool on an MCP server"
    
    def __init__(self, mcp_settings: MCPSettings):
        """
        Initialize the tool.
        
        Args:
            mcp_settings: MCP configuration settings
        """
        self.mcp_settings = mcp_settings
        self.logger = logging.getLogger("mycoder.mcp.tools.execute_tool")
    
    async def run(
        self, uri: str, params: Optional[Dict[str, Any]] = None, server: Optional[str] = None
    ) -> Any:
        """
        Execute a tool on an MCP server.
        
        Args:
            uri: URI of the tool
            params: Parameters to pass to the tool
            server: Name of the server to execute the tool on (if not provided, tries all servers)
            
        Returns:
            Any: The result of executing the tool
            
        Raises:
            ToolExecutionError: If there's an error executing the tool
        """
        try:
            for mcp_server in self.mcp_settings.servers:
                # Skip if server is specified and doesn't match
                if server and mcp_server.name != server:
                    continue
                
                try:
                    async with MCPClient(mcp_server) as client:
                        result = await client.execute_tool(uri, params)
                        return {
                            "result": result,
                            "server": mcp_server.name
                        }
                except ValueError:
                    # Tool not found on this server, try the next one
                    continue
            
            # If we get here, the tool wasn't found on any server
            raise ToolExecutionError(
                message=f"Tool not found: {uri}",
                tool_name=self.name
            )
        except Exception as e:
            self.logger.error(f"Error executing MCP tool: {str(e)}")
            raise ToolExecutionError(
                message=f"Error executing MCP tool: {str(e)}",
                tool_name=self.name
            )


def get_mcp_tools(mcp_settings: MCPSettings) -> List[Tool]:
    """
    Get all MCP tools.
    
    Args:
        mcp_settings: MCP configuration settings
        
    Returns:
        List[Tool]: List of MCP tools
    """
    return [
        ListMCPServersTool(mcp_settings),
        ListMCPResourcesTool(mcp_settings),
        GetMCPResourceTool(mcp_settings),
        ListMCPToolsTool(mcp_settings),
        ExecuteMCPToolTool(mcp_settings)
    ] 