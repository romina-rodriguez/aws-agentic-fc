"""AI Soccer Midfielder 2 Agent (attacking) — Player 3. Nova Pro."""

import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib")); sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "lib"))
from _bootstrap import setup_lib_path; setup_lib_path(__file__)

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from agent_base import create_agent, create_invoke_handler
from fallback import build_fallback, MID_CONFIG

app = BedrockAgentCoreApp()

MY_PLAYER_ID = 3
POSITION_LABEL = "MID2"

SYSTEM_PROMPT = f"""You control player {MY_PLAYER_ID} (MID, attacking) in 5v5 soccer. Return ONLY a JSON array with one command. No text, no thinking, no markdown.

FORMATION: 1-2-1. You are one of TWO midfielders. Player 2 is your midfield partner. Player 4 is the lone forward. Player 1 is DEF.

RULES (check in order, do the FIRST that matches):
1. If hasBall=True AND distOppGoal < 35 → SHOOT aim_location="BL", power=0.9
2. If hasBall=True AND forward player 4 is ahead and closer to goal → PASS type THROUGH to player 4
3. If hasBall=True AND midfield partner player 2 is open → PASS type GROUND to player 2
4. If hasBall=True → MOVE_TO toward opponent goal (advance x by 12), sprint=true
5. If teammate has ball AND ball in opponent half → MOVE_TO x=opp_goal*0.45, y=8, sprint=false
6. If teammate has ball AND ball in our half → MOVE_TO x=5, y=5, sprint=true
7. If opponent has ball AND distBall < 12 → SLIDE_TACKLE target=ball carrier, sprint=true, distance=5
8. If opponent has ball AND distBall < 20 → PRESS_BALL intensity 0.9, duration 2
9. If opponent has ball → INTERCEPT aggressive=true, duration 2

KEY: You are an ATTACKING midfielder in a 1-2-1. Push forward to support the lone striker (player 4). SHOOT from distance. Press hard when defending. Your midfield partner is player 2 — recycle possession through them.

STAMINA: Use sprint=true ONLY in rules 4 and 6. All other MOVE_TO use sprint=false.

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
