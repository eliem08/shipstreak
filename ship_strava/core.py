"""Turn git history into weekly shipping stats, streaks, records and leaderboards."""

from __future__ import annotations

import json
import os
import re
import subprocess
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

__all__ = [
    "Commit",
    "parse_log",
    "read_repo",
    "weekly",
    "streaks",
    "records",
    "leaderboard",
    "summary",
    "Kudos",
    "GIT_FORMAT",
]

SEP = "\x1e"
GIT_FORMAT = f"--format={SEP}%H%x09%an%x09%ae%x09%aI%x09%P%x09%D%x09%s"
SHIP_RE = re.compile(r"^(feat|fix|perf)(\(.+\))?!?:", re.I)


@dataclass
class Commit:
    sha: str
    author: str
    email: str
    when: datetime
    subject: str
    repo: str = ""
    added: int = 0
    removed: int = 0
    files: int = 0
    is_merge: bool = False
    tags: list = field(default_factory=list)

    @property
    def is_ship(self) -> bool:
        return (
            bool(SHIP_RE.match(self.subject))
            or bool(self.tags)
            or (self.is_merge and "pull request" in self.subject.lower())
        )

    @property
    def week(self) -> str:
        y, w, _ = self.when.isocalendar()
        return f"{y}-W{w:02d}"


def _parse_iso(value: str) -> datetime:
    """git emits a trailing "Z" for UTC; datetime.fromisoformat only accepts it from Python 3.11."""
    return datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)


def parse_log(text: str, repo: str = "") -> list[Commit]:
    commits = []
    for block in text.split(SEP):
        block = block.strip("\n")
        if not block:
            continue
        lines = block.split("\n")
        parts = lines[0].split("\t")
        if len(parts) < 7:
            continue
        sha, author, email, iso, parents, refs, subject = parts[:7]
        tags = [r.strip()[5:] for r in refs.split(",") if r.strip().startswith("tag: ")]
        c = Commit(sha, author, email, _parse_iso(iso), subject, repo, is_merge=len(parents.split()) > 1, tags=tags)
        for line in lines[1:]:
            m = re.match(r"^(\d+|-)\t(\d+|-)\t", line)
            if m:
                c.added += int(m.group(1)) if m.group(1) != "-" else 0
                c.removed += int(m.group(2)) if m.group(2) != "-" else 0
                c.files += 1
        commits.append(c)
    return commits


def read_repo(path: str, since: str | None = None) -> list[Commit]:
    cmd = ["git", "-C", path, "log", "--all", "--numstat", GIT_FORMAT]
    if since:
        cmd.append(f"--since={since}")
    out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if out.returncode != 0:
        raise RuntimeError(f"{path}: {out.stderr.strip()}")
    return parse_log(out.stdout, os.path.basename(os.path.abspath(path)))


def _match(c: Commit, author: str | None) -> bool:
    return not author or author.lower() in (c.author.lower(), c.email.lower())


def weekly(commits: list[Commit], author: str | None = None) -> dict[str, dict]:
    weeks: dict[str, dict] = defaultdict(
        lambda: {"commits": 0, "ships": 0, "added": 0, "removed": 0, "files": 0, "days": set(), "repos": set()}
    )
    for c in commits:
        if not _match(c, author):
            continue
        w = weeks[c.week]
        w["commits"] += 1
        w["ships"] += c.is_ship
        w["added"] += c.added
        w["removed"] += c.removed
        w["files"] += c.files
        w["days"].add(c.when.date())
        w["repos"].add(c.repo)
    return {
        k: {**v, "active_days": len(v["days"]), "days": sorted(v["days"]), "repos": sorted(v["repos"])}
        for k, v in sorted(weeks.items())
    }


def _week_start(key: str) -> date:
    y, w = key.split("-W")
    return date.fromisocalendar(int(y), int(w), 1)


def streaks(weeks: dict[str, dict], today: date) -> dict:
    shipped = sorted(_week_start(k) for k, v in weeks.items() if v["ships"] > 0)
    longest = cur = 0
    prev = None
    for d in shipped:
        cur = cur + 1 if prev and (d - prev).days == 7 else 1
        longest = max(longest, cur)
        prev = d
    this_week = today - timedelta(days=today.weekday())
    current = 0
    if shipped and (this_week - shipped[-1]).days in (0, 7):
        current, d = 0, shipped[-1]
        s = set(shipped)
        while d in s:
            current += 1
            d -= timedelta(days=7)
    return {"current": current, "longest": longest, "weeks_shipped": len(shipped)}


def records(weeks: dict[str, dict]) -> dict:
    if not weeks:
        return {}
    best_ships = max(weeks.items(), key=lambda kv: kv[1]["ships"])
    best_days = max(weeks.items(), key=lambda kv: kv[1]["active_days"])
    return {
        "most_ships": (best_ships[0], best_ships[1]["ships"]),
        "most_active_days": (best_days[0], best_days[1]["active_days"]),
    }


def leaderboard(commits: list[Commit], since: date) -> list[dict]:
    rows: dict[str, dict] = defaultdict(lambda: {"ships": 0, "commits": 0, "days": set()})
    for c in commits:
        if c.when.date() < since:
            continue
        r = rows[c.author]
        r["ships"] += c.is_ship
        r["commits"] += 1
        r["days"].add(c.when.date())
    board = [
        {"author": a, "ships": r["ships"], "active_days": len(r["days"]), "commits": r["commits"]}
        for a, r in rows.items()
    ]
    return sorted(board, key=lambda r: (-r["ships"], -r["active_days"], r["author"]))


def summary(week_key: str, w: dict, streak: dict) -> str:
    repos = ", ".join(w["repos"]) or "-"
    return (
        f"Week {week_key}: {w['ships']} ships across {len(w['repos'])} repo(s) ({repos}), "
        f"{w['commits']} commits on {w['active_days']} days, +{w['added']}/-{w['removed']} lines. "
        f"Streak: {streak['current']} week(s) (best {streak['longest']})."
    )


class Kudos:
    def __init__(self, path: str):
        self.path = path
        self.data = {}
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                self.data = json.load(fh)

    def give(self, frm: str, to: str, week: str):
        given = self.data.setdefault(f"{to}|{week}", [])
        if frm != to and frm not in given:
            given.append(frm)
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(self.data, fh, indent=2)

    def count(self, to: str, week: str) -> int:
        return len(self.data.get(f"{to}|{week}", []))
