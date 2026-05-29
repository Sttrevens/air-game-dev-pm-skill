# Air Game Dev PM

Air's game-development project management method for turning a game vision into trackable Experience, Mainstay, Feature, Level, Task, and Iter planning.

This repository packages the method as a portable `SKILL.md` Agent Skill plus a small standalone heatmap renderer. It is written to work in Claude Code, Codex, and other agents that support `SKILL.md`-style skill folders.

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

## Use With Claude Code

Claude Code skills live in `~/.claude/skills/<skill-name>/SKILL.md` for personal skills, or `.claude/skills/<skill-name>/SKILL.md` for project-local skills. The directory name becomes the slash command, so install this repo as `air-game-dev-pm` if you want to invoke it as `/air-game-dev-pm`.

Personal install:

```bash
git clone https://github.com/Sttrevens/air-game-dev-pm-skill.git ~/.claude/skills/air-game-dev-pm
```

Project install:

```bash
mkdir -p .claude/skills
git clone https://github.com/Sttrevens/air-game-dev-pm-skill.git .claude/skills/air-game-dev-pm
```

Then in Claude Code:

```text
/air-game-dev-pm
```

Or ask naturally, for example: "Use Air PM to break this game feature into Mainstays, Features, Tasks, and an Iter plan."

## Use With Codex

Copy this folder into your Codex skills directory:

```bash
mkdir -p ~/.codex/skills
git clone https://github.com/Sttrevens/air-game-dev-pm-skill.git ~/.codex/skills/air-game-dev-pm
```

Then ask Codex to use `$air-game-dev-pm`.

## Use Without A Skill Runtime

You can also use the method as a plain prompt/reference. Open `SKILL.md`, paste the relevant section into any AI tool, and ask it to structure your game plan with the Experience → Mainstay → Feature → Level → Task → Iter layers.

## Generate A Heatmap

```bash
python3 scripts/render_heatmap.py examples/sample_features.csv \
  --title "Air Game Dev PM Heatmap" \
  --output /tmp/air_pm_heatmap.html
```

Open the generated HTML in a browser. The renderer has no third-party Python dependencies.

## Files

- `SKILL.md`: portable Agent Skill instructions.
- `agents/openai.yaml`: optional UI metadata for OpenAI/Codex-style agent interfaces.
- `scripts/render_heatmap.py`: standalone CSV/JSON to HTML heatmap renderer.
- `examples/sample_features.csv`: sanitized sample data.
- `examples/sample_heatmap.html`: rendered example output.

## Note

This is a working PM scaffold, not a production management platform. The useful part is the discipline: make assumptions explicit, validate with the lowest-cost playable or inspectable stone, and keep the whole game visible.
