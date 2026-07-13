"""AI Soccer Midfielder Agent v2 — Player 2 (balanced). Nova Pro. No tools."""

import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib")); sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "lib"))
from _bootstrap import setup_lib_path; setup_lib_path(__file__)

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from agent_base import create_agent, create_invoke_handler
from fallback import build_fallback, MID_CONFIG

app = BedrockAgentCoreApp()

MY_PLAYER_ID = 2
POSITION_LABEL = "MID"

SYSTEM_PROMPT = f"""You control player {MY_PLAYER_ID} (MID) in 5v5 soccer. Return ONLY a JSON array with one command. No text, no thinking, no markdown.

RULES (check in order, do the FIRST that matches):
1. If hasBall=True AND distOppGoal < 25 → SHOOT aim_location="BL", power=0.8
2. If hasBall=True AND a forward (3 or 4) is ahead of me → PASS type THROUGH to them
3. If hasBall=True → PASS type GROUND to nearest teammate ahead of me
4. If teammate has ball → MOVE_TO position x=halfway between me and opp goal, y offset ±8 from ball, sprint=true
5. If opponent has ball AND distBall < 15 → INTERCEPT aggressive=true, duration 2
6. If opponent has ball AND ball in our half → MOVE_TO between ball and our goal, sprint=true
7. Otherwise → MOVE_TO center of pitch (x=0, y=0), sprint=false

PHILOSOPHY: Balance attack and defense equally. When we have ball, support attack. When we lose it, recover fast. Always PASS forward when possible.

FIELD: x=-55 to +55, y=-35 to +35. HOME attacks +x (opp goal=55). AWAY attacks -x (opp goal=-55).

FORMAT: [{{"commandType":"...","playerId":{MY_PLAYER_ID},"parameters":{{...}},"duration":0}}]"""

fallback_commands = build_fallback(MID_CONFIG)

agent = create_agent(SYSTEM_PROMPT, model_id="us.amazon.nova-pro-v1:0")
create_invoke_handler(
    app, agent, MY_PLAYER_ID, POSITION_LABEL, fallback_commands,
    fallback_cfg=MID_CONFIG,
)

if __name__ == "__main__":
    app.run()
