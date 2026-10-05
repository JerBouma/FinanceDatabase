# MCP Bundle

This directory contains the source for `financedatabase.mcpb`, an [MCP Bundle](https://github.com/modelcontextprotocol/mcpb) that installs the Finance Database MCP Server into any compatible AI client (Claude Desktop, Claude Code, and others) with a single click — no Python environment or manual configuration required.

## Installing

1. Download the latest `financedatabase.mcpb` from the releases page [here](https://github.com/JerBouma/FinanceDatabase/releases/latest/download/financedatabase.mcpb)
2. Double-click `financedatabase.mcpb` which will open Claude Desktop, this will open a prompt whether you want to install the bundle, click "Install".
3. A prompt will appear asking you to confirm the installation, click "Install" again. No API key is needed.
4. Enable the bundle by toggling the switch which says "Disabled" to "Enabled".
5. Restart Claude Desktop and the Finance Database MCP Server will be available for use in your conversations.

## Building and Testing Locally

1. Pull in the repository with `git pull https://github.com/JerBouma/FinanceDatabase`
2. Install required dependencies with `uv sync`
3. Build the MCP bundle with `bash financedatabase/mcp_server/mcpb/build-mcpb.sh` (requires the `mcpb` CLI: `npm install -g @anthropic-ai/mcpb`)
4. Find the generated `financedatabase.mcpb` in the `dist/` directory
5. Double-click it to install it into Claude Desktop.

By default the bundle depends on the published PyPI package (pinned to the
current version), so it won't reflect uncommitted local changes. Pass
`--local` to bundle against this checkout instead:

```bash
bash financedatabase/mcp_server/mcpb/build-mcpb.sh --local
```

This produces `dist/financedatabase-local.mcpb`, with the dependency pointed
at your local checkout (editable, via `uv`'s `[tool.uv.sources]`) instead of
the pinned PyPI release. Use it to test uncommitted changes end-to-end in
Claude Desktop before cutting a release. Don't publish this build.
