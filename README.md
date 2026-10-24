# ship-strava

[![CI](https://github.com/eliem08/ship-strava/actions/workflows/ci.yml/badge.svg)](https://github.com/eliem08/ship-strava/actions/workflows/ci.yml)

> **Strava for builders** — track what you ship every week.

Runners have Strava: every run logged, weekly mileage, streaks, kudos.
Builders have nothing but a GitHub contribution grid. `ship-strava` turns
your git history across all your repos into a weekly training log: ships,
streaks, personal records and a leaderboard for your crew.

## What the MVP does

- Reads `git log` across any number of local repos (no GitHub API needed)
- Per author, per ISO week: commits, lines added/removed, files touched, active
  days, and **ships** — `feat:` / `fix:` / `perf:` commits (Conventional Commits),
  merge commits of PRs, and tags (releases)
- **Streaks**: current and longest run of consecutive weeks with ≥ 1 ship
- **Personal records**: biggest week by ships, most active days in a week
- **Leaderboard** for a group of authors (ranked by ships, then active days —
  not lines of code, which rewards the wrong thing)
- **Kudos** between builders, stored in a small JSON file
- Weekly "activity summary" text like a Strava post

## Quickstart

```bash
pip install -e .
ship-strava week ~/code/umbra ~/code/agent-okta --author eliem08
ship-strava streak ~/code/* --author eliem08
ship-strava board ~/code/* --weeks 4
```

## Roadmap

- GitHub / GitLab OAuth for remote repos + deploy events (Vercel, Fly) as ships
- Clubs, challenges ("ship every day in November"), shareable weekly cards
- Privacy: only aggregates leave your machine

## Development

Zero runtime dependencies; Python 3.10+.

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
python -m unittest discover -s tests -t .           # unit + CLI smoke tests
ruff check . && ruff format --check .               # lint + format
```

```
ship_strava/core.py       domain logic (pure, importable, fully tested)
ship_strava/__main__.py   CLI (`ship-strava ...` / `python -m ship_strava ...`)
tests/                unit tests + generated CLI smoke tests
```

CI runs lint and tests on Ubuntu and Windows across Python 3.10, 3.12 and 3.13.
Design, data model, trade-offs and production path: **[ARCHITECTURE.md](ARCHITECTURE.md)**.

Part of the [agent-economy](https://github.com/eliem08/agent-economy) portfolio (idea #36).
