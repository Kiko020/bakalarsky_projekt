import json
from pathlib import Path
import unittest

from scrapy.http import HtmlResponse, XmlResponse
from scrapy.spiderloader import SpiderLoader
from scrapy.utils.project import get_project_settings

from pubcrawl.sites.bratislavske_noviny.parser import parse_article
from pubcrawl.sites.bratislavske_noviny.spider import BratislavskeNovinySpider
from pubcrawl.sites.bratislavske_noviny.urls import article_id, kind, normalize


BASE = "https://www.bratislavskenoviny.sk"
URL = BASE + "/samosprava/90504-komunalne-volby-strana-som-slovensko-ziskala-v-bratislave-styroch-starostov"
DATED_URL = BASE + "/aktuality/bratislava/90498-stvorkoalicia-ma-v-bratislave-vacsinu-i-v-miestnych-zastupitelstvach"
FIXTURES = Path(__file__).parent / "fixtures"


def response(body=None, url=URL, headers=None):
    return HtmlResponse(url, body=body if body is not None else
                        (FIXTURES / "bratislavske_noviny_article.html").read_bytes(),
                        encoding="utf-8", headers=headers or {})


class BratislavskeNovinyTests(unittest.TestCase):
    def test_url_rules(self):
        self.assertEqual(normalize(URL.replace("https://www.", "http://") + "?utm_source=x&b=2#photo"), URL + "?b=2")
        self.assertEqual(normalize("/samosprava", URL), BASE + "/samosprava")
        for url, identifier in ((URL, "90504"), (DATED_URL, "90498")):
            self.assertEqual(article_id(url), identifier)
            self.assertEqual(kind(url), "article")
            self.assertEqual(article_id(url + "/?utm_source=x"), identifier)
        for path in ("/", "/samosprava", "/samosprava/strana-2", "/aktuality/stare-mesto", "/aktuality/stare-mesto/strana-25", "/komunalne-volby-2026"):
            self.assertEqual(kind(BASE + path), "listing", path)
        self.assertEqual(kind(BASE + "/robots.txt"), "robots")
        self.assertEqual(kind(BASE + "/sitemaps/sitemap-1.xml.gz"), "sitemap")
        for path in ("/o-nas/rss/5-rss-kanal-banoviny-sk", "/inzercia/123-slug", "/vydania", "/feed/rss2?category=banoviny-1", "/samosprava?search=x", "/samosprava/strana-0", "/html/img.jpg", "/samosprava/unknown", "/diskusia/90504-slug"):
            self.assertIsNone(kind(BASE + path), path)
        for suffix in ("/diskusia", "/galeria", "?back_url=x", "?gallery=1"):
            self.assertIsNone(kind(URL + suffix))
        self.assertIsNone(normalize("https://cloudia.banoviny.sk/rx/example"))
        self.assertIsNone(normalize("https://example.com/"))

    def test_article_text_and_metadata(self):
        item = parse_article(response(headers={"Date": "Mon, 26 Oct 2026 18:03:04 GMT"}))
        self.assertEqual(item["title"], "Komunálne voľby: Strana SOM Slovensko získala v Bratislave štyroch starostov")
        self.assertEqual(item["intro"], "Strana Obcí a miest Slovenska bola vo voľbách úspešná.")
        self.assertEqual(item["body_text"], item["intro"] + "\n\nV Bratislave obsadila štyri pozície starostov.\n\nVýsledky volieb\n\nStrana získala aj poslanecké mandáty.\n\n(ts, ms)")
        self.assertEqual(item["published_at"], "2026-10-26T12:00:00+01:00")
        self.assertEqual(item["section"], "Samospráva")
        self.assertEqual(item["language"], "sk")
        self.assertEqual(item["canonical_url"], URL)
        self.assertEqual(json.loads(item["images_json"]), ["https://cloudia.banoviny.sk/rx/example"])
        self.assertEqual(json.loads(item["authors_json"]), [])
        self.assertEqual(json.loads(item["metadata_json"])["visible_date"], "Dnes, 12:00")

    def test_dates(self):
        dated = (FIXTURES / "bratislavske_noviny_dated.html").read_bytes()
        item = parse_article(response(dated, DATED_URL))
        self.assertEqual(item["published_at"], "2026-10-25T18:15:00+01:00")
        self.assertEqual(item["section"], "Bratislava")
        raw = response().body
        yesterday = raw.replace(b"Dnes", "Včera".encode())
        self.assertEqual(parse_article(response(yesterday, headers={"Date": "Sun, 25 Oct 2026 23:30:00 GMT"}))["published_at"], "2026-10-25T12:00:00+01:00")
        for headers in ({}, {"Date": "invalid"}):
            self.assertIsNone(parse_article(response(headers=headers))["published_at"])
        missing = raw.replace(b'Dnes, <time datetime="12:00">12:00</time>', b"unknown")
        self.assertIsNone(parse_article(response(missing))["published_at"])

    def test_optional_intro_and_canonical_validation(self):
        raw = response().body
        without_intro = raw.replace(b'class="lead"', b'class="plain"')
        item = parse_article(response(without_intro))
        self.assertIsNone(item["intro"])
        self.assertNotIn("Bočný panel", item["body_text"])
        self.assertIsNone(parse_article(response(raw.replace(b"90504-", b"90599-")))["canonical_url"])
        with self.assertRaises(ValueError):
            parse_article(response(b"<h1>Title</h1><article><p>Sidebar</p></article>"))
        with self.assertRaises(ValueError):
            parse_article(response(b'<div class="c-rte"><h1>Title</h1><div class="img"><p>Credit</p></div></div>'))

    def test_spider_registration_and_discovery(self):
        spider = BratislavskeNovinySpider()
        self.assertIs(SpiderLoader(get_project_settings()).load(spider.name), BratislavskeNovinySpider)
        self.assertEqual(spider.db, "data/bratislavske-noviny-v2.sqlite3")
        listing = response(b'<a href="/samosprava/strana-2">Next</a><a href="/aktuality/stare-mesto/90502-slug">Article</a><a href="/o-nas/rss">RSS</a>')
        self.assertEqual(list(spider.links(listing, "listing")), [(BASE + "/samosprava/strana-2", "listing"), (BASE + "/aktuality/stare-mesto/90502-slug", "article")])
        robots = response(b"User-agent: *\nSitemap: https://www.bratislavskenoviny.sk/sitemap.xml\n", BASE + "/robots.txt")
        self.assertEqual(list(spider.links(robots, "robots")), [(BASE + "/sitemap.xml", "sitemap")])
        sitemap = XmlResponse(BASE + "/sitemap.xml", body=(f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{URL}</loc></url><url><loc>{BASE}/inzercia/123-ad</loc></url></urlset>').encode())
        self.assertEqual(list(spider.links(sitemap, "sitemap")), [(URL, "article")])


if __name__ == "__main__":
    unittest.main()
