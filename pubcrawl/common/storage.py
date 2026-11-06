"""Site-independent SQLite archive storage."""

import fcntl
import gzip
import hashlib
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def now():
    return datetime.now(timezone.utc).isoformat()


SCHEMA = """
CREATE TABLE IF NOT EXISTS content (
 id INTEGER PRIMARY KEY, sha256 TEXT NOT NULL UNIQUE, normalized_text TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS html_blobs (
 id INTEGER PRIMARY KEY, sha256 TEXT NOT NULL UNIQUE, compression TEXT NOT NULL DEFAULT 'gzip',
 data BLOB NOT NULL
);
CREATE TABLE IF NOT EXISTS articles (
 id INTEGER PRIMARY KEY, site_article_id TEXT NOT NULL UNIQUE,
 requested_url TEXT NOT NULL, final_url TEXT NOT NULL, canonical_url TEXT,
 title TEXT NOT NULL, intro TEXT, body_text TEXT NOT NULL, authors_json TEXT NOT NULL,
 source TEXT, published_at TEXT, modified_at TEXT, section TEXT, tags_json TEXT NOT NULL,
 language TEXT, images_json TEXT NOT NULL, metadata_json TEXT NOT NULL,
 content_id INTEGER NOT NULL REFERENCES content(id), html_id INTEGER NOT NULL REFERENCES html_blobs(id),
 encoding TEXT, http_status INTEGER NOT NULL, fetched_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS url_aliases (
 url TEXT PRIMARY KEY, article_id INTEGER NOT NULL REFERENCES articles(id)
);
CREATE TABLE IF NOT EXISTS crawl_queue (
 id INTEGER PRIMARY KEY, url TEXT NOT NULL UNIQUE, kind TEXT NOT NULL,
 request_url TEXT NOT NULL, meta_json TEXT NOT NULL DEFAULT '{}', priority INTEGER NOT NULL DEFAULT 0,
 state TEXT NOT NULL DEFAULT 'pending' CHECK(state IN ('pending','in_flight','completed','failed','blocked')),
 retry_count INTEGER NOT NULL DEFAULT 0, error TEXT, http_status INTEGER,
 html_id INTEGER REFERENCES html_blobs(id), encoding TEXT, updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS queue_state ON crawl_queue(state, priority DESC, id);
CREATE INDEX IF NOT EXISTS article_content ON articles(content_id);
CREATE TABLE IF NOT EXISTS crawl_runs (
 id INTEGER PRIMARY KEY, label TEXT, started_at TEXT NOT NULL, finished_at TEXT,
 close_reason TEXT, settings_json TEXT NOT NULL, stats_json TEXT
);
CREATE TABLE IF NOT EXISTS crawl_attempts (
 id INTEGER PRIMARY KEY, run_id INTEGER REFERENCES crawl_runs(id),
 queue_id INTEGER NOT NULL REFERENCES crawl_queue(id), request_url TEXT NOT NULL,
 retry_count INTEGER NOT NULL, started_at TEXT NOT NULL, finished_at TEXT,
 outcome TEXT, http_status INTEGER, error_type TEXT, error_message TEXT
);
CREATE INDEX IF NOT EXISTS attempt_queue ON crawl_attempts(queue_id, id);
CREATE VIEW IF NOT EXISTS duplicate_content AS
 SELECT c.sha256, a.id AS article_id, a.site_article_id, a.final_url, a.title
 FROM articles a JOIN content c ON a.content_id=c.id
 WHERE a.content_id IN (SELECT content_id FROM articles GROUP BY content_id HAVING COUNT(*) > 1);
"""


