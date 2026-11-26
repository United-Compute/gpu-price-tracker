# Agent skills

Skills in this directory follow the [Agent Skills](https://agentskills.io/specification) layout (`SKILL.md` plus optional `references/` and `scripts/`). They describe how to use the public United Compute GPU price API. No API keys and no paid calls.

This repository also holds the open GPU price dataset (`data/`). The skill reads the same data live from the API.

## gpu-prices

Live cloud GPU rental prices and availability (H100, H200, B200, RTX 4090, RTX 5090, and the rest of the index) from [unitedcompute.ai](https://unitedcompute.ai).

### Install with skills.sh

```bash
npx skills add United-Compute/gpu-price-tracker
```

One skill, one agent:

```bash
npx skills add United-Compute/gpu-price-tracker --skill gpu-prices -a claude-code
```

The same `--skill gpu-prices` flag works with `-a cursor` and `-a codex`. The CLI copies the skill into that agent's skills directory.

### Install by hand

Copy `skills/gpu-prices/` to:

| Agent | Project directory | User directory |
|---|---|---|
| Claude Code | `.claude/skills/gpu-prices` | `~/.claude/skills/gpu-prices` |
| Cursor | `.cursor/skills/gpu-prices` | `~/.cursor/skills/gpu-prices` |
| Codex | `.agents/skills/gpu-prices` | `~/.agents/skills/gpu-prices` |

Codex also reads `.agents/skills` in parent directories up to the git root. Putting the copy only at the repository root's `.agents/skills` is enough for Codex sessions started anywhere in the repo.

### MCP

The MCP server is public at `https://unitedcompute.ai/mcp` (also listed in `/llms.txt` and on `/api`). The connect command the site already shows is:

```bash
claude mcp add --transport http united-compute https://unitedcompute.ai/mcp
```

`.mcp.json` is that command checked in, so Claude Code loads it from a checkout of this repo. `"type": "http"` is required there: Claude Code treats a URL with no `type` as a local stdio server. Cursor's plugin manifest points `mcpServers` at the same `.mcp.json`. No second config file.

`GET /mcp` returns 405. Clients must POST (Streamable HTTP). No API key.

Claude Code plugin (skill plus that MCP file):

```bash
claude plugin marketplace add United-Compute/gpu-price-tracker
claude plugin install united-compute@united-compute
```

Codex, in `~/.codex/config.toml`, uses the same URL. A `url` and no command means Streamable HTTP:

```toml
[mcp_servers.united-compute]
url = "https://unitedcompute.ai/mcp"
```

### Example prompts

- Where can I rent an H100 right now for under $3 an hour?
- Cheapest RTX 4090 on spot and on demand.
- B200 in stock in the US, data center only, skip resellers.
- Which GPU with at least 80 GB fits a training budget of $4 per hour?
- What is the H100 price index today, and how did it move in the last day?
