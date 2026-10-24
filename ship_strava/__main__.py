import argparse
import sys
from datetime import date, timedelta

from .core import Kudos, leaderboard, read_repo, records, streaks, summary, weekly


def _load(repos):
    commits = []
    for r in repos:
        try:
            commits += read_repo(r)
        except RuntimeError as e:
            print(f"skip {e}", file=sys.stderr)
    return commits


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ship-strava")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("week", "streak"):
        p = sub.add_parser(name)
        p.add_argument("repos", nargs="+")
        p.add_argument("--author")
    b = sub.add_parser("board")
    b.add_argument("repos", nargs="+")
    b.add_argument("--weeks", type=int, default=4)
    k = sub.add_parser("kudos")
    k.add_argument("frm")
    k.add_argument("to")
    k.add_argument("--week", default=f"{date.today().isocalendar()[0]}-W{date.today().isocalendar()[1]:02d}")
    k.add_argument("--store", default="kudos.json")
    a = ap.parse_args(argv)
    if a.cmd == "kudos":
        kd = Kudos(a.store)
        kd.give(a.frm, a.to, a.week)
        print(f"{a.to} has {kd.count(a.to, a.week)} kudos for {a.week}")
        return 0
    commits = _load(a.repos)
    if a.cmd == "board":
        for i, r in enumerate(leaderboard(commits, date.today() - timedelta(weeks=a.weeks)), 1):
            print(f"{i:>2}. {r['author']:<24} {r['ships']:>4} ships  {r['active_days']:>3} days  {r['commits']:>5} commits")
        return 0
    weeks = weekly(commits, a.author)
    st = streaks(weeks, date.today())
    if a.cmd == "streak":
        print(f"current streak {st['current']} weeks, longest {st['longest']}, {st['weeks_shipped']} weeks with ships")
        rec = records(weeks)
        if rec:
            print(f"PRs: most ships {rec['most_ships'][1]} ({rec['most_ships'][0]}), most active days {rec['most_active_days'][1]} ({rec['most_active_days'][0]})")
        return 0
    if not weeks:
        print("no commits found")
        return 1
    key = list(weeks)[-1]
    print(summary(key, weeks[key], st))
    return 0


if __name__ == "__main__":
    sys.exit(main())
