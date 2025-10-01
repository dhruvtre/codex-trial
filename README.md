# Codex Trial – Claude Agent SDK demo

This repository contains a barebones example that uses the
[`claude-agent-sdk`](https://docs.claude.com/en/api/agent-sdk/overview) to spin
up an interactive terminal agent. The code is intentionally small and
well-documented so it can act as a starting point for adding custom tools or
experimenting with different prompting strategies.

## Project layout

```
.
├── pyproject.toml              # Python package metadata and dependencies
├── run_agent.py                # Async CLI entry point for starting the agent
└── src/claude_agent_demo/
    ├── __init__.py
    ├── backend.py              # ClaudeSDKClient wrapper + helper utilities
    └── tools.py                # MCP tool helpers + sample echo tool
```

## Prerequisites

1. Python 3.11 or newer.
2. An Anthropic API key with access to the Claude Agent SDK endpoints. Export
   it as the `ANTHROPIC_API_KEY` environment variable or store it in a `.env`
   file at the project root.
3. (Optional) Claude Code CLI if you plan to use built-in tools that depend on
   local execution.

Install the dependencies with:

```bash
pip install -e .
```

## Running the demo agent

Launch the interactive terminal loop with the default configuration:

```bash
python run_agent.py
```

You can customise the model, system prompt, permission mode, and log level:

```bash
python run_agent.py \
  --model claude-3-5-sonnet-20240620 \
  --system-prompt "You are an enthusiastic Python tutor." \
  --permission-mode acceptEdits \
  --log-level DEBUG
```

To start the agent without the sample `echo` tool, pass `--no-tools`.

Provide a one-off prompt without starting the REPL by passing it as a
positional argument:

```bash
python run_agent.py "Summarise the repository layout."
```

Type `exit` (or press `Ctrl+C`) in the REPL to close the session.
