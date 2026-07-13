"""AI Soccer Goalkeeper Agent — Player 0. Nova Pro. No tools (speed)."""

import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib")); sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "lib"))
from _bootstrap import setup_lib_path; setup_lib_path(__file__)

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from agent_base import create_agent, create_invoke_handler
from fallback import build_fallback, GK_CONFIG

app = BedrockAgentCoreApp()

MY_PLAYER_ID = 0
POSITION_LABEL = "GK"

SYSTEM_PROMPT = f"""You control player {MY_PLAYER_ID} (GK) in 5v5 soccer. Return ONLY a JSON array with one command. No text, no thinking, no markdown.

RULES:
- If hasBall=True → [{{"commandType":"GK_DISTRIBUTE","playerId":{MY_PLAYER_ID},"parameters":{{"target_player_id":2,"method":"THROW"}},"duration":0}}]
- If ball is loose AND distBall < 10 → [{{"commandType":"INTERCEPT","playerId":{MY_PLAYER_ID},"parameters":{{"aggressive":true}},"duration":2}}]
- Otherwise → MOVE_TO between ball and your goal center. Your goal is at x=-55 (HOME) or x=55 (AWAY). Stay within 8 units of goal line. Track ball's y coordinate.

FIELD: x=-55 to +55, y=-35 to +35. HOME defends -x, AWAY defends +x.

FORMAT: [{{"commandType":"...","playerId":{MY_PLAYER_ID},"parameters":{{...}},"duration":0}}]"""

fallback_commands = build_fallback(GK_CONFIG)

agent = create_agent(SYSTEM_PROMPT, model_id="us.amazon.nova-pro-v1:0")
create_invoke_handler(
    app, agent, MY_PLAYER_ID, POSITION_LABEL, fallback_commands,
    fallback_cfg=GK_CONFIG,
)

if __name__ == "__main__":
    app.run()
