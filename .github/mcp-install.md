<!-- Last modified: 2026-07-14T00:00:00.000Z -->

# GitHub Copilot MCP Installation

Use this workflow when a user asks to make `loop-improver-mcp` available to GitHub Copilot.

1. Confirm that `uv` is installed. Install it with the platform's normal package manager when it is absent.
2. Open the user's GitHub Copilot MCP configuration with the `MCP: Open User Configuration` VS Code command.
3. Add this server configuration, preserving other configured servers:

```json
{
  "servers": {
    "loop-improver": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "tool",
        "run",
        "--from",
        "git+https://github.com/Thor-DraperJr/loop-improver-mcp.git",
        "loop-improver-mcp"
      ]
    }
  }
}
```

4. Start or restart the server from the MCP view and verify that `compare_loops`, `improve_loop`, and `record_loop_insight` are available.

The checked-out repository supplies the equivalent workspace configuration in `.vscode/mcp.json`. It runs the local checkout through `uv tool run --from .`, so contributors exercise the source they have open.