# Architecture — ship-strava

## 1. Scope
A training log for builders: weekly shipping stats, streaks, records, leaderboards, kudos from git history.
**MVP:** `git log --numstat` parser (custom record separator), ship classification (Conventional
`feat/fix/perf`, PR merges, tags), ISO-week aggregation, streaks, personal records, leaderboard,
weekly summary, JSON kudos store.
**Product:** GitHub/GitLab OAuth, deploy events as ships, clubs and challenges, shareable cards.

## 2. Data flow
```mermaid
flowchart LR
  Repos[Local repos] -->|git log --all --numstat| Parser
  Parser --> Commits[Commit records]
  Commits --> Weekly[ISO-week aggregates per author]
  Weekly --> Streaks & Records & Summary
  Commits --> Board[Leaderboard]
```

## 3. Design decisions
- **Ships, not lines of code.** Leaderboards rank by ships, then active days. LOC rewards the
  wrong behaviour.
- **A record separator (`\x1e`) + tab-delimited header** makes the parser robust to subjects
  containing any printable character.
- **Current streak tolerates the in-progress week.** If you shipped last week and haven't yet this
  week, the streak is still alive, which matches how Strava treats the current period.
- **UTC `Z` normalisation** before `fromisoformat`. git prints `Z` for UTC, and Python 3.10 rejects
  it (a regression test covers this; CI caught it).
- **Local-only by default.** It reads git on your machine and only aggregates would ever be uploaded.

## 4. Production architecture
A CLI/agent posts weekly aggregates (not code) to an API. Postgres (users, clubs, weeks). OAuth
integrations for remote repos and deploy providers (Vercel, Fly). A card renderer (OG images).

## 5. Risks
Gaming via trivial `feat:` commits. Weight ships by diff size bands and deploy evidence, and
clubs can choose their scoring rules.
