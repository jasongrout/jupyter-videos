# AGENTS.md

This file guides coding agents that work in this repository. The [README](README.md) describes the tools, the projects and the commands.

## Skills

The skills are in `.agents/skills/`.

- `release-video` (`.agents/skills/release-video/SKILL.md`): plan, record, voice and cut a release video; the owner's rules for videos and narration, and the lessons of the earlier videos. Read it before any change to a take, an edit, the voice or the cut.
- `docs-clips` (`.agents/skills/docs-clips/SKILL.md`): make or remake short silent clips for the documentation.
- `video-critic` (`.agents/skills/video-critic/SKILL.md`): critique a rendered cut with a background agent before the final render.

## Rules

- A video or a set of clips is a project in `projects/<name>/`, with its takes, its `edit.py` and its notes. The engine (`harness/`, `cut/`, `voice/`, `setup/`, `ai/`, `tools/`) holds nothing that only one project needs.
- Keep secrets and machine paths out of the repository: keys come from the environment (`OPENROUTER_API_KEY`), and paths from the variables in `env.example`.
- Everything that the tools make goes to `work/`, which git ignores: `work/runtime/` for the servers and `work/<project>/` for each project.
- Run takes, renders and benchmarks as tracked background jobs, never two of them at once, and stop processes by their PID.
- Report a blocker as soon as it shows, such as an expired key or a server that does not start.
