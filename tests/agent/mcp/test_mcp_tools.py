"""
Tests for the MCP tools implementation.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mycoder.agent.mcp.client import MCPClient, MCPTool
from mycoder.agent.mcp.tools import (
    MCPContextTool,
    MCPExecuteTool,
    get_mcp_tools
)


@pytest.fixture
def mcp_config():
    """Create a mock MCP configuration."""
    config = MagicMock()
    config.servers = ["http://localhost:8080"]
    config.enabled = True
    return config


@pytest.fixture
def mock_client():
    """Create a mock MCP client."""
    with patch("mycoder.agent.mcp.tools.MCPClient") as mock_client_class:
        mock_instance = MagicMock()
        mock_instance.fetch_context = AsyncMock()
        mock_instance.discover_tools = AsyncMock()
        mock_instance.execute_tool = AsyncMock()
        mock_client_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mcp_context_tool(mock_client):
    """Create an MCPContextTool instance for testing."""
    return MCPContextTool(mock_client)


@pytest.fixture
def mcp_execute_tool(mock_client):
    """Create an MCPExecuteTool instance for testing."""
    return MCPExecuteTool(mock_client)


def test_get_mcp_tools(mcp_config):
    """Test getting MCP tools from config."""
    with patch("mycoder.agent.mcp.tools.MCPClient") as mock_client_class:
        mock_instance = MagicMock()
        mock_client_class.return_value = mock_instance
        
        tools = get_mcp_tools(mcp_config)
        
        assert len(tools) == 2
        assert isinstance(tools[0], MCPContextTool)
        assert isinstance(tools[1], MCPExecuteTool)
        assert tools[0]._client == mock_instance
        assert tools[1]._client == mock_instance


def test_mcp_context_tool_init(mcp_context_tool):
    """Test initializing the MCP context tool."""
    assert mcp_context_tool.name == "mcp_context"
    assert "retrieve contextual information" in mcp_context_tool.description.lower()


def test_mcp_execute_tool_init(mcp_execute_tool):
    """Test initializing the MCP execute tool."""
    assert mcp_execute_tool.name == "mcp_execute"
    assert "execute an mcp tool" in mcp_execute_tool.description.lower()


@pytest.mark.asyncio
async def test_mcp_context_tool_run(mcp_context_tool, mock_client):
    """Test running the MCP context tool."""
    # Setup mock response
    mock_client.fetch_context.return_value = [
        MagicMock(
            uri="test://example.com/resource1",
            content_type="text/plain",
            content="Resource 1 content"
        ),
        MagicMock(
            uri="test://example.com/resource2",
            content_type="application/json",
            content="{\"key\": \"value\"}"
        )
    ]
    
    # Call run
    result = await mcp_context_tool.run(query="test query")
    
    # Verify the result
    assert isinstance(result, dict)
    assert "resources" in result
    assert len(result["resources"]) == 2
    assert result["resources"][0]["uri"] == "test://example.com/resource1"
    assert result["resources"][0]["content"] == "Resource 1 content"
    assert result["resources"][1]["uri"] == "test://example.com/resource2"
    assert result["resources"][1]["content"] == "{\"key\": \"value\"}"
    
    # Verify the client call
    mock_client.fetch_context.assert_called_once_with("test query")


@pytest.mark.asyncio
async def test_mcp_execute_tool_run(mcp_execute_tool, mock_client):
    """Test running the MCP execute tool."""
    # Setup mock tool
    mock_tool = MagicMock(spec=MCPTool)
    mock_tool.name = "mock_tool"
    mock_tool.schema = {
        "type": "object",
        "properties": {
            "param1": {"type": "string"}
        }
    }
    
    # Setup discover_tools to return the mock tool
    mock_client.discover_tools.return_value = [mock_tool]
    
    # Setup execute_tool response
    mock_client.execute_tool.return_value = "Tool execution result"
    
    # Call run
    result = await mcp_execute_tool.run(
        tool_name="mock_tool",
        arguments={"param1": "test value"}
    )
    
    # Verify the result
    assert isinstance(result, dict)
    assert "result" in result
    assert result["result"] == "Tool execution result"
    
    # Verify client calls
    mock_client.discover_tools.assert_called_once()
    mock_client.execute_tool.assert_called_once_with(
        mock_tool,
        {"param1": "test value"}
    )


@pytest.mark.asyncio
async def test_mcp_execute_tool_run_tool_not_found(mcp_execute_tool, mock_client):
    """Test running the MCP execute tool with a non-existent tool."""
    # Setup discover_tools to return no tools
    mock_client.discover_tools.return_value = []
    
    # Call run
    result = await mcp_execute_tool.run(
        tool_name="non_existent_tool",
        arguments={"param1": "test value"}
    )
    
    # Verify the result
    assert isinstance(result, dict)
    assert "error" in result
    assert "not found" in result["error"].lower()
    
    # Verify client calls
    mock_client.discover_tools.assert_called_once()
    mock_client.execute_tool.assert_not_called() 