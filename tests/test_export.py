import io
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

from scripts.export_articles import ExportError, export_articles


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "export_articles.py"


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.database = self.root / "archive.sqlite3"
        with sqlite3.connect(self.database) as database:
            database.execute("PRAGMA user_version=2")
            database.execute("""
                CREATE TABLE articles (
                    id INTEGER PRIMARY KEY, site_article_id TEXT NOT NULL,
                    final_url TEXT NOT NULL, title TEXT NOT NULL, intro TEXT,
                    body_text TEXT NOT NULL, authors_json TEXT NOT NULL,
                    source TEXT, published_at TEXT, modified_at TEXT,
                    section TEXT, tags_json TEXT NOT NULL, language TEXT,
                    images_json TEXT NOT NULL, metadata_json TEXT NOT NULL
                )
            """)
            database.executemany(
                "INSERT INTO articles VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                [
                    (2, "article-path", "https://www.cas.sk/article-path", "Second", None,
                     "Druhý text.", "[]", None, None, None, None, "[]", None, "[]",
                     '{"meta":{},"article_jsonld":{}}'),
                    (1, "9516997", "https://www.topky.sk/cl/10/9516997/article", "Živé správy",
                     "Úvod", "Prvý odsek.\n\nDruhý odsek.", '["Jana Nová"]', "TASR",
                     "2026-10-12T10:30:00+02:00", None, "Domáce", '["správy"]', "sk",
                     '["https://example.test/image.jpg"]',
                     '{"meta":{"og:type":"article"},"article_jsonld":{"@type":"NewsArticle"}}'),
                ],
            )

    def tearDown(self):
        self.temp.cleanup()

    def test_streams_exact_document_shape_in_database_order(self):
        output = io.StringIO()
        export_articles(self.database, output)
        documents = [json.loads(line) for line in output.getvalue().splitlines()]

        self.assertEqual([document["id"] for document in documents], ["9516997", "article-path"])
        first = documents[0]
        self.assertEqual(set(first), {"id", "url", "text", "meta"})
        self.assertEqual(first["url"], "https://www.topky.sk/cl/10/9516997/article")
        self.assertEqual(first["text"], "Prvý odsek.\n\nDruhý odsek.")
        self.assertEqual(first["meta"]["authors"], ["Jana Nová"])
        self.assertEqual(first["meta"]["tags"], ["správy"])
        self.assertEqual(first["meta"]["images"], ["https://example.test/image.jpg"])
        self.assertEqual(first["meta"]["metadata"]["article_jsonld"]["@type"], "NewsArticle")
        self.assertNotIn("http_status", first["meta"])
        self.assertIsNone(documents[1]["meta"]["intro"])

    def test_cli_writes_utf8_output_file(self):
        destination = self.root / "articles.jsonl"
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(self.database), "-o", str(destination)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertIn("Živé správy", destination.read_text(encoding="utf-8"))
        self.assertEqual(len(destination.read_text(encoding="utf-8").splitlines()), 2)

    def test_cli_streams_to_stdout(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(self.database)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(result.stdout.splitlines()), 2)
        self.assertEqual(json.loads(result.stdout.splitlines()[0])["meta"]["title"], "Živé správy")

    def test_rejects_missing_database_and_incompatible_schema(self):
        with self.assertRaisesRegex(ExportError, "database does not exist"):
            export_articles(self.root / "missing.sqlite3", io.StringIO())

        incompatible = self.root / "old.sqlite3"
        sqlite3.connect(incompatible).close()
        with self.assertRaisesRegex(ExportError, "schema version 0"):
            export_articles(incompatible, io.StringIO())

    def test_rejects_malformed_json_with_article_context(self):
        with sqlite3.connect(self.database) as database:
            database.execute("UPDATE articles SET authors_json='broken' WHERE id=1")
        with self.assertRaisesRegex(ExportError, "article '9516997'.*authors_json"):
            export_articles(self.database, io.StringIO())

    def test_refuses_to_overwrite_input_database(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(self.database), "-o", str(self.database)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("must not be the input database", result.stderr)
        with sqlite3.connect(self.database) as database:
            self.assertEqual(database.execute("SELECT count(*) FROM articles").fetchone()[0], 2)


if __name__ == "__main__":
    unittest.main()
