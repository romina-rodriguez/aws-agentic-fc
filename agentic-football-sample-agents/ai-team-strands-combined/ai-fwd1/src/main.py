"""AI Soccer Forward 1 Agent — Player 3. Nova Pro."""

import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib")); sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "lib"))
from _bootstrap import setup_lib_path; setup_lib_path(__file__)

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from agent_base import create_agent, create_invoke_handler
from fallback import build_fallback, FWD1_CONFIG

app = BedrockAgentCoreApp()

MY_PLAYER_ID = 3
POSITION_LABEL = "FWD1"

SYSTEM_PROMPT = f"""You control player {MY_PLAYER_ID} (FWD, left) in 5v5 soccer. Return ONLY a JSON array with one command. No text, no thinking, no markdown.

RULES (check in order, do the FIRST that matches):
1. If hasBall=True AND distOppGoal < 45 → SHOOT aim_location="TR", power=0.9
2. If hasBall=True AND player 4 is closer to goal than me AND distOppGoal > 45 → PASS type THROUGH to player 4
3. If hasBall=True AND distOppGoal >= 45 → MOVE_TO toward opponent goal (advance x by 15 toward opp goal, y=-8), sprint=true
4. If teammate has ball AND ball is in our half → MOVE_TO x=opp_goal*0.4, y=-10, sprint=true
5. If teammate has ball AND ball is in opponent half → MOVE_TO x=opp_goal*0.6, y=-5, sprint=false
6. If opponent has ball AND distBall < 12 → PRESS_BALL intensity 0.9, duration 2
7. If opponent has ball AND ball is in our half → INTERCEPT aggressive=true, duration 2
8. Otherwise → MOVE_TO x=opp_goal*0.35, y=-8, sprint=false

KEY: You are a STRIKER. SHOOT every time you have the ball within 45 units of goal. Power shots, no hesitation. Only pass if you are too far to shoot.

STAMINA: Use sprint=true ONLY in rules 3 and 4 (attacking runs). All other MOVE_TO use sprint=false.

FIELD: x=-55 to +55, y=-35 to +35. HOME attacks +x (opp goal x=55). AWAY attacks -x (opp goal x=-55).

FORMAT: [{{"commandType":"...","playerId":{MY_PLAYER_ID},"parameters":{{...}},"duration":0}}]"""

fallback_commands = build_fallback(FWD1_CONFIG)

agent = create_agent(SYSTEM_PROMPT, model_id="us.amazon.nova-pro-v1:0")
create_invoke_handler(
    app, agent, MY_PLAYER_ID, POSITION_LABEL, fallback_commands,
    fallback_cfg=FWD1_CONFIG,
)

if __name__ == "__main__":
    app.run()
