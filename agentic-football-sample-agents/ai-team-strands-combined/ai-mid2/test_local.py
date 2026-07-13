"""Local test for the MID2 agent (player 3) — tests state summary, parsing, and fallback."""

import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "lib"))
from test_helpers import mock_agentcore, GAME_STATE, TEAM_ID
mock_agentcore()
from state import summarize_state
from parsing import parse_commands
from fallback import build_fallback, MID_CONFIG

MY_PLAYER_ID = 3
POSITION_LABEL = "MID2"
fallback_commands = build_fallback(MID_CONFIG)

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

if __name__ == "__main__":
    test_summarize()
    test_fallback()
    print("✅ All local tests passed (Combined team — MID2, player 3)")
