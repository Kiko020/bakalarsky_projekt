import gzip
import io

import scrapy
from scrapy.exceptions import IgnoreRequest
from scrapy.utils.sitemap import Sitemap, sitemap_urls_from_robots


def boolean(value):
    if isinstance(value, bool):
        return value
    if str(value).lower() not in {"true", "false", "1", "0"}:
        raise ValueError("Boolean arguments must be true, false, 1, or 0")
    return str(value).lower() in {"true", "1"}


class ArchiveSpider(scrapy.Spider):
    """Shared durable crawling behavior; subclasses supply site-specific rules."""
    start_urls = ()

    def __init__(self, db=None, refresh_discovery=False, retry_failed=False,
                 run_label=None, diagnostics=True, **kwargs):
        super().__init__(**kwargs)
        self.db = db or self.default_db
        self.refresh_discovery = boolean(refresh_discovery)
        self.retry_failed = boolean(retry_failed)
        self.run_label = run_label
        self.diagnostics = boolean(diagnostics)

    async def start(self):
        for url in self.start_urls:
            yield scrapy.Request(url)

    def links(self, response, page_kind):
        if page_kind == "robots":
            for url in sitemap_urls_from_robots(response.body, response.url):
                normalized = self.normalize(url, response.url)
                if normalized:
                    yield normalized, "sitemap"
        elif page_kind == "sitemap":
            body = response.body
            if body.startswith(b"\x1f\x8b"):
                limit = self.settings.getint("DOWNLOAD_MAXSIZE") if hasattr(self, "settings") else 20 * 1024 * 1024
                with gzip.GzipFile(fileobj=io.BytesIO(body)) as compressed:
                    body = compressed.read(limit + 1)
                if len(body) > limit:
                    raise ValueError("Decompressed sitemap exceeds DOWNLOAD_MAXSIZE")
            document = Sitemap(body)
            if document.type not in {"sitemapindex", "urlset"}:
                raise ValueError("Invalid sitemap document")
            for entry in document:
                normalized = self.normalize(entry.get("loc", "").strip(), response.url)
                if normalized:
                    entry_kind = "sitemap" if document.type == "sitemapindex" else self.kind(normalized)
                    if entry_kind:
                        yield normalized, entry_kind
        else:
            for href in response.css("a::attr(href)").getall():
                normalized = self.normalize(href, response.url)
                entry_kind = self.kind(normalized) if normalized else None
                if entry_kind:
                    yield normalized, entry_kind

    def blacklist_reason(self, response):
        """Return a reason to permanently skip a response, if applicable."""
        return None

    def parse(self, response):
        queue_id = response.meta["_queue_id"]
        attempt_id = response.meta.get("_attempt_id")
        page_kind = response.meta["_kind"]
        if response.status != 200:
            with self.store.db:
                self.store.finish(queue_id, "failed", f"HTTP {response.status}", response, attempt_id,
                                  error_type="HTTPStatusError")
            self.crawler.stats.inc_value("archive/failed")
            return
        reason = self.blacklist_reason(response)
        if reason:
            with self.store.db:
                self.store.finish(queue_id, "blocked", reason, response, attempt_id,
                                  error_type="BlacklistedResponse")
            self.crawler.stats.inc_value("archive/blacklisted")
            return
        try:
            links = list(self.links(response, page_kind))
            data = self.parse_article(response) if page_kind == "article" else None
        except Exception as exc:
            # Preserve HTML on parse failures; never hash empty/non-article text.
            with self.store.db:
                self.store.finish(queue_id, "failed", f"{type(exc).__name__}: {exc}", response, attempt_id,
                                  error_type=type(exc).__name__)
            self.crawler.stats.inc_value("archive/parse_failed")
            self.logger.error("Cannot parse %s: %s", response.url, exc)
            return
        try:
            with self.store.db:
                if data:
                    self.store.save_article(data, response, response.meta["_original_url"])
                for url, entry_kind in links:
                    self.store.discover(url, entry_kind)
                self.store.finish(queue_id, response=response, attempt_id=attempt_id)
            self.crawler.stats.inc_value("archive/articles" if data else "archive/discovery_pages")
            if data:
                return data
            else:
                return None
        except Exception:
            # A database failure must not acknowledge the request or continue crawling.
            self.logger.exception("Database transaction failed; unfinished work will resume")
            self.crawler.engine.close_spider(self, reason="database_error")
            raise

    def failed(self, failure):
        """Record download failures for every archive spider.

        The durable scheduler attaches this errback to all queued requests, so
        it belongs on the shared base class rather than on one site spider.
        """
        request = failure.request
        try:
            with self.store.db:
                self.store.finish(request.meta["_queue_id"], "blocked" if failure.check(IgnoreRequest) else "failed",
                                  failure.getErrorMessage(), attempt_id=request.meta.get("_attempt_id"),
                                  error_type=failure.type.__name__)
            self.crawler.stats.inc_value("archive/failed")
        except Exception:
            self.logger.exception("Database transaction failed; unfinished work will resume")
            self.crawler.engine.close_spider(self, reason="database_error")
            raise
