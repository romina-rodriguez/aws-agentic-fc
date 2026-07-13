"""AI Soccer Defender Agent — Player 1. Nova Pro. No tools (speed)."""

import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib")); sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "lib"))
from _bootstrap import setup_lib_path; setup_lib_path(__file__)

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from agent_base import create_agent, create_invoke_handler
from fallback import build_fallback, DEF_CONFIG

app = BedrockAgentCoreApp()

MY_PLAYER_ID = 1
POSITION_LABEL = "DEF"

SYSTEM_PROMPT = f"""You control player {MY_PLAYER_ID} (DEF) in 5v5 soccer. Return ONLY a JSON array with one command. No text, no thinking, no markdown.

RULES (check in order, do the FIRST that matches):
1. If hasBall=True AND a forward (player 3 or 4) is ahead → PASS type THROUGH to them
2. If hasBall=True → PASS type GROUND to player 2 (midfielder)
3. If opponent has ball AND distBall < 12 → SLIDE_TACKLE the ball carrier (target_player_id from state, sprint=true, distance=5)
4. If opponent has ball AND distBall < 20 → PRESS_BALL intensity 0.9, duration 2
5. If opponent has ball AND opponent is near our goal (within 30 units) → MARK that opponent, tightness TIGHT, duration 3
6. If ball is loose AND distBall < 15 → INTERCEPT aggressive=true, duration 2
7. If opponent has ball AND ball in opponent half → MOVE_TO defensive position x=my_goal*0.5, y=0, sprint=false
8. Otherwise → MOVE_TO position between ball and your goal, y=ball_y*0.5, sprint=false

STAMINA: NEVER sprint. Use sprint=false on all MOVE_TO. Your job is positioning, not running.

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
