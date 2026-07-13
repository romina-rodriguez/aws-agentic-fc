# Formation Inconsistency Report

## Scope

Analyzed all `src/main.py` files under `ai-team-strands-combined`:

| Agent dir | File | Declared player | Declared role |
|---|---|---:|---|
| `ai-gk` | `ai-gk/src/main.py` | 0 | GK |
| `ai-def` | `ai-def/src/main.py` | 1 | DEF |
| `ai-mid` | `ai-mid/src/main.py` | 2 | MID |
| `ai-mid2` | `ai-mid2/src/main.py` | 2 | MID |
| `ai-fwd1` | `ai-fwd1/src/main.py` | 3 | FWD1 |
| `ai-fwd2` | `ai-fwd2/src/main.py` | 4 | FWD2 |

Assumption for this review: intended outfield formation is `1-2-1`, meaning:

| Player ID | Intended role |
|---:|---|
| 0 | GK |
| 1 | DEF |
| 2 | MID |
| 3 | MID |
| 4 | FWD |

## Summary

The current combined team is internally inconsistent with a `1-2-1` formation.

The deployed/documented shape is effectively `GK-DEF-MID-FWD-FWD`, not `GK-DEF-MID-MID-FWD`. That explains the observed issue where the defender moved too far forward: the defender prompt explicitly prioritizes a through pass to forwards `3` or `4` before passing to midfielder `2`.

There is also an `ai-mid2` directory, but it uses the same player ID as `ai-mid` (`2`) and is not included in the deploy script. So the repo contains a second midfielder implementation, but it is not usable as a second midfielder in the active team.

## Findings

### 1. High: deployed team shape is `1-1-2`, not `1-2-1`

Evidence:

| File | Line | Evidence |
|---|---:|---|
| `README.md` | 96-104 | Documents player `2` as MID, player `3` as Forward 1, player `4` as Forward 2 |
| `deploy-all.sh` | 33 | Deploys `ai-gk ai-def ai-mid ai-fwd1 ai-fwd2` |

Current deployed outfield shape:

| Player ID | Active deployed agent | Role |
|---:|---|---|
| 1 | `ai-def` | DEF |
| 2 | `ai-mid` | MID |
| 3 | `ai-fwd1` | FWD |
| 4 | `ai-fwd2` | FWD |

This is one defender, one midfielder, two forwards.

Impact:

- The prompts are written around two forwards.
- DEF is encouraged to look beyond midfield.
- MID is encouraged to feed either forward.
- FWD1 and FWD2 behave as a striker pair.
- `ai-mid2` does not participate in normal deploy flow.

Recommended fix:

Choose the active `1-2-1` mapping explicitly. Suggested mapping:

| Player ID | Agent | Role |
|---:|---|---|
| 0 | `ai-gk` | GK |
| 1 | `ai-def` | DEF |
| 2 | `ai-mid` | MID |
| 3 | `ai-mid2` | MID |
| 4 | `ai-fwd2` or renamed `ai-fwd` | FWD |

Then update README, deploy script, prompts, and fallback config to match.

### 2. High: DEF first possession rule targets forwards before midfield

Evidence:

`ai-def/src/main.py`:

```text
18  1. If hasBall=True AND a forward (player 3 or 4) is ahead -> PASS type THROUGH to them
19  2. If hasBall=True -> PASS type GROUND to player 2 (midfielder)
```

Why inconsistent:

In `1-2-1`, the defender's natural first pass should usually be to a midfielder, not directly to a forward. The current first rule tells DEF to attempt a through pass to a forward whenever possible. The MID pass is only fallback.

Impact:

- DEF can seek long vertical passes.
- DEF may advance or orient too high to create/execute forward passing lanes.
- Team shape can stretch into a broken `DEF -> FWD` route.
- Midfield can be bypassed, making the `1-2-1` structure irrelevant in possession.

Recommended fix:

Change DEF possession priority to:

1. Pass ground to safest/open midfielder.
2. Pass to second midfielder if first is covered.
3. Only pass forward as an exception when clearly open and DEF can stay positioned.

Example prompt direction:

```text
1. If hasBall=True AND midfielder player 2 or 3 is available -> PASS type GROUND to best midfielder
2. If hasBall=True AND no midfielder is safe AND forward player 4 is clearly open -> PASS type THROUGH to player 4
3. If hasBall=True -> PASS type GROUND to nearest midfielder
```

### 3. High: `ai-mid2` duplicates player ID `2`

Evidence:

| File | Line | Evidence |
|---|---:|---|
| `ai-mid/src/main.py` | 12 | `MY_PLAYER_ID = 2` |
| `ai-mid2/src/main.py` | 12 | `MY_PLAYER_ID = 2` |

Why inconsistent:

