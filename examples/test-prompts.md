# Test Prompts

Use these prompts to verify that the skill preserves Air PM's project-management
logic instead of producing a generic feature list.

## New Game Idea

```text
Use air-game-dev-pm to structure a co-op horror game where players film ghosts
for a live audience. Focus on the first playable stone.
```

Expected behavior: starts from player experience, then creates Mainstays,
Features, L-level targets, Tasks, and an Iter output.

## Existing Feature Pile

```text
Use air-game-dev-pm to reorganize this feature pile into Mainstays and L1-L4
evidence: camera aiming, audience chat, ghost AI, room generation, online
ownership, save system, replay export.
```

Expected behavior: separates player-facing Features from capability Features
and avoids pushing one Feature to L4 while neighbors stay undefined.

## Cubic Map Smoke Test

```text
Use air-game-dev-pm to generate a sample CSV and render the 3D cubic map.
```

Expected behavior: uses `scripts/render_cubic_map.py`; output is a
self-contained HTML file with fixed L1-L4 bands, target wireframes, and Gap
view.

## Review Existing Plan

```text
Use air-game-dev-pm to review this plan. Tell me where it is lopsided and what
the next inspectable stone should be.
```

Expected behavior: findings focus on imbalance, missing validation evidence,
blocked capability Features, and rollback signals.
