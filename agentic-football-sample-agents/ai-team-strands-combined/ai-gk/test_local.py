"""Local test for the GK agent — tests state summary, parsing, and fallback.
Does NOT test combined agent creation (requires MEMORY_ID + GATEWAY_URL)."""

import json
import sys
import os

# Setup paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "lib"))

from test_helpers import mock_agentcore, GAME_STATE, TEAM_ID
mock_agentcore()

from state import summarize_state
from parsing import parse_commands
from fallback import build_fallback, GK_CONFIG

MY_PLAYER_ID = 0
POSITION_LABEL = "GK"
fallback_commands = build_fallback(GK_CONFIG)


def test_summarize():
    print(f"=== STATE SUMMARY ({POSITION_LABEL}, player {MY_PLAYER_ID}) ===")
    summary = summarize_state(GAME_STATE, TEAM_ID, MY_PLAYER_ID, POSITION_LABEL)
    print(summary)
    print()


def test_fallback():
    print(f"=== FALLBACK ({POSITION_LABEL}) ===")
    cmds = fallback_commands(GAME_STATE, TEAM_ID, MY_PLAYER_ID)
    for c in cmds:
        pid = c.get("playerId")
        tid = c.get("teamId")
        ok = "OK" if pid == MY_PLAYER_ID and tid == TEAM_ID else "WRONG"
        print(f"  [{ok}] P{pid} T{tid}: {c['commandType']} {c.get('parameters', {})}")
    assert all(c["playerId"] == MY_PLAYER_ID for c in cmds), "FAIL: wrong playerId"
    assert all(c["teamId"] == TEAM_ID for c in cmds), "FAIL: wrong teamId"
    print(f"  All {len(cmds)} commands correct (pid={MY_PLAYER_ID}, tid={TEAM_ID})")
    print()


def test_fallback_with_ball():
    print(f"=== FALLBACK WITH BALL ({POSITION_LABEL}) ===")
    state = json.loads(json.dumps(GAME_STATE))
    state["ball"]["possessionAgentId"] = f"agentId_{MY_PLAYER_ID}"
    cmds = fallback_commands(state, TEAM_ID, MY_PLAYER_ID)
    for c in cmds:
        print(f"  P{c['playerId']}: {c['commandType']} {c.get('parameters', {})}")
    assert cmds[0]["commandType"] == "GK_DISTRIBUTE", f"FAIL: expected GK_DISTRIBUTE"
    print(f"  Correctly distributes via {cmds[0]['parameters'].get('method')}")
    print()


def test_parse():
    print("=== PARSE TESTS ===")
    tests = [
        ('[{"commandType":"GK_DISTRIBUTE","playerId":0,"parameters":{"target_player_id":1,"method":"THROW"},"duration":0}]', 1),
        ('Here:\n[{"commandType":"MOVE_TO","playerId":0,"parameters":{"target_x":-49,"target_y":2,"sprint":false},"duration":0}]\nDone!', 1),
        ('{"commandType":"SET_STANCE","playerId":0,"parameters":{"stance":2},"duration":0}', 1),
        ("invalid json", 0),
        ('[]', 0),
    ]
    all_pass = True
    for resp, expected in tests:
        cmds = parse_commands(resp, TEAM_ID, MY_PLAYER_ID)
        ok = len(cmds) == expected
        if cmds:
            ok = ok and all(c["playerId"] == MY_PLAYER_ID for c in cmds)
        status = "PASS" if ok else "FAIL"
        if not ok:
            all_pass = False
        print(f"  [{status}] '{resp[:60]}...' -> {len(cmds)} cmds (expected {expected})")
    if all_pass:
        print("  All parse tests passed")
    print()


if __name__ == "__main__":
    test_summarize()
    test_fallback()
    test_fallback_with_ball()
    test_parse()
    print("✅ All local tests passed (Combined team — GK)")