Two different agent directories cannot both control player `2` in the same team. If both were deployed, they would conflict. If only one is deployed, then `ai-mid2` is dead/unused for the active formation.

Impact:

- There is no real second midfielder in the active setup.
- `ai-mid2` cannot represent player `3` or `4` until its ID changes.
- Its existence suggests a `1-2-1` migration started but was not completed.

Recommended fix:

Assign `ai-mid2` to the player ID that becomes the second midfielder.

If player `3` becomes MID:

```python
MY_PLAYER_ID = 3
POSITION_LABEL = "MID2"
```

Then remove or repurpose `ai-fwd1`, because `ai-fwd1` currently controls player `3`.

### 4. High: `ai-mid2` is not deployed by default

Evidence:

`deploy-all.sh`:

```text
33  ALL_AGENTS=("ai-gk" "ai-def" "ai-mid" "ai-fwd1" "ai-fwd2")
```

Why inconsistent:

The repo contains `ai-mid2`, but deploy-all ignores it. So even if `ai-mid2` were corrected, the default deploy still sends two forwards.

Impact:

- Match runtime will not reflect intended `1-2-1`.
- Manual deploys can diverge from normal deploys.
- README and deployment behavior disagree with a two-midfielder strategy.

Recommended fix:

For `1-2-1`, update deploy list. Example:

```bash
ALL_AGENTS=("ai-gk" "ai-def" "ai-mid" "ai-mid2" "ai-fwd2")
```

The specific forward to keep depends on which ID remains forward.

### 5. Medium: MID prompts assume two forwards

Evidence:

`ai-mid/src/main.py`:

```text
19  2. If hasBall=True AND a forward (player 3 or 4) is closer to opponent goal than me -> PASS type THROUGH to that forward
28  KEY: You are the playmaker. When you have the ball, PASS THROUGH to forwards first.
```

`ai-mid2/src/main.py`:

```text
19  2. If hasBall=True AND a forward (player 3 or 4) is ahead -> PASS type THROUGH to them
```

Why inconsistent:

In a `1-2-1`, there should be one forward, not players `3` and `4` both acting as forwards. One of those IDs should be the second midfielder.

Impact:

- Midfielders may pass through to another midfielder as if they are a striker.
- The second midfielder may be pulled into forward spaces.
- The team may collapse into a `1-1-2` attack even if names are changed.

Recommended fix:

Make MID/MID2 aware of:

- one forward target
- one midfield partner
- recycle/switch option through midfield

Example:

```text
1. If hasBall=True AND distOppGoal < 35 -> SHOOT only if lane is clear
2. If hasBall=True AND forward player 4 is ahead and open -> PASS type THROUGH to player 4
3. If hasBall=True AND midfield partner player 3/2 is safer -> PASS type GROUND to midfield partner
4. If hasBall=True -> carry into midfield space, not striker line
```

### 6. Medium: FWD1 and FWD2 cross-pass logic assumes striker pair

Evidence:

`ai-fwd1/src/main.py`:

```text
19  2. If hasBall=True AND player 4 is closer to goal than me AND distOppGoal > 45 -> PASS type THROUGH to player 4
```

`ai-fwd2/src/main.py`:

```text
19  2. If hasBall=True AND player 3 is closer to goal than me AND distOppGoal > 45 -> PASS type THROUGH to player 3
```

Why inconsistent:

This is coherent for two forwards, but not for `1-2-1`. If player `3` becomes MID, then FWD2 should not treat player `3` as a striker pair partner. If player `4` becomes MID, then FWD1 should not treat player `4` as a striker pair partner.

Impact:

- Forward may pass to a midfielder as if they are a forward running behind.
- Second midfielder may get pulled higher.
- One-forward structure becomes two-forward behavior.

Recommended fix:

Keep only one forward prompt active. Update it to:

- shoot when close
- combine with MID support when far
- hold advanced central/side space
- avoid treating the second MID as a second striker

### 7. Medium: active docs contradict intended `1-2-1`

Evidence:

`README.md` documents:

| Player ID | Position |
|---:|---|
| 0 | Goalkeeper |
| 1 | Defender |
| 2 | Midfielder |
| 3 | Forward 1 |
| 4 | Forward 2 |

Why inconsistent:

The README matches the current deployed setup, not the intended `1-2-1` setup.

Impact:

- Future prompt edits may keep reinforcing two-forward behavior.
- Anyone deploying from docs gets the wrong shape.
- `ai-mid2` remains unexplained.

Recommended fix:

Update README after final role mapping is chosen.

### 8. Medium: fallback behavior outside `main.py` also assumes two forwards

Although the requested scan focused on `main.py`, the shared fallback matters because invalid/slow LLM outputs can fall back to this logic.

Evidence:

`agentic-football-sample-agents/lib/fallback.py`:

