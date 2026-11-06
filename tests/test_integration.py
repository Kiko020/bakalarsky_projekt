import collections
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.database = str(self.root / "crawl.sqlite3")
        self.processes = []

    @property
    def hits(self):
        path = self.root / "hits"
        return collections.Counter(path.read_text().splitlines() if path.exists() else [])

    def tearDown(self):
        for process in self.processes:
            if process.poll() is None:
                process.kill()
            process.communicate(timeout=10)
        self.temp.cleanup()

    def launch(self, **extras):
        env = dict(os.environ, FIXTURE_DB=self.database, FIXTURE_ROOT=str(self.root), **extras)
        process = subprocess.Popen([sys.executable, "-m", "tests.run_crawler"], cwd=ROOT, env=env,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        self.processes.append(process)
        return process

    def complete(self, **extras):
        process = self.launch(**extras)
        output, _ = process.communicate(timeout=30)
        self.assertEqual(process.returncode, 0, output)
        self.assertNotIn("Unhandled error", output)
        self.assertNotIn("Traceback", output)
        return output

    def rows(self, sql):
        with sqlite3.connect(self.database) as db:
            return db.execute(sql).fetchall()

    def assert_archive(self):
        self.assertEqual(self.rows("SELECT count(*) FROM articles"), [(7,)])
        self.assertEqual(self.rows("SELECT count(*) FROM duplicate_content"), [(2,)])
        self.assertEqual(self.rows("SELECT count(*) FROM crawl_queue WHERE state IN ('pending','in_flight')"), [(0,)])
        self.assertEqual(self.rows("SELECT count(*) FROM crawl_queue WHERE state='failed'"), [(2,)])
        self.assertEqual(self.rows("SELECT count(*) FROM crawl_queue WHERE state='blocked'"), [(1,)])
        self.assertEqual(self.hits["/cl/10/109/Blocked"], 0)
        self.assertEqual(self.hits["/cl/10/104/Retry"], 3)
        self.assertEqual(self.rows("SELECT retry_count FROM crawl_queue WHERE url LIKE '%/104/%'"), [(2,)])
        self.assertEqual(self.rows("PRAGMA integrity_check"), [("ok",)])
        self.assertEqual(self.rows("SELECT close_reason FROM crawl_runs ORDER BY id DESC LIMIT 1"), [("finished",)])
        self.assertGreater(self.rows("SELECT count(*) FROM crawl_attempts")[0][0], 0)

    def test_full_crawl_resume_and_refresh(self):
        self.complete()
        self.assert_archive()
        hits = self.hits.copy()
        self.complete()
        self.assertEqual(self.hits, hits)
        (self.root / "new").touch()
        self.complete(FIXTURE_REFRESH="true")
        self.assertEqual(self.rows("SELECT count(*) FROM articles"), [(8,)])
        self.assertEqual(self.hits["/cl/10/100/First"], 1)

    def test_sita_homepage_and_rss_discover_and_store_article(self):
        self.complete(FIXTURE_SITE="sita")
        self.assertEqual(self.rows("SELECT site_article_id, title, body_text FROM articles"),
                         [("/vofinanciach/example-story", "SITA example", "Article body.")])
        self.assertEqual(self.rows("SELECT count(*) FROM crawl_queue WHERE state='completed'"), [(4,)])

    def test_teraz_homepage_rss_and_sitemap_discover_article(self):
        self.complete(FIXTURE_SITE="teraz")
        self.assertEqual(self.rows("SELECT site_article_id, title, body_text FROM articles"),
                         [("123", "Teraz example", "Article body.")])
        self.assertEqual(self.rows("SELECT count(*) FROM crawl_queue WHERE state='completed'"), [(6,)])

    def test_hlavne_spravy_homepage_and_sitemap_discover_article(self):
        self.complete(FIXTURE_SITE="hlavne_spravy")
        self.assertEqual(self.rows("SELECT site_article_id, title, body_text FROM articles"),
                         [("1234567", "Hlavné správy example", "Article body.")])
        self.assertEqual(self.rows("SELECT count(*) FROM crawl_queue WHERE state='completed'"), [(4,)])

    def test_graceful_stop_resume(self):
        self.complete(FIXTURE_CLOSE_PAGES="4")
        self.assertGreater(self.rows("SELECT count(*) FROM crawl_queue WHERE state IN ('pending','in_flight')")[0][0], 0)
        self.complete()
        self.assert_archive()

    def test_forced_termination_resume(self):
        (self.root / "slow").touch()
        process = self.launch()
        deadline = time.monotonic() + 15
        while not (self.root / "started").exists() and time.monotonic() < deadline and process.poll() is None:
            time.sleep(0.02)
        if not (self.root / "started").exists():
            process.kill()
            output, _ = process.communicate(timeout=10)
            self.fail("Crawler did not reach delayed article: " + output)
        self.assertGreater(self.rows("SELECT count(*) FROM crawl_queue WHERE state='in_flight'")[0][0], 0)
        process.kill()
        process.communicate(timeout=10)
        (self.root / "release").touch()
        self.complete()
        self.assert_archive()
        self.assertEqual(self.hits["/cl/10/100/First"], 2)
        self.assertEqual(self.hits["/cl/10/108/Child"], 1)


if __name__ == "__main__":
    unittest.main()
