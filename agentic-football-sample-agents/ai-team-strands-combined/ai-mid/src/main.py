"""AI Soccer Midfielder Agent — Player 2. Nova Pro."""

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
1. If hasBall=True AND distOppGoal < 35 → SHOOT aim_location="TR", power=0.85
2. If hasBall=True AND a forward (player 3 or 4) is closer to opponent goal than me → PASS type THROUGH to that forward
3. If hasBall=True AND under pressure (opponent within 10) → PASS type GROUND to nearest teammate
4. If hasBall=True → MOVE_TO toward opponent goal (advance x by 12), sprint=true
5. If teammate has ball AND ball in opponent half → MOVE_TO x between me and opp goal, y offset ±8 from ball, sprint=false
6. If teammate has ball AND ball in our half → MOVE_TO x=0, y=ball_y*0.3, sprint=true
7. If opponent has ball AND distBall < 15 → PRESS_BALL intensity 0.8, duration 2
8. If opponent has ball AND ball in our half → INTERCEPT aggressive=true, duration 2
9. Otherwise → MOVE_TO x=0, y=0, sprint=false

KEY: You are the playmaker. When you have the ball, PASS THROUGH to forwards first. SHOOT if close enough. When defending, INTERCEPT and PRESS aggressively.

STAMINA: Use sprint=true ONLY in rules 4 and 6 (attacking transitions). All other MOVE_TO use sprint=false.

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
