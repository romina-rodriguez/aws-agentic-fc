"""Combined agent factory: Memory + Gateway for AI soccer position agents.

Creates a Strands Agent that has:
  - AgentCore Memory (STM) for cross-tick history recall
  - AgentCore Gateway (MCP) for tactical analysis tools
"""

import os
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamablehttp_client
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager
from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig


def _create_gateway_transport():
    """Build a Streamable HTTP transport pointing at the AgentCore Gateway."""
    gateway_url = os.environ.get("GATEWAY_URL")
    if not gateway_url:
        raise RuntimeError("GATEWAY_URL environment variable is required")

    headers = {}
    access_token = os.environ.get("GATEWAY_ACCESS_TOKEN")
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    return streamablehttp_client(gateway_url, headers=headers)


def create_combined_agent(
    system_prompt: str,
    player_id: int,
    position_label: str,
    model_id: str = "us.amazon.nova-micro-v1:0",
) -> tuple[Agent, MCPClient]:
    """Create a Strands Agent with both Memory (STM) and Gateway (MCP tools).

    Required env vars:
      MEMORY_ID    — AgentCore Memory resource ID
      GATEWAY_URL  — AgentCore Gateway MCP endpoint
      TEAM_ID      — used as actor_id and session_id prefix (optional, defaults to 'combined')

    Returns:
      (agent, mcp_client) — caller must use `with mcp_client:` context manager
      when invoking the agent so tools remain available.
    """
    # --- Memory setup ---
    memory_id = os.environ.get("MEMORY_ID")
    team_id = os.environ.get("TEAM_ID", "combined")

    if not memory_id:
        raise RuntimeError("MEMORY_ID environment variable is required")

    session_manager = AgentCoreMemorySessionManager(
        agentcore_memory_config=AgentCoreMemoryConfig(
            memory_id=memory_id,
            session_id=f"match-{team_id}-{position_label}",
            actor_id=f"{team_id}-{position_label}",
        ),
        region_name=os.environ.get("AWS_DEFAULT_REGION"),
    )

    # --- Gateway/MCP setup ---
    mcp_client = MCPClient(_create_gateway_transport)
    model = BedrockModel(model_id=model_id)

    # Fetch tool definitions inside the context so the connection is active
    with mcp_client:
        tools = mcp_client.list_tools_sync()

    # --- Create agent with both memory and tools ---
    agent = Agent(
        model=model,
        system_prompt=system_prompt,
        tools=tools,
        session_manager=session_manager,
    )

    return agent, mcp_client
