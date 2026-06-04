---
name: air-game-dev-pm
description: Game-development PM method for turning game vision into Experience, Mainstays, Features, Levels, Tasks, Iters, heatmaps, MVP scope, and validation plans.
---

# Air Game Development PM

Use Air's PM method to plan game development from the farthest clearly foreseeable player experience back into trackable work. The method is especially useful for indie or small hybrid teams where design, tech, art, and production decisions must stay visible and reversible.

This skill follows the common `SKILL.md` Agent Skills layout and can be used by Claude Code, Codex, and other agents that read skill directories.

## Core Principles

1. **Start from the farthest foreseeable experience.**
   - Describe the farthest version of the experience that can be clearly imagined.
   - "Farthest" is not "final": it may take many iterations to become real.
   - Write it from the player's perspective first, then the designer/system perspective.

2. **Lowest power consumption.**
   - For every execution choice, ask: can this be cheaper in money, time, people, art cost, risk, or brainpower while still validating the same thing?
   - Validate high-risk, low-cost assumptions first.
   - Avoid spending final-art or production effort before the relevant risk has been reduced.

3. **Cross the river by feeling the stones.**
   - Every Iter/Sprint should produce a playable or inspectable "stone".
   - Stand on the current stone, see whether the next stone is visible, then move.
   - If a direction fails, roll back to the previous stone, not to the beginning.

4. **Keep the process continuously trackable.**
   - Use explicit levels, owners, statuses, and views.
   - Prefer heatmaps or matrices over vague progress language.
   - The team should be able to tell at a glance whether the project is balanced or lopsided.

## Planning Workflow

### 1. Define the Experience

Write a concise Experience (`E`) statement:

- **Player view:** subjective feeling, core fantasy, what the player does, how a session unfolds.
- **Designer view:** what is different, narrative/task design, systems, interactions, signature difficulty.
- **User story:** one concrete sequence of play from start to payoff.
- **Assumptions:** what must be true for this experience to work.

Do not begin with a feature list. Features serve the experience.

### 2. Split Into Mainstays

Create `Mainstay` entries for the game's highest-level supports. A Mainstay is a core pillar/basket that cannot easily be placed under another game concept.

Examples:

- `M-A` Core combat loop
- `M-B` Streaming room / audience loop
- `M-C` Level progression
- `M-D` Meta progression
- `M-Tech` Technical/system dependency

Special Mainstays can represent system dependencies. For simple projects, call them `Tech`; for complex projects, split them into `Net`, `Audio`, `Graphic`, `Pst`, etc.

### 3. Split Mainstays Into Features

Create `Feature` entries under each Mainstay.

- `F-*`: user-facing features that directly create player-perceived gameplay.
- `C-*`: capability features that support gameplay across multiple Mainstays, such as networking, save systems, audio recognition, build pipelines, or performance tooling.

Each Feature should have:

- ID: `F-A1`, `F-B3`, `C-NET-1`
- name
- owning Mainstay
- type: user-facing feature or capability feature
- dependencies, especially capability dependencies
- current Level and target Level
- owner
- current Iter focus/status
- concept or evidence link when available

### 4. Define Levels

Use Levels to express quality and validation state.

| Level | Meaning | Goal |
|---|---|---|
| `L1` | Concept case: words, sketches, paper prototype | Team consensus and early tradeoffs |
| `L2` | Concept prototype: temporary assets, graybox, procedural art | Verify "is it fun / does it work?" |
| `L3` | Implementation: stable code, UI, formal assets | Non-specialists can experience it; production viability |
| `L4` | Polish: performance, feel, balance, bug fixing | Shippable or "boutique" quality |

Do not push one Feature from L1 to L4 while neighboring core Features are still unknown. Prefer filling the same Level across the relevant Mainstays/Features before deepening.

### 5. Break Features Into Tasks

Only at the Task layer should work become directly executable.

Task fields:

- ID: `T-FA1-1`
- task name
- linked Feature
- task type: programming, design, art, tech design, QA, etc.
- owner/executor
- task status: not started / in progress / done / blocked
- owning Iter

A Task should no longer require major conceptual decomposition. If it still does, promote that thinking back to Feature or L1 work.

### 6. Plan Iters

Each Iter should contain some part of all relevant pillars, with a different Level emphasis. The game should remain "whole", even when rough.

For each Iter, define:

- goal
- target Experience
- focus Mainstays
- Features to raise in Level
- Tasks needed
- expected playable/inspectable output
- rollback condition

Example pattern:

- `Iter 0`: foundation, repo/tooling/project management table.
- `Iter 1`: simplest playable loop, raise core loop Features to L2.
- `Iter 2`: add first strategy/build layer, upgrade some previous Features to L3.
- `Iter 3`: add level/session structure, prove rhythm.
- `Iter 4+`: expand new Features from L1/L2 while polishing old Features to L3/L4.

## Output Templates

### Experience Brief

```markdown
## Experience
- Farthest foreseeable player experience:
- Player actions:
- Emotional arc:
- Concrete user story:
- Designer/system differences:
- Key assumptions:
- Lowest-cost validation:
- Rollback signal:
```

### Mainstay Table

```markdown
| Mainstay ID | Name | Description | Experience role | Owner |
|---|---|---|---|---|
| M-A |  |  |  |  |
```

