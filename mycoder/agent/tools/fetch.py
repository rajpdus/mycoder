"""
Fetch tool for making HTTP requests.

This tool allows the agent to interact with external web services
and fetch data from URLs.
"""

import json
from typing import Dict, List, Optional, Union

import httpx
from pydantic import BaseModel, Field, HttpUrl

from .base import Tool


class FetchArgs(BaseModel):
    """Arguments for the Fetch tool."""
    
    url: HttpUrl = Field(
        description="The URL to send the request to"
    )
    method: str = Field(
        default="GET",
        description="HTTP method to use (GET, POST, PUT, DELETE, etc.)"
    )
    headers: Optional[Dict[str, str]] = Field(
        default=None,
        description="HTTP headers to include with the request"
    )
    params: Optional[Dict[str, str]] = Field(
        default=None,
        description="Query parameters to include with the request"
    )
    body: Optional[Union[Dict, List, str]] = Field(
        default=None,
        description="Request body to send with the request (for POST/PUT)"
    )
    timeout: Optional[float] = Field(
        default=30.0,
        description="Request timeout in seconds"
    )


class FetchResult(BaseModel):
    """Result of the Fetch tool."""
    
    status_code: int = Field(
        description="HTTP status code of the response"
    )
    headers: Dict[str, str] = Field(
        description="HTTP headers from the response"
    )
    content: str = Field(
        description="Response body content"
    )
    content_type: str = Field(
        description="Content type of the response"
    )


class Fetch(Tool):
    """
    Tool for making HTTP requests to external services.
    
    This tool allows the agent to fetch data from the web, interact with APIs,
    and retrieve information from online sources.
    """
    
    name = "fetch"
    description = (
        "Make HTTP requests to external services or websites. Use this tool "
        "to fetch data from URLs, interact with APIs, or retrieve information "
        "from online sources. Supports various HTTP methods (GET, POST, etc.) "
        "and allows customization of headers, query parameters, and request body."
    )
    args_schema = FetchArgs
    returns_schema = FetchResult
    
    async def run(
        self, 
        url: HttpUrl, 
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, str]] = None,
        body: Optional[Union[Dict, List, str]] = None,
        timeout: float = 30.0
    ) -> dict:
        """
        Make an HTTP request to the specified URL.
        
        Args:
            url: The URL to send the request to
            method: HTTP method to use (GET, POST, PUT, DELETE, etc.)
            headers: HTTP headers to include with the request
            params: Query parameters to include with the request
            body: Request body to send with the request (for POST/PUT)
            timeout: Request timeout in seconds
            
        Returns:
            dict: Response data including status code, headers, and content
            
        Raises:
            httpx.RequestError: If the request fails
        """
        async with httpx.AsyncClient() as client:
            # Prepare request body if provided
            json_data = None
            data = None
            
            if body is not None:
                if isinstance(body, (dict, list)):
                    json_data = body
                else:
                    data = body
            
            # Make the request
            method = method.upper()
            response = await client.request(
                method=method,
                url=str(url),
                headers=headers,
                params=params,
                json=json_data,
                data=data,
                timeout=timeout
            )
            
            # Get content type from headers
            content_type = response.headers.get('content-type', '').split(';')[0]
            
            # Convert response to dict for all header values
            response_headers = dict(response.headers.items())
            
            # Process the response
            return {
                "status_code": response.status_code,
                "headers": response_headers,
                "content": response.text,
                "content_type": content_type
            } 