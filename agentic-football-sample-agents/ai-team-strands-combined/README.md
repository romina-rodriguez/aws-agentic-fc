# AI Team (Strands) — Combined: Memory + Gateway

Five AI agents that each control a single player in a 5v5 soccer match, combining
**AgentCore Memory** (cross-tick recall) with **AgentCore Gateway** (MCP tactical tools)
using balanced strategy prompts as the foundation.

Built with [Strands Agents SDK](https://github.com/strands-agents/sdk-python) and deployed to
[Amazon Bedrock AgentCore](https://docs.aws.amazon.com/bedrock-agentcore/).

## Strategy

This team combines the best of both worlds:

- **Memory (STM)** — Agents remember previous ticks. They learn opponent patterns,
  recall which passes were intercepted, and adapt their strategy as the match progresses.
- **Gateway (MCP Tools)** — Agents have access to 4 tactical analysis tools for
  data-driven decisions (pass probability, shot evaluation, space finding, threat ranking).
- **Balanced Prompts** — Solid positional play as the foundation, enhanced by
  memory-informed and tool-assisted decision making.

### Available MCP Tools
| Tool | Purpose |
|------|---------|
| `calculate_pass_options` | Pass success probability based on interception risk |
| `evaluate_shot` | Shot probability with aim recommendation |
| `find_open_space` | Grid-based open space finder by zone |
| `get_defensive_assignment` | Opponent threat ranking for marking priority |

## Architecture

```
agents/
├── lib/                            # Shared library (same as other teams)
└── ai-team-strands-combined/
    ├── ai-gk/                      # Goalkeeper  (player 0) — Nova Micro + Memory + Gateway
    ├── ai-def/                     # Defender    (player 1) — Nova Lite  + Memory + Gateway
    ├── ai-mid/                     # Midfielder  (player 2) — Nova Pro   + Memory + Gateway
    ├── ai-fwd1/                    # Forward 1   (player 3) — Nova Micro + Memory + Gateway
    ├── ai-fwd2/                    # Forward 2   (player 4) — Nova Lite  + Memory + Gateway
    ├── combined_agent_base.py      # Agent factory (Memory + MCP)
    ├── combined_invoke_handler.py  # Invoke handler with MCP context + Memory
    ├── gateway_tools/              # Lambda handlers for tactical tools
    ├── manage_gateway.py           # Gateway creation script
    ├── create_memory.py            # Memory resource creation script
    ├── deploy-all.sh               # Full deploy script (macOS/Linux)
    └── README.md
```

## Prerequisites

- Python 3.10+
- AWS CLI configured with valid credentials
- AWS account with Bedrock model access (Nova Micro, Lite, and Pro)
- AgentCore CLI: `pip install bedrock-agentcore-starter-toolkit`
- `rsync` (pre-installed on macOS)

## Quick Start

### Deploy everything (one command)

```bash
AWS_DEFAULT_REGION=us-east-1 ./deploy-all.sh
```

The script automatically:
1. Creates a Memory resource (or reuses existing)
2. Creates Lambda IAM role (reuses if exists)
3. Deploys 4 Lambda functions for tactical tools
4. Creates Gateway execution role (reuses if exists)
5. Creates MCP Gateway with NONE auth (reuses if exists)
6. Registers Lambda targets on the gateway
7. Deploys all 5 agents with both `MEMORY_ID` and `GATEWAY_URL`
8. Attaches Gateway + Memory permissions to execution roles

### Deploy a single agent

```bash
AWS_DEFAULT_REGION=us-east-1 ./deploy-all.sh ai-mid
```

### Skip auto-setup (if you already have resources)

```bash
export MEMORY_ID=<your-memory-id>
export GATEWAY_URL=https://your-gateway-id.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp
./deploy-all.sh
```

### Local test (no AWS needed)

```bash
python3 ai-gk/test_local.py
python3 ai-mid/test_local.py --llm  # needs AWS credentials
```

## Player IDs and Positions

| Player ID | Position   | Model      |
|-----------|------------|------------|
| 0         | Goalkeeper | Nova Micro |
| 1         | Defender   | Nova Lite  |
| 2         | Midfielder | Nova Pro   |
| 3         | Forward 1  | Nova Micro |
| 4         | Forward 2  | Nova Lite  |
