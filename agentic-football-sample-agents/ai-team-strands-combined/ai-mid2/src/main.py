"""AI Soccer Midfielder Agent v2 (aggressive) — Player 2. Nova Pro."""

import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib")); sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "lib"))
from _bootstrap import setup_lib_path; setup_lib_path(__file__)

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from agent_base import create_agent, create_invoke_handler
from fallback import build_fallback, MID_CONFIG

app = BedrockAgentCoreApp()

MY_PLAYER_ID = 2
POSITION_LABEL = "MID"

SYSTEM_PROMPT = f"""You control player {MY_PLAYER_ID} (MID, aggressive) in 5v5 soccer. Return ONLY a JSON array with one command. No text, no thinking, no markdown.

RULES (check in order, do the FIRST that matches):
1. If hasBall=True AND distOppGoal < 40 → SHOOT aim_location="BL", power=0.9
2. If hasBall=True AND a forward (player 3 or 4) is ahead → PASS type THROUGH to them
3. If hasBall=True → MOVE_TO toward opponent goal (advance x by 15), sprint=true
4. If teammate has ball AND I am in opponent half → MOVE_TO x=opp_goal*0.5, y offset ±10, sprint=false
5. If teammate has ball AND I am in our half → MOVE_TO toward opponent half (x=10), sprint=true
6. If opponent has ball AND distBall < 12 → SLIDE_TACKLE target=ball carrier, sprint=true, distance=5
7. If opponent has ball AND distBall < 20 → PRESS_BALL intensity 0.9, duration 2
8. If opponent has ball → INTERCEPT aggressive=true, duration 2

KEY: You are an ATTACKING midfielder. Push forward constantly. SHOOT from distance (within 40 units). Press hard when defending — use SLIDE_TACKLE if close. Never sit back.

STAMINA: Use sprint=true ONLY in rules 3 and 5 (forward runs). All other MOVE_TO use sprint=false.

FIELD: x=-55 to +55, y=-35 to +35. HOME attacks +x (opp goal=55). AWAY attacks -x (opp goal=-55).

FORMAT: [{{"commandType":"...","playerId":{MY_PLAYER_ID},"parameters":{{...}},"duration":0}}]

RULE: target_x and target_y MUST be integers. NEVER output multiplication expressions like 55*0.5 or ball_y*0.3 — compute the value first."""

fallback_commands = build_fallback(MID_CONFIG)

agent = create_agent(SYSTEM_PROMPT, model_id="us.amazon.nova-pro-v1:0")
create_invoke_handler(
    app, agent, MY_PLAYER_ID, POSITION_LABEL, fallback_commands,
    fallback_cfg=MID_CONFIG,
)

if __name__ == "__main__":
    app.run()
