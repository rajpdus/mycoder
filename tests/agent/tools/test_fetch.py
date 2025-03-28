"""
Tests for the Fetch tool implementation.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import aiohttp

from mycoder.agent.tools.fetch import Fetch, FetchArgs


@pytest.fixture
def mock_response():
    """Create a mock aiohttp ClientResponse."""
    response = MagicMock(spec=aiohttp.ClientResponse)
    response.status = 200
    response.text = AsyncMock(return_value="Response text")
    response.json = AsyncMock(return_value={"key": "value"})
    response.headers = {"Content-Type": "application/json", "Server": "nginx"}
    return response


@pytest.fixture
def mock_session():
    """Create a mock aiohttp ClientSession."""
    session = MagicMock(spec=aiohttp.ClientSession)
    session.request = AsyncMock()
    session.__aenter__ = AsyncMock()
    session.__aexit__ = AsyncMock()
    session.__aenter__.return_value = session
    return session


@pytest.fixture
def fetch_tool(mock_session, mock_response):
    """Create a Fetch tool instance for testing."""
    with patch("mycoder.agent.tools.fetch.aiohttp.ClientSession", return_value=mock_session):
        mock_session.request.return_value = mock_response
        fetch = Fetch()
        yield fetch


def test_fetch_tool_init():
    """Test initializing the Fetch tool."""
    fetch = Fetch()
    assert fetch.name == "fetch"
    assert "make http requests" in fetch.description.lower()
    assert fetch.args_schema == FetchArgs


@pytest.mark.asyncio
async def test_fetch_get_request(fetch_tool, mock_session, mock_response):
    """Test making a GET request with the Fetch tool."""
    # Run the fetch tool
    result = await fetch_tool.run(
        url="https://example.com/api",
        method="GET"
    )
    
    # Verify the result
    assert result["status"] == 200
    assert result["body"] == "Response text"
    assert "headers" in result
    assert result["headers"]["Content-Type"] == "application/json"
    
    # Verify the session call
    mock_session.request.assert_called_once_with(
        "GET",
        "https://example.com/api",
        headers={},
        json=None,
        data=None,
        timeout=30
    )


@pytest.mark.asyncio
async def test_fetch_post_request_with_json(fetch_tool, mock_session, mock_response):
    """Test making a POST request with JSON data."""
    # Run the fetch tool
    result = await fetch_tool.run(
        url="https://example.com/api",
        method="POST",
        headers={"Authorization": "Bearer token"},
        json={"name": "Test"}
    )
    
    # Verify the result
    assert result["status"] == 200
    assert result["body"] == "Response text"
    
    # Verify the session call
    mock_session.request.assert_called_once_with(
        "POST",
        "https://example.com/api",
        headers={"Authorization": "Bearer token"},
        json={"name": "Test"},
        data=None,
        timeout=30
    )


@pytest.mark.asyncio
async def test_fetch_post_request_with_data(fetch_tool, mock_session, mock_response):
    """Test making a POST request with form data."""
    # Run the fetch tool
    result = await fetch_tool.run(
        url="https://example.com/api",
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data="name=Test&value=123"
    )
    
    # Verify the result
    assert result["status"] == 200
    assert result["body"] == "Response text"
    
    # Verify the session call
    mock_session.request.assert_called_once_with(
        "POST",
        "https://example.com/api",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        json=None,
        data="name=Test&value=123",
        timeout=30
    )


@pytest.mark.asyncio
async def test_fetch_with_json_response_parsing(fetch_tool, mock_session, mock_response):
    """Test that JSON responses are parsed when the Content-Type is application/json."""
    # Set the response Content-Type to application/json
    mock_response.headers = {"Content-Type": "application/json"}
    
    # Run the fetch tool
    result = await fetch_tool.run(
        url="https://example.com/api",
        method="GET",
        parse_json=True
    )
    
    # Verify the result
    assert result["status"] == 200
    assert result["body"] == {"key": "value"}
    
    # Verify the session call
    mock_session.request.assert_called_once()
    mock_response.json.assert_called_once()


@pytest.mark.asyncio
async def test_fetch_with_timeout_error(fetch_tool, mock_session):
    """Test handling of timeout errors."""
    # Make the request method raise a timeout error
    mock_session.request.side_effect = aiohttp.ClientTimeout("Timeout error")
    
    # Run the fetch tool
    result = await fetch_tool.run(
        url="https://example.com/api",
        method="GET"
    )
    
    # Verify the result
    assert "error" in result
    assert "timeout" in result["error"].lower()


@pytest.mark.asyncio
async def test_fetch_with_connection_error(fetch_tool, mock_session):
    """Test handling of connection errors."""
    # Make the request method raise a connection error
    mock_session.request.side_effect = aiohttp.ClientConnectionError("Connection error")
    
    # Run the fetch tool
    result = await fetch_tool.run(
        url="https://example.com/api",
        method="GET"
    )
    
    # Verify the result
    assert "error" in result
    assert "connection" in result["error"].lower()


@pytest.mark.asyncio
async def test_fetch_with_unexpected_error(fetch_tool, mock_session):
    """Test handling of unexpected errors."""
    # Make the request method raise an unexpected error
    mock_session.request.side_effect = Exception("Unexpected error")
    
    # Run the fetch tool
    result = await fetch_tool.run(
        url="https://example.com/api",
        method="GET"
    )
    
    # Verify the result
    assert "error" in result
    assert "unexpected error" in result["error"].lower() 