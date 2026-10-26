import os
import shutil
import subprocess
import tempfile
import unittest
from datetime import date

from shipstreak import Kudos, leaderboard, parse_log, read_repo, records, streaks, summary, weekly
from shipstreak.core import SEP, export_log

LOG = (
    f"{SEP}a1\tSam\tsam@x.io\t2026-10-05T10:00:00+00:00\tp0\ttag: v1.0\tchore: release\n\n3\t1\tREADME.md\n"
    f"{SEP}a2\tSam\tsam@x.io\t2026-10-06T10:00:00+00:00\tp1\t\tfeat(api): add search\n\n120\t10\tapi.py\n5\t0\ttest_api.py\n"
    f"{SEP}a3\tSam\tsam@x.io\t2026-10-14T10:00:00+00:00\tp2\t\tfix: null crash\n\n2\t2\tapi.py\n"
    f"{SEP}a4\tLee\tlee@x.io\t2026-10-20T10:00:00+00:00\tp3 p4\t\tMerge pull request #7 from lee/branch\n"
    f"{SEP}a5\tSam\tsam@x.io\t2026-10-21T10:00:00+00:00\tp5\t\tdocs: typo\n\n1\t1\tREADME.md\n"
)


class Tests(unittest.TestCase):
    def setUp(self):
        self.commits = parse_log(LOG, "repo")

    def test_parse(self):
        self.assertEqual(len(self.commits), 5)
        c = self.commits[1]
        self.assertEqual((c.added, c.removed, c.files), (125, 10, 2))
        self.assertEqual(self.commits[0].tags, ["v1.0"])
        self.assertTrue(self.commits[3].is_merge and self.commits[3].is_ship)
        self.assertFalse(self.commits[4].is_ship)

    def test_weekly_streaks_records(self):
        w = weekly(self.commits, "sam")
        self.assertEqual(list(w), ["2026-W41", "2026-W42", "2026-W43"])
        self.assertEqual(w["2026-W41"]["ships"], 2)
        st = streaks(w, date(2026, 10, 21))
        self.assertEqual(st["longest"], 2)
        self.assertEqual(st["current"], 2)  # W43 has no ship yet, W42 + W41 still count
        self.assertEqual(records(w)["most_ships"], ("2026-W41", 2))
        self.assertIn("Streak: 2 week(s)", summary("2026-W41", w["2026-W41"], st))

    def test_leaderboard(self):
        board = leaderboard(self.commits, date(2026, 10, 10))
        # tie on ships (1 each); Sam wins on active days (2 vs 1)
        self.assertEqual([r["author"] for r in board], ["Sam", "Lee"])
        self.assertEqual(board[0]["ships"], board[1]["ships"])

    def test_utc_z_suffix_parses_on_all_versions(self):
        # git log %aI prints "Z" for UTC; Python 3.10 fromisoformat rejects it
        log = f"{SEP}z1\tA\ta@x\t2026-10-24T14:43:50Z\tp\t\tfeat: x\n"
        (c,) = parse_log(log)
        self.assertEqual(c.when.utcoffset().total_seconds(), 0)

    def test_kudos(self):
        with tempfile.TemporaryDirectory() as d:
            k = Kudos(os.path.join(d, "k.json"))
            k.give("lee", "sam", "2026-W41")
            k.give("lee", "sam", "2026-W41")
            k.give("sam", "sam", "2026-W41")
            self.assertEqual(Kudos(os.path.join(d, "k.json")).count("sam", "2026-W41"), 1)

    @unittest.skipUnless(shutil.which("git"), "git not installed")
    def test_real_git_repo(self):
        with tempfile.TemporaryDirectory() as d:
            env = {
                **os.environ,
                "GIT_AUTHOR_NAME": "T",
                "GIT_AUTHOR_EMAIL": "t@x",
                "GIT_COMMITTER_NAME": "T",
                "GIT_COMMITTER_EMAIL": "t@x",
            }
            subprocess.run(["git", "init", "-q", d], check=True)
            with open(os.path.join(d, "a.txt"), "w") as fh:
                fh.write("x\n")
            subprocess.run(["git", "-C", d, "add", "."], check=True)
            subprocess.run(["git", "-C", d, "commit", "-q", "-m", "feat: first"], check=True, env=env)
            commits = read_repo(d)
            self.assertEqual(len(commits), 1)
            self.assertTrue(commits[0].is_ship)
            self.assertEqual(commits[0].added, 1)
            # the export file is the web app's upload format: same commits, same repo name
            exported = os.path.join(d, "history.log")
            with open(exported, "w", encoding="utf-8") as fh:
                fh.write(export_log(d))
            again = read_repo(exported)
            self.assertEqual([(c.sha, c.repo, c.added) for c in again], [(c.sha, c.repo, c.added) for c in commits])

    def test_bundled_example_and_rejecting_non_exports(self):
        example = os.path.join(os.path.dirname(__file__), "..", "examples", "acme-app.log")
        commits = read_repo(example)
        self.assertEqual({c.repo for c in commits}, {"acme-app"})
        self.assertGreater(sum(c.is_ship for c in commits), 50)
        with tempfile.TemporaryDirectory() as d:
            junk = os.path.join(d, "notes.txt")
            with open(junk, "w", encoding="utf-8") as fh:
                fh.write("just some notes\n")
            with self.assertRaises(ValueError):
                read_repo(junk)

    def test_empty_feat_commits_are_not_ships(self):
        log = "".join(
            f"{SEP}e{i}\tSam\tsam@x.io\t2026-10-06T10:0{i}:00+00:00\tp\t\tfeat: totally real feature {i}\n"
            for i in range(5)
        )
        self.assertEqual(sum(c.is_ship for c in parse_log(log)), 0)

    def test_same_commit_and_same_person_are_counted_once(self):
        twice = parse_log(LOG, "repo") + parse_log(LOG, "fork")
        board = {r["author"]: r for r in leaderboard(twice, date(2026, 10, 1))}
        self.assertEqual(board["Sam"]["commits"], 4)
        renamed = LOG.replace("a5\tSam\t", "a5\tsam\t")
        board = leaderboard(parse_log(renamed), date(2026, 10, 1))
        self.assertEqual(len(board), 2, board)
        dup = parse_log(LOG + LOG)
        self.assertEqual(len(dup), 5)

    def test_self_kudos_ignores_case_and_write_is_atomic(self):
        with tempfile.TemporaryDirectory() as d:
            k = Kudos(os.path.join(d, "k.json"))
            k.give("Sam", "sam", "2026-W41")
            k.give(" SAM ", "Sam", "2026-W41")
            self.assertEqual(k.count("sam", "2026-W41"), 0)
            self.assertEqual(os.listdir(d), ["k.json"])


if __name__ == "__main__":
    unittest.main()
