# Model Context Protocol Examples

This document demonstrates how to use Model Context Protocol (MCP) integration with MyCoder-Py.

## Basic MCP Client Usage

```python
import asyncio
from mycoder.settings.config import MCPServer, MCPServerAuth
from mycoder.agent.mcp import MCPClient

async def mcp_client_example():
    # Create server configuration
    server_config = MCPServer(
        name="docs",
        url="http://localhost:3000",
        auth=MCPServerAuth(
            type="bearer",
            token="your-auth-token"
        )
    )
    
    # Use the MCP client as a context manager
    async with MCPClient(server_config) as client:
        # List available resources
        resources = await client.list_resources()
        print(f"Available resources: {resources}")
        
        # Get a specific resource
        if resources:
            uri = resources[0]["uri"]
            resource = await client.get_resource(uri)
            print(f"Resource content: {resource.content[:100]}...")
        
        # List available tools
        tools = await client.list_tools()
        print(f"Available tools: {[tool.name for tool in tools]}")
        
        # Execute a tool if available
        if tools:
            tool = tools[0]
            print(f"Executing tool: {tool.name}")
            result = await client.execute_tool(tool.uri, params={"query": "example"})
            print(f"Tool result: {result}")

if __name__ == "__main__":
    asyncio.run(mcp_client_example())
```

## Using MCP with LLM Providers

```python
import asyncio
from mycoder.settings.config import MCPServer, MCPServerAuth, MCPSettings, Settings
from mycoder.agent.llm import create_provider, Message, MessageRole
from mycoder.agent.mcp import MCPClient

async def mcp_with_llm_example():
    # Configure MCP settings
    mcp_settings = MCPSettings(
        servers=[
            MCPServer(
                name="docs",
                url="http://localhost:3000",
                auth=MCPServerAuth(type="bearer", token="your-token")
            )
        ],
        default_resources=["docs://api/reference"]
    )
    
    # Create settings
    settings = Settings(mcp=mcp_settings)
    
    # Create provider
    provider = create_provider("anthropic", model="claude-3-sonnet-20240229")
    
    # Retrieve context from MCP
    server_config = settings.mcp.servers[0]
    resource_content = ""
    
    async with MCPClient(server_config) as client:
        # Get a specific resource
        try:
            resource = await client.get_resource("docs://api/reference")
            resource_content = resource.content
        except ValueError as e:
            print(f"Error getting resource: {e}")
    
    # Prepare messages with context
    messages = [
        Message(
            role=MessageRole.SYSTEM,
            content="You are a helpful assistant. Use the provided documentation to answer questions."
        ),
        Message(
            role=MessageRole.USER,
            content=f"Context:\n{resource_content}\n\nQuestion: How do I use the API?"
        )
    ]
    
    # Generate response
    response = await provider.generate(messages)
    print(f"Assistant: {response.message.content}")

if __name__ == "__main__":
    asyncio.run(mcp_with_llm_example())
```

## Using MCP Tools

```python
import asyncio
from mycoder.settings.config import MCPServer, MCPServerAuth, MCPSettings, Settings
from mycoder.agent.tools import load_mcp_tools

async def mcp_tools_example():
    # Configure MCP settings
    mcp_settings = MCPSettings(
        servers=[
            MCPServer(
                name="docs",
                url="http://localhost:3000",
                auth=MCPServerAuth(type="bearer", token="your-token")
            )
        ]
    )
    
    # Create settings
    settings = Settings(mcp=mcp_settings)
    
    # Load MCP tools
    mcp_tools = load_mcp_tools(settings)
    
    # Print available tools
    print("Available MCP tools:")
    for tool in mcp_tools:
        print(f"- {tool.name}: {tool.description}")
    
    # Use the tools
    if mcp_tools:
        # List servers
        list_servers_tool = next((tool for tool in mcp_tools if tool.name == "list_mcp_servers"), None)
        if list_servers_tool:
            servers = await list_servers_tool.run()
            print(f"Servers: {servers}")
        
        # List resources
        list_resources_tool = next((tool for tool in mcp_tools if tool.name == "list_mcp_resources"), None)
        if list_resources_tool:
            resources = await list_resources_tool.run()
            print(f"Resources: {resources}")
        
        # Get a resource
        get_resource_tool = next((tool for tool in mcp_tools if tool.name == "get_mcp_resource"), None)
        if get_resource_tool and resources:
            resource = await get_resource_tool.run(uri=resources[0]["uri"])
            print(f"Resource: {resource}")

if __name__ == "__main__":
    asyncio.run(mcp_tools_example()) 