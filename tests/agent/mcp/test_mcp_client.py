"""
Tests for the MCP client implementation.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mycoder.agent.mcp.client import MCPClient, MCPResource, MCPTool


@pytest.fixture
def mcp_config():
    """Create a mock MCP configuration."""
    config = MagicMock()
    config.servers = ["http://localhost:8080"]
    config.enabled = True
    return config


@pytest.fixture
def mock_response():
    """Create a mock HTTP response."""
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = {
        "hello": "world"
    }
    return mock


@pytest.fixture
def mock_httpx_client():
    """Create a mock httpx client."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = MagicMock()
        mock_get = AsyncMock()
        mock_post = AsyncMock()
        mock_instance.get = mock_get
        mock_instance.post = mock_post
        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mcp_client(mcp_config, mock_httpx_client):
    """Create an MCPClient instance for testing."""
    client = MCPClient(mcp_config)
    return client


def test_mcp_resource_init():
    """Test initializing an MCPResource."""
    resource = MCPResource(
        uri="test://example.com/resource",
        content_type="text/plain",
        content="Example content"
    )
    
    assert resource.uri == "test://example.com/resource"
    assert resource.content_type == "text/plain"
    assert resource.content == "Example content"


def test_mcp_tool_init():
    """Test initializing an MCPTool."""
    tool = MCPTool(
        name="test_tool",
        description="A test tool",
        server_url="http://localhost:8080"
    )
    
    assert tool.name == "test_tool"
    assert tool.description == "A test tool"
    assert tool.server_url == "http://localhost:8080"


def test_mcp_client_init(mcp_client, mcp_config):
    """Test initializing the MCP client."""
    assert mcp_client._config == mcp_config
    assert len(mcp_client._servers) == 1
    assert mcp_client._servers[0] == "http://localhost:8080"


@pytest.mark.asyncio
async def test_fetch_resource(mcp_client, mock_httpx_client, mock_response):
    """Test fetching a resource from MCP."""
    # Setup mock response
    mock_httpx_client.get.return_value = mock_response
    
    # Call fetch_resource
    resource = await mcp_client.fetch_resource("test://example.com/resource")
    
    # Verify the result
    assert isinstance(resource, MCPResource)
    assert resource.uri == "test://example.com/resource"
    assert resource.content == json.dumps({"hello": "world"})
    
    # Verify the HTTP call
    mock_httpx_client.get.assert_called_once()
    args, kwargs = mock_httpx_client.get.call_args
    assert "test://example.com/resource" in args[0]


@pytest.mark.asyncio
async def test_fetch_resource_with_accept(mcp_client, mock_httpx_client, mock_response):
    """Test fetching a resource with accept header."""
    # Setup mock response
    mock_response.headers = {"content-type": "application/json"}
    mock_httpx_client.get.return_value = mock_response
    
    # Call fetch_resource with accept header
    resource = await mcp_client.fetch_resource(
        "test://example.com/resource",
        accept="application/json"
    )
    
    # Verify headers
    args, kwargs = mock_httpx_client.get.call_args
    assert "headers" in kwargs
    assert kwargs["headers"]["Accept"] == "application/json"
    assert resource.content_type == "application/json"


@pytest.mark.asyncio
async def test_fetch_context(mcp_client, mock_httpx_client, mock_response):
    """Test fetching context from MCP."""
    # Setup mock response with resources
    mock_response.json.return_value = {
        "resources": [
            {
                "uri": "test://example.com/resource1",
                "contentType": "text/plain",
                "content": "Resource 1 content"
            },
            {
                "uri": "test://example.com/resource2",
                "contentType": "application/json",
                "content": "{\"key\": \"value\"}"
            }
        ]
    }
    mock_httpx_client.post.return_value = mock_response
    
    # Call fetch_context
    resources = await mcp_client.fetch_context("test query")
    
    # Verify the result
    assert isinstance(resources, list)
    assert len(resources) == 2
    assert resources[0].uri == "test://example.com/resource1"
    assert resources[0].content_type == "text/plain"
    assert resources[0].content == "Resource 1 content"
    assert resources[1].uri == "test://example.com/resource2"
    assert resources[1].content_type == "application/json"
    assert resources[1].content == "{\"key\": \"value\"}"
    
    # Verify the HTTP call
    mock_httpx_client.post.assert_called_once()
    args, kwargs = mock_httpx_client.post.call_args
    assert "/mcp/context" in args[0]
    assert kwargs["json"]["query"] == "test query"


@pytest.mark.asyncio
async def test_discover_tools(mcp_client, mock_httpx_client, mock_response):
    """Test discovering tools from MCP."""
    # Setup mock response with tools
    mock_response.json.return_value = {
        "tools": [
            {
                "name": "tool1",
                "description": "Tool 1 description",
                "schema": {
                    "type": "object",
                    "properties": {
                        "param1": {"type": "string"}
                    }
                }
            },
            {
                "name": "tool2",
                "description": "Tool 2 description",
                "schema": {
                    "type": "object",
                    "properties": {
                        "param2": {"type": "integer"}
                    }
                }
            }
        ]
    }
    mock_httpx_client.get.return_value = mock_response
    
    # Call discover_tools
    tools = await mcp_client.discover_tools()
    
    # Verify the result
    assert isinstance(tools, list)
    assert len(tools) == 2
    assert tools[0].name == "tool1"
    assert tools[0].description == "Tool 1 description"
    assert tools[0].server_url == "http://localhost:8080"
    assert tools[1].name == "tool2"
    assert tools[1].description == "Tool 2 description"
    
    # Verify the HTTP call
    mock_httpx_client.get.assert_called_once()
    args, kwargs = mock_httpx_client.get.call_args
    assert "/mcp/tools" in args[0]


@pytest.mark.asyncio
async def test_execute_tool(mcp_client, mock_httpx_client, mock_response):
    """Test executing a tool via MCP."""
    # Setup mock response
    mock_response.json.return_value = {
        "result": "Tool execution result"
    }
    mock_httpx_client.post.return_value = mock_response
    
    # Create a tool
    tool = MCPTool(
        name="test_tool",
        description="A test tool",
        server_url="http://localhost:8080",
        schema={
            "type": "object",
            "properties": {
                "param1": {"type": "string"}
            }
        }
    )
    
    # Call execute_tool
    result = await mcp_client.execute_tool(tool, {"param1": "test value"})
    
    # Verify the result
    assert result == "Tool execution result"
    
    # Verify the HTTP call
    mock_httpx_client.post.assert_called_once()
    args, kwargs = mock_httpx_client.post.call_args
    assert "/mcp/tools/test_tool" in args[0]
    assert kwargs["json"]["param1"] == "test value"


@pytest.mark.asyncio
async def test_close(mcp_client, mock_httpx_client):
    """Test closing the client."""
    mock_httpx_client.aclose = AsyncMock()
    
    await mcp_client.close()
    
    mock_httpx_client.aclose.assert_called_once() 