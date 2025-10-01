# Barebones Claude Agent

This repository demonstrates a minimal agent built with the
[Claude Agent SDK](https://docs.claude.com/en/api/agent-sdk/overview).
It wires together three main pieces:

1. **`agent_backend/agent.py`** – The primary agent loop that drives the
   conversation using `ClaudeSDKClient`.
2. **`agent_backend/tools.py`** – A dedicated module for declaring tools. The
   included `echo` tool serves as a template for adding more capabilities.
3. **`run.py`** – A terminal-friendly entry point that validates required
   environment variables, accepts a prompt, and streams responses back to the
   console.

The code is intentionally lightweight so it can be used as a starting point for
more elaborate agents.

## Getting started

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Export your Anthropic API key (the Claude SDK reads it from
   `ANTHROPIC_API_KEY`):

   ```bash
   export ANTHROPIC_API_KEY=sk-ant-...
   ```

3. Run the agent with an initial prompt:

   ```bash
   python run.py "Summarise the capabilities of this starter agent"
   ```

   You can also pipe a prompt through standard input:

   ```bash
   echo "List three ideas for extending this agent." | python run.py
   ```

The agent prints the streamed response from Claude, including any tool calls
and the final usage summary.

## Extending the agent

- **Add tools:** Define new `@tool` functions in `agent_backend/tools.py` and
  include them in the exported `TOOLS` tuple. The helper `get_tool_server`
  automatically exposes them to the SDK.
- **Custom prompts or models:** Adjust the defaults by instantiating
  `AgentConfig` with a custom system prompt, limited tool list, or model name
  before calling `run_agentic_loop`.
- **Integrate elsewhere:** Import `BarebonesAgent` and use the
  `run_session()` coroutine to embed the agent loop into other applications.

For more advanced scenarios, refer to Anthropic's official guide on
[building agents with the Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk).
