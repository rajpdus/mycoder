# MyCoder-Py Architecture

MyCoder-Py is designed with a modular architecture that separates concerns and enables easy extension. This document provides an overview of the system architecture.

## System Overview

```
mycoder-py/
├── src/
│   └── mycoder/
│       ├── agent/         # Agent and tool system
│       │   ├── llm/       # LLM providers
│       │   └── tools/     # Tool implementations
│       ├── cli/           # Command-line interface
│       ├── settings/      # Configuration management
│       └── utils/         # Utility functions
└── tests/                 # Test suite
```

## Core Components

### 1. Agent System

The agent is the core of MyCoder. It orchestrates:
- Communication with LLM providers
- Tool execution
- Context management
- Task planning and execution

### 2. LLM Providers

The LLM provider system abstracts interactions with different language model APIs:
- Defines a common interface for all providers
- Handles message formatting and tool schemas
- Manages API communication
- Provides token counting and context window management

Currently supported providers:
- OpenAI (GPT models)
- Anthropic (Claude models, planned)
- Ollama (local models, planned)

### 3. Tool System

The tool system provides capabilities for the agent to interact with the external world:
- Abstract base Tool class
- Registration and discovery of tools
- Execution and error handling
- Standardized schemas for LLM tool use

Tool categories:
- File operations (read, write, list)
- Shell commands
- User interaction
- (More planned)

### 4. CLI

The Command-Line Interface provides:
- User-friendly entry points
- Configuration via CLI options
- Interactive mode for continuous operation
- Various subcommands for specific functionality

### 5. Configuration System

The configuration system manages:
- Environment variables
- Default settings
- Command-line overrides
- Feature flags

## Data Flow

1. User input → CLI
2. CLI → Configuration
3. Configuration → Agent initialization
4. Agent → Tool registration
5. Agent → LLM Provider initialization
6. Agent execution loop:
   - Agent → LLM Provider (send messages)
   - LLM Provider → Agent (response/tool calls)
   - Agent → Tool execution (if tool calls)
   - Tool → Agent (results)
   - Agent → LLM Provider (tool results)

## Extension Points

MyCoder is designed to be extensible at several points:

1. **LLM Providers**: Add new providers by implementing the `LLMProvider` interface
2. **Tools**: Create new tools by subclassing the `Tool` base class
3. **CLI Commands**: Add new commands by extending the Click command group
4. **Configuration**: Add new settings to the Settings class 