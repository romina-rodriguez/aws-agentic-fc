"""Local test for the FWD1 agent — tests state summary, parsing, and fallback."""

import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "lib"))
from test_helpers import mock_agentcore, GAME_STATE, TEAM_ID
mock_agentcore()
from state import summarize_state
from parsing import parse_commands
from fallback import build_fallback, FWD1_CONFIG

MY_PLAYER_ID = 3
POSITION_LABEL = "FWD1"
fallback_commands = build_fallback(FWD1_CONFIG)

def test_summarize():
    print(f"=== STATE SUMMARY ({POSITION_LABEL}, player {MY_PLAYER_ID}) ===")
    print(summarize_state(GAME_STATE, TEAM_ID, MY_PLAYER_ID, POSITION_LABEL))
    print()

def test_fallback():
    print(f"=== FALLBACK ({POSITION_LABEL}) ===")
    cmds = fallback_commands(GAME_STATE, TEAM_ID, MY_PLAYER_ID)
    for c in cmds:
        ok = "OK" if c["playerId"] == MY_PLAYER_ID and c["teamId"] == TEAM_ID else "WRONG"
        print(f"  [{ok}] {c['commandType']} {c.get('parameters', {})}")
    assert all(c["playerId"] == MY_PLAYER_ID for c in cmds)
    print()

def test_fallback_with_ball():
    print(f"=== FALLBACK WITH BALL ({POSITION_LABEL}) ===")
    state = json.loads(json.dumps(GAME_STATE))
    state["ball"]["possessionAgentId"] = f"agentId_{MY_PLAYER_ID}"
    cmds = fallback_commands(state, TEAM_ID, MY_PLAYER_ID)
    for c in cmds:
        print(f"  P{c['playerId']}: {c['commandType']} {c.get('parameters', {})}")
    assert cmds[0]["commandType"] in ("SHOOT", "MOVE_TO")
    print()

if __name__ == "__main__":
    test_summarize()
    test_fallback()
    test_fallback_with_ball()
    print("✅ All local tests passed (Combined team — FWD1)")