class Store:
    def __init__(self, path, article_id):
        self.article_id = article_id
        path = Path(path).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = open(str(path) + ".lock", "a+")
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self.lock.close()
            raise RuntimeError(f"Another crawler is using {path}") from None
        try:
            self.db = sqlite3.connect(path)
            self.db.row_factory = sqlite3.Row
            self.db.execute("PRAGMA foreign_keys=ON")
            self.db.execute("PRAGMA journal_mode=WAL")
            self.db.execute("PRAGMA synchronous=FULL")
            version = self.db.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 2):
                raise RuntimeError(
                    f"Unsupported database schema version: {version}; use a new database for schema version 2"
                )
            self.db.executescript(SCHEMA)
            self.db.execute("PRAGMA user_version=2")
        except Exception:
            if hasattr(self, "db"):
                self.db.close()
            self.lock.close()
            raise

    def close(self):
        self.db.close()
        self.lock.close()

    def recover(self, refresh=False, retry_failed=False):
        with self.db:
            self.db.execute("UPDATE crawl_queue SET state='pending' WHERE state='in_flight'")
            if refresh:
                self.db.execute("UPDATE crawl_queue SET state='pending', request_url=url, meta_json='{}', retry_count=0 WHERE state='completed' AND kind != 'article'")
            if retry_failed:
                self.db.execute("UPDATE crawl_queue SET state='pending', request_url=url, meta_json='{}', retry_count=0, error=NULL WHERE state='failed'")

    def start_run(self, label, settings):
        result = self.db.execute(
            "INSERT INTO crawl_runs(label,started_at,settings_json) VALUES (?,?,?)",
            (label, now(), settings),
        )
        return result.lastrowid

    def end_run(self, run_id, reason, stats):
        self.db.execute(
            "UPDATE crawl_runs SET finished_at=?, close_reason=?, stats_json=? WHERE id=? AND finished_at IS NULL",
            (now(), reason, stats, run_id),
        )

    def begin_attempt(self, queue_id, run_id, request_url, retry_count):
        result = self.db.execute(
            "INSERT INTO crawl_attempts(run_id,queue_id,request_url,retry_count,started_at) VALUES (?,?,?,?,?)",
            (run_id, queue_id, request_url, retry_count, now()),
        )
        return result.lastrowid

    def end_attempt(self, attempt_id, outcome, response=None, error_type=None, error_message=None):
        if attempt_id is None:
            return
        result = self.db.execute(
            "UPDATE crawl_attempts SET finished_at=?, outcome=?, http_status=?, error_type=?, error_message=? "
            "WHERE id=? AND finished_at IS NULL",
            (now(), outcome, getattr(response, "status", None), error_type, error_message, attempt_id),
        )
        if result.rowcount != 1:
            raise RuntimeError(f"Unknown or already completed crawl attempt: {attempt_id}")

    def discover(self, url, page_kind, priority=0):
        """Caller owns the transaction, including parent completion."""
        sid = self.article_id(url) if page_kind == "article" else None
        existing = self.db.execute("SELECT id FROM articles WHERE site_article_id=?", (sid,)).fetchone() if sid else None
        if existing:
            self.db.execute("INSERT OR IGNORE INTO url_aliases VALUES (?,?)", (url, existing[0]))
            return False
        result = self.db.execute(
            "INSERT OR IGNORE INTO crawl_queue(url,kind,request_url,priority,updated_at) VALUES (?,?,?,?,?)",
            (url, page_kind, url, priority, now()))
        return result.rowcount == 1

    def saved_article(self, url):
        return self.db.execute(
            "SELECT id FROM articles WHERE site_article_id=? UNION SELECT article_id FROM url_aliases WHERE url=? LIMIT 1",
            (self.article_id(url), url)).fetchone()

    def complete_saved_alias(self, queue_id):
        result = self.db.execute(
            "UPDATE crawl_queue SET state='completed', updated_at=? WHERE id=? AND state='pending'",
            (now(), queue_id),
        )
        if result.rowcount != 1:
            raise RuntimeError(f"Cannot complete non-pending saved alias: {queue_id}")

    def blob(self, body):
        digest = hashlib.sha256(body).hexdigest()
        self.db.execute("INSERT OR IGNORE INTO html_blobs(sha256,data) VALUES (?,?)", (digest, gzip.compress(body, mtime=0)))
        return self.db.execute("SELECT id FROM html_blobs WHERE sha256=?", (digest,)).fetchone()[0]

    def save_article(self, data, response, requested_url):
        sid = self.article_id(response.url) or self.article_id(requested_url)
        existing = self.db.execute("SELECT id FROM articles WHERE site_article_id=?", (sid,)).fetchone()
        if existing:
            record_id = existing[0]
        else:
            normalized = data.pop("normalized_text")
            digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
            self.db.execute("INSERT OR IGNORE INTO content(sha256,normalized_text) VALUES (?,?)", (digest, normalized))
            content_id = self.db.execute("SELECT id FROM content WHERE sha256=?", (digest,)).fetchone()[0]
            values = dict(data, site_article_id=sid, requested_url=requested_url, final_url=response.url,
                          content_id=content_id, html_id=self.blob(response.body), encoding=response.encoding,
                          http_status=response.status, fetched_at=now())
            columns = list(values)
            record_id = self.db.execute(
                f"INSERT INTO articles({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})",
                [values[key] for key in columns]).lastrowid
        for url in {requested_url, response.url, data.get("canonical_url")} - {None}:
            self.db.execute("INSERT OR IGNORE INTO url_aliases VALUES (?,?)", (url, record_id))
        return record_id

    def finish(self, queue_id, state="completed", error=None, response=None, attempt_id=None, error_type=None):
        if state not in {"completed", "failed", "blocked"}:
            raise ValueError(f"Invalid terminal queue state: {state}")
        blob_id = self.blob(response.body) if response is not None and state == "failed" else None
        result = self.db.execute(
            "UPDATE crawl_queue SET state=?, error=?, http_status=?, html_id=?, encoding=?, updated_at=? "
            "WHERE id=? AND state='in_flight'",
            (state, error, response.status if response is not None else None, blob_id,
             getattr(response, "encoding", None), now(), queue_id),
        )
        if result.rowcount != 1:
            raise RuntimeError(f"Cannot finish non-in-flight queue entry: {queue_id}")
        self.end_attempt(attempt_id, state, response, error_type, error)
