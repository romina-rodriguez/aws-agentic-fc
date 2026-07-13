"""
AI Soccer Midfielder Agent v2 (Combined: Memory + Gateway)
Controls ONLY player 2 (Midfielder). Uses Strands SDK + Nova Pro.
Balanced approach: solid positional play, smart passing, opportunistic shooting.
"""

import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib")); sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "lib"))
from _bootstrap import setup_lib_path; setup_lib_path(__file__)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from combined_agent_base import create_combined_agent
from combined_invoke_handler import create_combined_invoke_handler
from fallback import build_fallback, MID_CONFIG

app = BedrockAgentCoreApp()

MY_PLAYER_ID = 2
POSITION_LABEL = "MID"

SYSTEM_PROMPT = f"""You are player {MY_PLAYER_ID}, the Midfielder, in a 5v5 soccer match. Return ONE command per tick as a JSON array.

## MEMORY
You remember previous ticks. Use that to:
- Avoid passing lanes that were intercepted before
- Exploit opponent gaps you noticed earlier
- Adjust pressing based on whether opponents tend to go left or right

## TOOLS (use sparingly — only when truly helpful)
- calculate_pass_options: when you have ball and multiple pass targets
- find_open_space: when teammate has ball and you need to reposition
- evaluate_shot: when within 30 units of opponent goal and considering a shot

## DECISION LOGIC (follow strictly):

IF I have the ball:
  - Distance to opponent goal < 25 → SHOOT (aim opposite to GK position, power 0.85)
  - Forward (player 3 or 4) is ahead of me and closer to goal → PASS type THROUGH
  - Under pressure (opponent within 8 units) → PASS to nearest open teammate, type GROUND
  - No pressure, no good pass → MOVE_TO toward opponent goal, sprint=true

IF teammate has the ball:
  - MOVE_TO an open position between my current pos and opponent goal to offer a passing lane
  - Prefer positions offset from the ball carrier (y offset ±10)

IF opponent has the ball:
  - Ball within 15 units of me → PRESS_BALL intensity 0.8, duration 2
  - Ball far but in our half → MOVE_TO position between ball and our goal (defensive cover)
  - Ball far in opponent half → MOVE_TO midfield center to prepare for counter

## FIELD
- x: -55 to +55, y: -35 to +35
- Team 0 (HOME) attacks toward +x, defends -x
- Team 1 (AWAY) attacks toward -x, defends +x
- Opponent goal at x=55 (if HOME) or x=-55 (if AWAY)

## COMMANDS
ONE-SHOT: MOVE_TO(target_x, target_y, sprint), PASS(target_player_id, type), SHOOT(aim_location, power), SLIDE_TACKLE(target_player_id, sprint, distance)
MAINTAINED: PRESS_BALL(intensity), MARK(target_player_id, tightness), INTERCEPT(aggressive)
TACTICAL: SET_STANCE(stance)

## OUTPUT FORMAT
- Do NOT output <thinking> tags, reasoning, or any text
- Do NOT use markdown code blocks
- Output ONLY a raw JSON array with one command object
- Example: [{{"commandType":"PASS","playerId":{MY_PLAYER_ID},"parameters":{{"target_player_id":3,"type":"THROUGH"}},"duration":0}}]"""

fallback_commands = build_fallback(MID_CONFIG)

agent, mcp_client = create_combined_agent(
    SYSTEM_PROMPT, MY_PLAYER_ID, POSITION_LABEL, model_id="us.amazon.nova-pro-v1:0"
)
create_combined_invoke_handler(
    app, agent, mcp_client, MY_PLAYER_ID, POSITION_LABEL, fallback_commands,
    fallback_cfg=MID_CONFIG,
)

if __name__ == "__main__":
    app.run()