### Feature Table

```markdown
| Feature ID | Name | Mainstay | Type F/C | Depends on | Current L | Target L | Owner | Iter | Status | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|
| F-A1 |  | M-A | F |  | L1 | L2 |  | Iter 1 | Todo |  |
```

### Task Table

```markdown
| Task ID | Task | Feature | Type | Owner | Iter | Status | Definition of Done |
|---|---|---|---|---|---|---|---|
| T-FA1-1 |  | F-A1 | Programming |  | Iter 1 | Todo |  |
```

### Iter Plan

```markdown
## Iter N: Name
- Goal:
- Target experience:
- Focus Mainstays:
- Features raised:
- Tasks:
- Output:
- Validation:
- Rollback condition:
```

## Review Checklist

When reviewing a plan, check:

- Does it begin with a clear player Experience, not a feature pile?
- Are assumptions explicit and ordered by risk?
- Is the proposed validation the lowest-cost way to learn?
- Are Mainstays high-level enough and mutually understandable?
- Are Features split into user-facing `F` and capability `C` where useful?
- Are Levels used as quality/validation state, not percent-complete theater?
- Is the plan balanced across pillars, or is one area racing ahead while others remain L1?
- Is every Feature owned by someone?
- Are Tasks directly executable?
- Does each Iter produce a playable or inspectable stone?
- Is the rollback point clear?

## Heatmap Guidance

Represent progress as a matrix:

- rows: Mainstays and Features
- columns: Levels or Iters
- cells: current Level/status
- colors: warm for early/uncertain, cool for mature/ordered

Look for uneven color fields. A small cool island surrounded by warm unknowns usually means premature production depth. A healthy project gradually cools across the map while preserving a whole playable shape.

### Standard Heatmap Data

Use this canonical Feature data shape when creating a live project board, Feishu Sheet/Base, CSV, or JSON:

```csv
mainstay_id,mainstay_name,feature_id,feature_name,type,depends_on,current_level,target_level,owner,iter,status,evidence
M-A,Filming Core,F-A1,Wieldable camera aiming,F,,L3,L4,Steven,Iter 4,in progress,https://...
M-Tech,Tech Capability,C-NET-1,Fusion peer ownership,C,,L2,L4,Justin,Iter 4,blocked,
```

Field rules:

- `mainstay_id`: `M-A`, `M-B`, `M-Tech`, etc.
- `feature_id`: `F-A1` for player-facing Features, `C-NET-1` for capability Features.
- `type`: `F` for user-facing gameplay, `C` for capability/system support.
- `current_level` / `target_level`: `L1`, `L2`, `L3`, `L4`.
- `status`: `todo`, `in progress`, `done`, `blocked` or Chinese equivalents.
- `evidence`: link to concept docs, builds, QA notes, videos, PRDs, or playable proof.

### Generate A Standalone 2D HTML Heatmap

Use the bundled script when a user asks for a visible global progress heatmap. Resolve the skill directory from the current agent runtime when possible. In Claude Code, prefer `${CLAUDE_SKILL_DIR}`. In Codex, use the installed skill path or the repository checkout path.

```bash
python3 ${CLAUDE_SKILL_DIR:-.}/scripts/render_heatmap.py \
  ${CLAUDE_SKILL_DIR:-.}/examples/sample_features.csv \
  --title "CAM DOWN! Global PM Heatmap" \
  --output /tmp/camdown_pm_heatmap.html
```

The script accepts CSV or JSON and outputs a single HTML file that can be opened locally or uploaded to Feishu/Miaoda. It intentionally has no external dependencies.

### Generate A Self-Contained 3D Cubic Map

Use the cubic renderer when the user wants an interactive pillar/cube view that can be shared as one file without running a local terminal server.

```bash
python3 ${CLAUDE_SKILL_DIR:-.}/scripts/render_cubic_map.py \
  ${CLAUDE_SKILL_DIR:-.}/examples/sample_features.csv \
  --title "CAM DOWN! Air PM Cubic Map" \
  --output /tmp/camdown_pm_cubic_map.html
```

The cubic renderer accepts the same CSV feature rows as `render_heatmap.py`. It also accepts nested JSON in the form `{"mainstays":[...]}` with `features` and optional `tasks`. The generated HTML embeds its JavaScript runtime, data, CSS, and app code, so the file can be opened directly from disk with no server after generation.

For "real-time" team usage, use Feishu Base/Sheet as the source of truth:

1. Keep one Feature table using the canonical fields above.
2. Use the team's preferred automation, spreadsheet export, or task API to export the latest table rows.
3. Save them as CSV/JSON.
4. Run `scripts/render_heatmap.py` for a 2D map or `scripts/render_cubic_map.py` for a self-contained 3D cubic map.
5. Share the HTML or deploy it through the team's preferred static host.

Do not treat the heatmap as a replacement for PM judgment. Use it to reveal imbalance, missing owners, blocked capability dependencies, and premature polish.

## Tone and Bias

Be practical, not bureaucratic. Favor simple tables, concrete experience stories, and explicit tradeoffs. Push back when a plan spends expensive art/production effort before validating the underlying experience. Treat special demos, investor builds, and exhibitions as valid "tilted" Iters, but name the tilt so the team does not confuse it with healthy baseline production.
