# Air Game Dev PM Skill

Air's game-development project management method for turning a game vision into trackable Experience, Mainstay, Feature, Level, Task, and Iter planning.

This repository packages the method as a Codex skill plus a small standalone heatmap renderer.

## What This Skill Helps With

- Start from the farthest clearly foreseeable player experience instead of a feature pile.
- Split a game into Mainstays, Features, executable Tasks, and Iter milestones.
- Use `L1` to `L4` as validation and maturity levels, not vague percent-complete theater.
- Keep development balanced across pillars so one area does not sprint to polish while neighboring foundations are still unknown.
- Generate a lightweight PM heatmap from CSV or JSON.

## Core Vocabulary

| Layer | Meaning |
|---|---|
| Experience | The player-facing fantasy, session, feeling, and proof target. |
| Mainstay | A high-level pillar that supports the experience. |
| Feature | A player-facing feature (`F-*`) or capability feature (`C-*`). |
| Level | Validation/maturity state: `L1` concept, `L2` prototype, `L3` implementation, `L4` polish. |
| Task | Directly executable work item. |
| Iter | A playable or inspectable stepping stone with a rollback condition. |

## Install As A Codex Skill

Copy this folder into your Codex skills directory:

```bash
mkdir -p ~/.codex/skills
cp -R air-game-dev-pm-skill ~/.codex/skills/air-game-dev-pm
```

Then ask Codex to use `$air-game-dev-pm`.

## Generate A Heatmap

```bash
python3 scripts/render_heatmap.py examples/sample_features.csv \
  --title "Air Game Dev PM Heatmap" \
  --output /tmp/air_pm_heatmap.html
```

Open the generated HTML in a browser. The renderer has no third-party Python dependencies.

## Files

- `SKILL.md`: the Codex skill instructions.
- `agents/openai.yaml`: skill metadata for agent interfaces.
- `scripts/render_heatmap.py`: standalone CSV/JSON to HTML heatmap renderer.
- `examples/sample_features.csv`: sanitized sample data.

## Note

This is a working PM scaffold, not a production management platform. The useful part is the discipline: make assumptions explicit, validate with the lowest-cost playable or inspectable stone, and keep the whole game visible.