```text
229  forwards = [p for p in players if _is_my_team(p, team_id) and _player_idx(p) in (3, 4)]
```

Also:

```text
98   FWD1_CONFIG = FallbackConfig(...)
110  FWD2_CONFIG = FallbackConfig(...)
```

Why inconsistent:

MID fallback still treats players `3` and `4` as forwards.

Impact:

- Even after prompt fixes, fallback can still produce `1-1-2` behavior.
- MID fallback may pass to the second midfielder as if they are a forward.
- DEF fallback currently passes to nearest non-GK teammate, which may be acceptable, but not explicitly role-aware.

Recommended fix:

Make fallback formation-aware or create configs for:

- `DEF_CONFIG`
- `MID1_CONFIG`
- `MID2_CONFIG`
- `FWD_CONFIG`

For `1-2-1`, MID fallback should know the single forward ID and the midfield partner ID.

## Cross-Player Role Matrix

Current prompts:

| Player ID | Agent | Role in prompt | Pass targets mentioned | Formation meaning |
|---:|---|---|---|---|
| 0 | `ai-gk` | GK | target player `2` | OK for distribution to MID |
| 1 | `ai-def` | DEF | forwards `3/4`, then MID `2` | Wrong priority for `1-2-1` |
| 2 | `ai-mid` | MID | forwards `3/4` | Assumes two forwards |
| 2 | `ai-mid2` | MID aggressive | forwards `3/4` | Duplicate ID, assumes two forwards |
| 3 | `ai-fwd1` | FWD left | player `4` | Assumes striker pair |
| 4 | `ai-fwd2` | FWD right | player `3` | Assumes striker pair |

Target `1-2-1` should look more like:

| Player ID | Role | Primary possession behavior |
|---:|---|---|
| 0 | GK | distribute to DEF/MID, usually MID |
| 1 | DEF | pass to MID1/MID2, hold defensive shape |
| 2 | MID1 | connect DEF to FWD, recycle through MID2 |
| 3 | MID2 | support MID1/FWD, not permanent striker |
| 4 | FWD | shoot/hold/run behind, combine with MIDs |

## Recommended Implementation Order

1. Choose final player ID mapping.
2. Fix `ai-mid2` player ID and label.
3. Decide which forward remains active.
4. Update `deploy-all.sh`.
5. Update DEF prompt pass priority.
6. Update MID/MID2 prompts for one forward plus midfield partner.
7. Update remaining FWD prompt.
8. Update fallback configs.
9. Update README.
10. Run local tests for each active agent.

## Concrete Minimal Fix Set

If using this mapping:

| ID | Role |
|---:|---|
| 0 | GK |
| 1 | DEF |
| 2 | MID |
| 3 | MID |
| 4 | FWD |

Then minimal files to update:

| File | Change |
|---|---|
| `ai-mid2/src/main.py` | set `MY_PLAYER_ID = 3`, `POSITION_LABEL = "MID2"` |
| `deploy-all.sh` | replace `ai-fwd1` with `ai-mid2` in `ALL_AGENTS` |
| `ai-def/src/main.py` | pass to MID `2/3` before FWD `4` |
| `ai-mid/src/main.py` | target FWD `4`; treat player `3` as midfield partner |
| `ai-mid2/src/main.py` | target FWD `4`; treat player `2` as midfield partner |
| `ai-fwd2/src/main.py` | stop treating player `3` as second striker |
| `README.md` | document `1-2-1` and active agents |
| `fallback.py` | stop treating `(3, 4)` as both forwards |

Optional cleanup:

| File/dir | Change |
|---|---|
| `ai-fwd1` | remove from deploy path, rename, or archive |
| `ai-fwd1/test_local.py` | remove/update if no longer active |

## Risk Notes

- Prompt-only changes may not be enough because fallback can still use old role assumptions.
- Deployment changes without ID changes can create duplicate control of player `2`.
- ID changes without README/deploy updates will preserve confusion.
- Keeping both `ai-fwd1` and `ai-fwd2` while saying `1-2-1` will keep producing striker-pair behavior.

## Verification Checklist

After fixes:

- `rg -n "player 3 or 4|forwards|FWD1|FWD2|MY_PLAYER_ID = 2|ALL_AGENTS" ai-* deploy-all.sh README.md`
- Confirm only one active forward prompt.
- Confirm two distinct MID player IDs.
- Confirm `deploy-all.sh` deploys five agents total: GK, DEF, MID, MID, FWD.
- Run active local tests:

```bash
python3 ai-gk/test_local.py
python3 ai-def/test_local.py
python3 ai-mid/test_local.py
python3 ai-mid2/test_local.py
python3 ai-fwd2/test_local.py
```

## Unresolved Questions

- Which ID single FWD?
- Keep `ai-fwd1` or `ai-fwd2`?
- MID2 style aggressive or balanced?