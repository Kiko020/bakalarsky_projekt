"""Subprocess entry point with a deterministic, socket-free fixture website."""
import asyncio
import os
from pathlib import Path
from urllib.parse import urlsplit

from scrapy.crawler import CrawlerProcess
from scrapy.http import HtmlResponse, TextResponse, XmlResponse
from scrapy.utils.project import get_project_settings

from pubcrawl.sites.topky.spider import TopkySpider
from pubcrawl.sites.sita.spider import SitaSpider
from pubcrawl.sites.teraz.spider import TerazSpider
from pubcrawl.sites.hlavne_spravy.spider import HlavneSpravySpider


class FixtureHandler:
    async def close(self):
        pass

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    async def download_request(self, request):
        root = Path(os.environ["FIXTURE_ROOT"])
        parts = urlsplit(request.url)
        path = parts.path + ("?" + parts.query if parts.query else "")
        with (root / "hits").open("a") as log:
            log.write(path + "\n")
        hits = (root / "hits").read_text().splitlines().count(path)
        status = 200
        headers = {}
        response_type = HtmlResponse
        if os.environ.get("FIXTURE_SITE") == "sita":
            article = "https://sita.sk/vofinanciach/example-story/"
            if path == "/robots.txt":
                response_type = TextResponse
                body = "User-agent: *\n"
            elif path == "/":
                body = '<a href="/vofinanciach/example-story/">Example</a>'
            elif path == "/feed/":
                response_type = XmlResponse
                body = f"<rss><channel><item><link>{article}</link></item></channel></rss>"
            elif path == "/vofinanciach/example-story/":
                body = '<html lang="sk"><h1>SITA example</h1><div class="entry-content"><p>Article body.</p></div></html>'
            else:
                status = 404
                body = "Not found"
            return response_type(request.url, status=status, headers=headers,
                                 body=body.encode("utf-8"), encoding="utf-8")
        if os.environ.get("FIXTURE_SITE") == "teraz":
            article = "https://www.teraz.sk/slovensko/example/123-clanok.html"
            if path == "/robots.txt":
                response_type = TextResponse
                body = "User-agent: *\nSitemap: https://www.teraz.sk/sitemap.xml\n"
            elif path == "/sitemap.xml":
                response_type = XmlResponse
                body = f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{article}</loc></url></urlset>'
            elif path == "/rss/vsetky-spravy.rss":
                response_type = XmlResponse
                body = f"<rss><channel><item><link>{article}</link></item></channel></rss>"
            elif path in {"/", "/najnovsie"}:
                body = f'<a href="{article}">Example</a>'
            elif path == "/slovensko/example/123-clanok.html":
                body = '<html lang="sk"><h1>Teraz example</h1><div class="article-content"><p>Article body.</p></div></html>'
            else:
                status = 404
                body = "Not found"
            return response_type(request.url, status=status, headers=headers,
                                 body=body.encode("utf-8"), encoding="utf-8")
        if os.environ.get("FIXTURE_SITE") == "hlavne_spravy":
            article = "https://www.hlavnespravy.sk/example-article/1234567"
            if path == "/robots.txt":
                response_type = TextResponse
                body = "User-agent: *\n"
            elif path == "/sitemap_index.xml":
                response_type = XmlResponse
                body = f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{article}</loc></url></urlset>'
            elif path == "/":
                body = f'<a href="{article}">Example article</a><a href="https://example.com/outside/1234567">External</a>'
            elif path == "/example-article/1234567":
                body = '<html lang="sk"><h1>Hlavné správy example</h1><div class="entry-content"><p>Article body.</p></div></html>'
            else:
                status = 404
                body = "Not found"
            return response_type(request.url, status=status, headers=headers,
                                 body=body.encode("utf-8"), encoding="utf-8")
        if path == "/robots.txt":
            response_type = TextResponse
            body = "User-agent: *\nDisallow: /cl/10/109/Blocked\nSitemap: https://www.topky.sk/sitemap.xml\n"
        elif path == "/":
            body = '<a href="/se/10/Domace">Section</a>'
            if (root / "new").exists():
                body += '<a href="/cl/10/110/New">New</a>'
        elif path == "/sitemap.xml":
            response_type = XmlResponse
            body = '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><sitemap><loc>https://www.topky.sk/archive-map.xml</loc></sitemap></sitemapindex>'
        elif path == "/archive-map.xml":
            response_type = XmlResponse
            body = '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://www.topky.sk/cl/10/103/Sitemap-only</loc></url></urlset>'
        elif path == "/se/10/Domace":
            body = '''<a href="/cl/10/100/First?utm_source=test">First</a>
            <a href="/cl/10/100/First#anchor">Repeat</a>
            <a href="/cl/10/101/Duplicate">Copy</a>
            <a href="/cl/10/102/Redirect">Redirect</a>
            <a href="/cl/10/104/Retry">Retry</a>
            <a href="/cl/10/105/Invalid">Invalid</a>
            <a href="/cl/10/106/Missing">Missing</a>
            <a href="/cl/10/109/Blocked">Blocked</a>
            <a href="/se/10/Domace?page=2">Next</a>
            <a href="https://example.com/">External</a>'''
        elif path == "/se/10/Domace?page=2":
            body = '<a href="/cl/10/107/Older">Old</a><a href="/se/10/Domace">Back</a>'
        elif path == "/cl/10/102/Redirect":
            status = 302
            headers["Location"] = "/cl/10/102/Final"
            body = "Redirect"
        elif path == "/cl/10/104/Retry" and hits < 3:
            status = 503
            body = "Try again"
        elif path == "/cl/10/105/Invalid":
            body = "<h1>No article body</h1>"
        elif path == "/cl/10/106/Missing":
            status = 404
            body = "Missing"
        else:
            if path == "/cl/10/100/First" and (root / "slow").exists():
                (root / "started").touch()
                while not (root / "release").exists():
                    await asyncio.sleep(0.02)
            text = "Identický obsah článku." if "/100/" in path or "/101/" in path else "Text pre " + path
            extra = '<a href="/cl/10/108/Child">Child</a>' if "/100/" in path else ""
            body = f'<html lang="sk"><h1>Title {path}</h1><div class="article-body"><p>{text}</p></div>{extra}</html>'
        return response_type(request.url, status=status, headers=headers, body=body.encode("utf-8"), encoding="utf-8")


if __name__ == "__main__":
    settings = get_project_settings()
    settings.setdict({
        "DOWNLOAD_HANDLERS": {"https": "tests.run_crawler.FixtureHandler"},
        "DOWNLOAD_DELAY": 0,
        "AUTOTHROTTLE_ENABLED": False,
        "LOG_LEVEL": "ERROR",
        "CONCURRENT_REQUESTS": 1,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "RETRY_TIMES": 3,
    }, priority="cmdline")
    if os.environ.get("FIXTURE_CLOSE_PAGES"):
        settings.set("CLOSESPIDER_PAGECOUNT", int(os.environ["FIXTURE_CLOSE_PAGES"]), priority="cmdline")
    process = CrawlerProcess(settings)
    spider = {
        "sita": SitaSpider,
        "teraz": TerazSpider,
        "hlavne_spravy": HlavneSpravySpider,
    }.get(os.environ.get("FIXTURE_SITE"), TopkySpider)
    process.crawl(spider, db=os.environ["FIXTURE_DB"],
                  refresh_discovery=os.environ.get("FIXTURE_REFRESH", "false"))
    process.start()
