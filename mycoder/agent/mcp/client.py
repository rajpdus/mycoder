"""
MCP client implementation for MyCoder.

This module provides a client for interacting with Model Context Protocol servers.
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

import aiohttp
from pydantic import BaseModel

from src.mycoder.settings.config import MCPServer, MCPServerAuth


class MCPResource(BaseModel):
    """A resource from an MCP server."""
    
    uri: str
    content: str
    metadata: Optional[Dict[str, Any]] = None


class MCPTool(BaseModel):
    """A tool from an MCP server."""
    
    uri: str
    name: str
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    returns: Optional[Dict[str, Any]] = None


class MCPClient:
    """
    Client for interacting with MCP servers.
    
    This client handles the communication with MCP servers according to the
    Model Context Protocol specification.
    """
    
    def __init__(self, server_config: MCPServer):
        """
        Initialize the MCP client.
        
        Args:
            server_config: Configuration for the MCP server
        """
        self.server_config = server_config
        self.logger = logging.getLogger("mycoder.mcp.client")
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Enter the async context manager."""
        if not self._session:
            self._session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the async context manager."""
        if self._session:
            await self._session.close()
            self._session = None
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """
        Get the authorization headers for the MCP server.
        
        Returns:
            Dict[str, str]: The authorization headers
        """
        auth = self.server_config.auth
        headers = {}
        
        if auth.type == "bearer" and auth.token:
            headers["Authorization"] = f"Bearer {auth.token}"
        elif auth.type == "basic" and auth.username and auth.password:
            import base64
            auth_str = f"{auth.username}:{auth.password}"
            encoded = base64.b64encode(auth_str.encode()).decode()
            headers["Authorization"] = f"Basic {encoded}"
        
        return headers
    
    def _get_session(self) -> aiohttp.ClientSession:
        """
        Get the aiohttp session, creating one if needed.
        
        Returns:
            aiohttp.ClientSession: The session
        
        Raises:
            RuntimeError: If the client is not used as a context manager
        """
        if not self._session:
            raise RuntimeError(
                "MCPClient must be used as a context manager (with ... as client:)"
            )
        return self._session
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """
        List available resources from the MCP server.
        
        Returns:
            List[Dict[str, Any]]: List of resources with metadata
        
        Raises:
            ValueError: If the server returns an error
        """
        session = self._get_session()
        url = f"{self.server_config.url}/resources"
        headers = self._get_auth_headers()
        
        try:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ValueError(
                        f"Error listing MCP resources: {response.status} - {error_text}"
                    )
                
                return await response.json()
        except aiohttp.ClientError as e:
            self.logger.error(f"Error connecting to MCP server: {str(e)}")
            raise ValueError(f"Error connecting to MCP server: {str(e)}")
    
    async def get_resource(self, uri: str) -> MCPResource:
        """
        Get a resource from the MCP server.
        
        Args:
            uri: The URI of the resource
        
        Returns:
            MCPResource: The resource
        
        Raises:
            ValueError: If the resource doesn't exist or the server returns an error
        """
        session = self._get_session()
        # Extract the path from the URI (format: scheme://path)
        if "://" not in uri:
            raise ValueError(f"Invalid resource URI format: {uri}")
        
        scheme, path = uri.split("://", 1)
        url = f"{self.server_config.url}/resources/{scheme}/{path}"
        headers = self._get_auth_headers()
        
        try:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ValueError(
                        f"Error getting MCP resource: {response.status} - {error_text}"
                    )
                
                data = await response.json()
                return MCPResource(
                    uri=uri,
                    content=data.get("content", ""),
                    metadata=data.get("metadata")
                )
        except aiohttp.ClientError as e:
            self.logger.error(f"Error connecting to MCP server: {str(e)}")
            raise ValueError(f"Error connecting to MCP server: {str(e)}")
    
    async def list_tools(self) -> List[MCPTool]:
        """
        List available tools from the MCP server.
        
        Returns:
            List[MCPTool]: List of tools
        
        Raises:
            ValueError: If the server returns an error
        """
        session = self._get_session()
        url = f"{self.server_config.url}/tools"
        headers = self._get_auth_headers()
        
        try:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ValueError(
                        f"Error listing MCP tools: {response.status} - {error_text}"
                    )
                
                data = await response.json()
                return [
                    MCPTool(
                        uri=tool.get("uri", ""),
                        name=tool.get("name", ""),
                        description=tool.get("description"),
                        parameters=tool.get("parameters"),
                        returns=tool.get("returns")
                    )
                    for tool in data
                ]
        except aiohttp.ClientError as e:
            self.logger.error(f"Error connecting to MCP server: {str(e)}")
            raise ValueError(f"Error connecting to MCP server: {str(e)}")
    
    async def execute_tool(self, uri: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Execute a tool on the MCP server.
        
        Args:
            uri: The URI of the tool
            params: The parameters to pass to the tool
        
        Returns:
            Any: The result of executing the tool
        
        Raises:
            ValueError: If the tool doesn't exist or the server returns an error
        """
        session = self._get_session()
        # Extract the path from the URI (format: scheme://path)
        if "://" not in uri:
            raise ValueError(f"Invalid tool URI format: {uri}")
        
        scheme, path = uri.split("://", 1)
        url = f"{self.server_config.url}/tools/{scheme}/{path}"
        headers = self._get_auth_headers()
        headers["Content-Type"] = "application/json"
        
        try:
            async with session.post(
                url, headers=headers, json=params or {}
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ValueError(
                        f"Error executing MCP tool: {response.status} - {error_text}"
                    )
                
                return await response.json()
        except aiohttp.ClientError as e:
            self.logger.error(f"Error connecting to MCP server: {str(e)}")
            raise ValueError(f"Error connecting to MCP server: {str(e)}") 