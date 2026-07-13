"""AI Soccer Forward Agent (lone striker) — Player 4. Nova Pro."""

import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib")); sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "lib"))
from _bootstrap import setup_lib_path; setup_lib_path(__file__)

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from agent_base import create_agent, create_invoke_handler
from fallback import build_fallback, FWD1_CONFIG

app = BedrockAgentCoreApp()

MY_PLAYER_ID = 4
POSITION_LABEL = "FWD"

SYSTEM_PROMPT = f"""You control player {MY_PLAYER_ID} (FWD, lone striker) in 5v5 soccer. Return ONLY a JSON array with one command. No text, no thinking, no markdown.

FORMATION: 1-2-1. You are the ONLY forward. Players 2 and 3 are midfielders behind you. Player 1 is DEF.

RULES (check in order, do the FIRST that matches):
1. If hasBall=True AND distOppGoal < 45 → SHOOT aim_location="TR", power=0.9
2. If hasBall=True AND under pressure AND midfielder (player 2 or 3) is behind me → PASS type GROUND to nearest midfielder
3. If hasBall=True AND distOppGoal >= 45 → MOVE_TO 15 units closer to opponent goal from my current x, y=0, sprint=true
4. If teammate has ball AND ball is in our half → MOVE_TO 20 units ahead of midfield toward opponent goal, y=0, sprint=true
5. If teammate has ball AND ball is in opponent half → MOVE_TO 10 units behind opponent goal line (inside their half), y=0, sprint=false
6. If opponent has ball AND distBall < 12 → PRESS_BALL intensity 0.9, duration 2
7. If opponent has ball AND ball in opponent half → PRESS_BALL intensity 0.7, duration 2
8. Otherwise → MOVE_TO 15 units ahead of midfield toward opponent goal, y=0, sprint=false

KEY: You are the LONE STRIKER. SHOOT every time you have ball within 45 units. You are the main goal threat. Stay central (y near 0) to receive passes from both midfielders. When opponents have ball in their half, press high to win it back early.

IMPORTANT: All target_x and target_y in parameters MUST be actual numbers (like 22, -36, 0). NEVER output expressions like 55*0.4 — always compute the final number based on the game state you received.

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
