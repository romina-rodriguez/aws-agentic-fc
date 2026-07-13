"""AI Soccer Forward 1 Agent — Player 3. Nova Pro. No tools (speed)."""

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
1. If hasBall=True AND distOppGoal < 35 → SHOOT aim_location="TR", power=0.9
2. If hasBall=True AND player 4 is closer to goal than me → PASS type THROUGH to player 4
3. If hasBall=True AND player 2 is open behind me → PASS type GROUND to player 2
4. If hasBall=True → MOVE_TO toward opponent goal (advance x by 15 toward opp goal, y=-8), sprint=true
5. If teammate has ball AND teammate is in our half → MOVE_TO attacking position (x=opp_goal*0.5, y=-10), sprint=true
6. If teammate has ball AND teammate is in opponent half → MOVE_TO near opponent penalty area (x=opp_goal*0.7, y=-5), sprint=true
7. If opponent has ball AND distBall < 15 → PRESS_BALL intensity 0.9, duration 2
8. Otherwise → MOVE_TO stay in opponent half (x=opp_goal*0.4, y=-8), sprint=false

KEY: You are a STRIKER. Your job is to SHOOT and SCORE. When you have the ball near goal, ALWAYS shoot. Never pass when you can shoot from within 35 units.

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
