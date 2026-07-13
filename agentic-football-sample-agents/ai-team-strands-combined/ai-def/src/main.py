"""AI Soccer Defender Agent — Player 1. Nova Pro."""

import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib")); sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "lib"))
from _bootstrap import setup_lib_path; setup_lib_path(__file__)

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from agent_base import create_agent, create_invoke_handler
from fallback import build_fallback, DEF_CONFIG

app = BedrockAgentCoreApp()

MY_PLAYER_ID = 1
POSITION_LABEL = "DEF"

SYSTEM_PROMPT = f"""You control player {MY_PLAYER_ID} (DEF) in 5v5 soccer. Return ONLY a JSON array with one command. No text, no thinking, no markdown.

FORMATION: 1-2-1. You are the SOLE defender. Player 2 and 3 are midfielders. Player 4 is the lone forward.

RULES (check in order, do the FIRST that matches):
1. If hasBall=True AND midfielder player 2 or 3 is open → PASS type GROUND to nearest midfielder
2. If hasBall=True AND forward player 4 is clearly ahead with space → PASS type THROUGH to player 4
3. If hasBall=True → PASS type GROUND to nearest teammate (safe pass)
4. If opponent has ball AND distBall < 8 → SLIDE_TACKLE target=ball carrier, sprint=true, distance=5
5. If opponent has ball AND distBall < 18 → PRESS_BALL intensity 0.9, duration 2
6. If opponent has ball AND opponent near our goal (within 30 units) → MARK that opponent, tightness TIGHT, duration 3
7. If ball is loose AND distBall < 15 → INTERCEPT aggressive=true, duration 2
8. If opponent has ball AND ball in opponent half → MOVE_TO x=my_goal*0.4, y=0, sprint=false
9. Otherwise → MOVE_TO position between ball and your goal, y=ball_y*0.4, sprint=false

KEY: You are the ONLY defender. Stay disciplined. Pass to MIDFIELDERS first (players 2 and 3), not directly to forward unless wide open. Never sprint — conserve stamina. Tackle only when very close (< 8 units).

STAMINA: NEVER sprint. Use sprint=false on ALL MOVE_TO.

FIELD: x=-55 to +55, y=-35 to +35. HOME defends -x (goal at x=-55), AWAY defends +x (goal at x=55).

FORMAT: [{{"commandType":"...","playerId":{MY_PLAYER_ID},"parameters":{{...}},"duration":0}}]"""

fallback_commands = build_fallback(DEF_CONFIG)

agent = create_agent(SYSTEM_PROMPT, model_id="us.amazon.nova-pro-v1:0")
create_invoke_handler(
    app, agent, MY_PLAYER_ID, POSITION_LABEL, fallback_commands,
    fallback_cfg=DEF_CONFIG,
)

if __name__ == "__main__":
    app.run()
