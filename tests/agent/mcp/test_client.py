"""
Tests for the MCP client implementation.
"""

from unittest.mock import MagicMock, patch

import pytest

from mycoder.agent.mcp.client import MCPClient, MCPResource, MCPTool
from mycoder.settings.config import MCPServer, MCPServerAuth


def test_mcp_resource_init():
    """Test initializing an MCPResource."""
    resource = MCPResource(
        uri="test://example.com/resource",
        content="Test content"
    )
    assert resource.uri == "test://example.com/resource"
    assert resource.content == "Test content"


def test_mcp_tool_init():
    """Test initializing an MCPTool."""
    tool = MCPTool(
        name="test_tool",
        uri="test://example.com/tools/test"
    )
    assert tool.name == "test_tool"
    assert tool.uri == "test://example.com/tools/test"


def test_mcp_client_init():
    """Test initializing the MCPClient."""
    auth = MCPServerAuth(type="bearer", token="test_token")
    config = MCPServer(name="test", url="http://localhost:8080", auth=auth)
    
    with patch("mycoder.agent.mcp.client.aiohttp.ClientSession"):
        client = MCPClient(config)
        assert client.server_config == config 