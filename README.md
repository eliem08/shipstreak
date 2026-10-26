<!-- sell-kit:start -->
# ShipStreak

[![CI](https://github.com/eliem08/shipstreak/actions/workflows/ci.yml/badge.svg)](https://github.com/eliem08/shipstreak/actions/workflows/ci.yml)

> **Track what you ship every week and keep the streak alive.**

**Who it's for:** Indie hackers, build-in-public founders and engineering teams.

**The problem:** Shipping consistently is what separates builders who succeed, and nothing tracks it the way a fitness app tracks runs.

**What you get:** Turn git history into weekly ships, streaks, records and team leaderboards, with empty-commit gaming filtered out.

## Quickstart

Customers receive a release archive with the wheel and the examples. Python 3.10+ and no other dependencies.

```bash
pip install shipstreak-0.1.0-py3-none-any.whl
shipstreak week examples/acme-app.log
shipstreak streak examples/acme-app.log
shipstreak board examples/acme-app.log --weeks 52
```

## Web app and API

Every command is also a JSON API endpoint and a browser form, served by the built-in web app.

```bash
shipstreak-web --port 8000          # then open http://127.0.0.1:8000
shipstreak-web keys create --label "first customer"   # prints an API key (stored hashed)
docker build -t shipstreak . && docker run -p 8000:8000 -e API_KEYS=sk_... -v shipstreak-data:/data shipstreak
```

Every API call needs `Authorization: Bearer <key>` once any key exists; a server on a public address refuses to start without one. Calls are rate-limited per key (60/min, `--rate`) and metered: `shipstreak-web usage` prints calls per key for billing.

Endpoints: `POST /api/week`, `POST /api/streak`, `POST /api/board`, `POST /api/kudos`, plus `GET /healthz` and `GET /api/spec` (machine-readable field list).
Files are sent as `{"name": ..., "content": ...}`, folders as `{"files": [...]}` or a base64 zip.

## Deploy and sell

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/eliem08/shipstreak)

`render.yaml` (one click, above) and `fly.toml` (`fly launch --copy-config`) both run the Dockerfile with a persistent `/data` volume and a `/healthz` check.
To sell self-serve, set four variables and point a Stripe webhook at `https://<your-host>/billing/webhook` (events `checkout.session.completed` and `customer.subscription.deleted`):

| Variable | Example |
|---|---|
| `STRIPE_SECRET_KEY` | `sk_live_...` |
| `STRIPE_WEBHOOK_SECRET` | `whsec_...` |
| `STRIPE_PRICES` | `team=price_123,business=price_456` |
| `PUBLIC_URL` | `https://shipstreak.example.com` |

Buyers pick a plan on `/pricing`, pay on Stripe Checkout and see their API key once on the success page. Cancelling the subscription revokes the key. A selling server always requires a key.

## Pricing

Every plan starts with a 14-day free trial. Prices in USD, billed monthly unless noted.

| Plan | Price | Includes |
|---|---|---|
| **Builder** | $5 per month | Unlimited repos; Streaks and records; Weekly summary |
| **Team** | $8 per member per month | Leaderboards; Kudos; Team summary |
| **Community** | $199 per month | Hackathons and cohorts; Public leaderboards; Branding |

To start a trial or buy a plan, [request access](https://github.com/eliem08/shipstreak/issues/new?title=ShipStreak%20trial&labels=sales).

## Licence

Proprietary. Copyright (c) 2026 eliem08. All rights reserved. Use requires a paid plan or an active trial; see [LICENSE](LICENSE).
<!-- sell-kit:end -->

## What it does

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
shipstreak week ~/code/umbra ~/code/agentwarden --author eliem08
shipstreak streak ~/code/* --author eliem08
shipstreak board ~/code/* --weeks 4
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
shipstreak/core.py       domain logic (pure, importable, fully tested)
shipstreak/__main__.py   CLI (`shipstreak ...` / `python -m shipstreak ...`)
tests/                unit tests + generated CLI smoke tests
```

CI runs lint and tests on Ubuntu and Windows across Python 3.10, 3.12 and 3.13.
Design, data model, trade-offs and production path: **[ARCHITECTURE.md](ARCHITECTURE.md)**.

Part of the [agent-economy](https://github.com/eliem08/agent-economy) portfolio (idea #36).
