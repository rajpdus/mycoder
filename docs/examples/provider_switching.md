# Provider Switching Examples

This document provides examples of how to switch between different LLM providers in MyCoder-Py.

## Basic Provider Selection

```python
import asyncio
from mycoder.agent.llm import (
    create_provider,
    Message, 
    MessageRole
)

async def compare_providers():
    # Create messages
    messages = [
        Message(role=MessageRole.SYSTEM, content="You are a helpful assistant."),
        Message(role=MessageRole.USER, content="Explain quantum computing in one sentence.")
    ]
    
    # Create OpenAI provider
    openai_provider = create_provider("openai", model="gpt-4")
    
    # Create Anthropic provider
    anthropic_provider = create_provider("anthropic", model="claude-3-sonnet-20240229")
    
    # Generate responses
    openai_response = await openai_provider.generate(messages)
    anthropic_response = await anthropic_provider.generate(messages)
    
    # Print responses
    print(f"OpenAI response: {openai_response.message.content}")
    print(f"Anthropic response: {anthropic_response.message.content}")
    
    # Compare token usage
    openai_tokens = openai_provider.count_message_tokens(messages)
    anthropic_tokens = anthropic_provider.count_message_tokens(messages)
    
    print(f"OpenAI token count: {openai_tokens}")
    print(f"Anthropic token count: {anthropic_tokens}")

asyncio.run(compare_providers())
```

## Using Provider from Configuration

```python
import asyncio
from mycoder.settings import Settings
from mycoder.agent.llm import (
    create_provider,
    Message, 
    MessageRole
)

async def use_configured_provider():
    # Load settings
    settings = Settings()
    
    # Get provider type from settings
    provider_type = settings.provider_type  # e.g., "anthropic"
    
    # Create provider from settings
    if provider_type == "openai":
        provider = create_provider(
            "openai",
            api_key=settings.openai_api_key,
            model=settings.default_model
        )
    else:  # anthropic
        provider = create_provider(
            "anthropic",
            api_key=settings.anthropic_api_key,
            model=settings.default_model
        )
    
    # Use the provider
    messages = [
        Message(role=MessageRole.USER, content="Hello, who are you?")
    ]
    
    response = await provider.generate(messages)
    print(f"Response from {provider.provider_name}: {response.message.content}")

asyncio.run(use_configured_provider())
```

## Selecting Provider Based on Task

```python
import asyncio
from mycoder.agent.llm import (
    create_provider,
    Message, 
    MessageRole
)

def get_provider_for_task(task_type):
    """Get the appropriate provider for a specific task type."""
    if task_type == "coding":
        # GPT-4 is often good for coding tasks
        return create_provider("openai", model="gpt-4")
    elif task_type == "creative":
        # Claude is known for creative writing
        return create_provider("anthropic", model="claude-3-opus-20240229")
    else:  # general reasoning
        # Use a faster, cheaper model for general questions
        return create_provider("openai", model="gpt-3.5-turbo")

async def answer_questions():
    questions = [
        {"type": "coding", "text": "Write a Python function to check if a string is a palindrome."},
        {"type": "creative", "text": "Write a short poem about artificial intelligence."},
        {"type": "general", "text": "What is the capital of France?"}
    ]
    
    for q in questions:
        # Get the appropriate provider for this question type
        provider = get_provider_for_task(q["type"])
        
        # Create message
        messages = [
            Message(role=MessageRole.USER, content=q["text"])
        ]
        
        # Generate response
        response = await provider.generate(messages)
        
        # Print result
        print(f"\nQuestion ({q['type']}): {q['text']}")
        print(f"Answer ({provider.provider_name}, {provider.model_name}):")
        print(response.message.content)
        print("-" * 80)

asyncio.run(answer_questions()) 