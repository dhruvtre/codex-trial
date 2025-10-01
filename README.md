# Codex Trial – Claude Agent Demo

This repository now includes a minimal example that demonstrates how to spin up
an agent loop with the Claude Agent SDK.  The project is intentionally small so
that it can serve as a scaffold for experimenting with additional tools and
prompting strategies.

## Project layout

```
.
├── pyproject.toml              # Python package metadata and dependencies
├── run_agent.py                # CLI entry point for starting the agent
└── src/claude_agent_demo/
    ├── __init__.py
    ├── backend.py              # Agent bootstrapping + main loop
    └── tools.py                # Lightweight tool registry abstraction
```

## Prerequisites

1. Python 3.11 or newer.
2. An Anthropic API key with access to the Claude Agent SDK endpoints.  Export
   it as the `ANTHROPIC_API_KEY` environment variable or store it in a
   `.env` file at the project root.

Install the dependencies with:

```bash
pip install -e .
```

## Running the demo agent

Launch the interactive terminal loop with the default configuration:

```bash
python run_agent.py
```

You can customise the model, system prompt, and log level:

```bash
python run_agent.py --model claude-3-5-sonnet-20240620 --log-level DEBUG
```

To start the agent without the sample `echo` tool, pass `--no-default-tools`.

Type `exit` (or press `Ctrl+C`) in the REPL to close the session.
