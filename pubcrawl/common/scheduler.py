"""Persistent Scrapy scheduler shared by every site adapter."""

import json

from scrapy import Request

from .storage import Store, now


class SQLiteScheduler:
    @classmethod
    def from_crawler(cls, crawler):
        instance = cls()
        instance.crawler = crawler
        return instance

    def open(self, spider):
        self.spider = spider
        self.store = spider.store = Store(spider.db, spider.article_id)
        self.store.recover(spider.refresh_discovery, spider.retry_failed)
        self.run_id = None
        if spider.diagnostics:
            settings = {key: self.crawler.settings.get(key) for key in (
                "USER_AGENT", "ROBOTSTXT_OBEY", "CONCURRENT_REQUESTS", "CONCURRENT_REQUESTS_PER_DOMAIN",
                "DOWNLOAD_DELAY", "AUTOTHROTTLE_ENABLED", "RETRY_TIMES", "DOWNLOAD_TIMEOUT", "DOWNLOAD_MAXSIZE",
            )}
            with self.store.db:
                self.run_id = self.store.start_run(spider.run_label, json.dumps(settings, sort_keys=True))

    def close(self, reason):
        if hasattr(self, "store"):
            if getattr(self, "run_id", None) is not None:
                with self.store.db:
                    self.store.end_run(self.run_id, reason, json.dumps(self.crawler.stats.get_stats(), default=str, sort_keys=True))
            self.store.close()

    def enqueue_request(self, request):
        queue_id = request.meta.get("_queue_id")
        url = self.spider.normalize(request.url)
        if url is None:
            if queue_id is not None:
                with self.store.db:
                    self.store.finish(queue_id, "blocked", "Redirect outside allowed site hosts")
            return False
        with self.store.db:
            if queue_id is not None:
                # Redirects/retries belong to the same durable unit of work.
                result = self.store.db.execute(
                    "UPDATE crawl_queue SET state='pending', request_url=?, meta_json=?, retry_count=?, priority=?, updated_at=? "
                    "WHERE id=? AND state='in_flight'",
                    (url, json.dumps(request.meta), request.meta.get("retry_times", 0), request.priority, now(), queue_id))
                if result.rowcount != 1:
                    raise RuntimeError(f"Cannot reschedule non-in-flight queue entry: {queue_id}")
                self.store.end_attempt(request.meta.get("_attempt_id"), "rescheduled")
                return True
            page_kind = self.spider.kind(url)
            return self.store.discover(url, page_kind, request.priority) if page_kind else False

    def next_request(self):
        with self.store.db:
            while True:
                row = self.store.db.execute("SELECT * FROM crawl_queue WHERE state='pending' ORDER BY priority DESC,id LIMIT 1").fetchone()
                if row is None:
                    return None
                saved = self.store.saved_article(row["url"]) if row["kind"] == "article" else None
                if saved is None:
                    break
                self.store.db.execute("INSERT OR IGNORE INTO url_aliases VALUES (?,?)", (row["url"], saved[0]))
                self.store.complete_saved_alias(row["id"])
            result = self.store.db.execute(
                "UPDATE crawl_queue SET state='in_flight', updated_at=? WHERE id=? AND state='pending'",
                (now(), row["id"]),
            )
            if result.rowcount != 1:
                raise RuntimeError(f"Cannot claim queue entry: {row['id']}")
            attempt_id = self.store.begin_attempt(row["id"], getattr(self, "run_id", None), row["request_url"], row["retry_count"])
        meta = json.loads(row["meta_json"])
        meta.update(_queue_id=row["id"], _attempt_id=attempt_id, _kind=row["kind"], _original_url=row["url"])
        return Request(row["request_url"], callback=self.spider.parse, errback=self.spider.failed,
                       meta=meta, priority=row["priority"], dont_filter=True)

    def has_pending_requests(self):
        return self.store.db.execute("SELECT 1 FROM crawl_queue WHERE state='pending' LIMIT 1").fetchone() is not None
