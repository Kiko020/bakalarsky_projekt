import gzip
import json
from pathlib import Path
import tempfile
import unittest

from scrapy import Request
from scrapy.http import HtmlResponse, XmlResponse

from pubcrawl.common.parser import normalized_text
from pubcrawl.common.scheduler import SQLiteScheduler
from pubcrawl.common.storage import Store
from pubcrawl.sites.cas.parser import parse_article as parse_cas_article
from pubcrawl.sites.cas.spider import CasSpider
from pubcrawl.sites.cas.urls import article_id as cas_article_id, kind as cas_kind, normalize as cas_normalize
from pubcrawl.sites.diva.parser import parse_article as parse_diva_article
from pubcrawl.sites.diva.spider import DivaSpider
from pubcrawl.sites.dennikn_blog.parser import parse_article as parse_dennikn_blog_article
from pubcrawl.sites.dennikn_blog.spider import DennikNBlogSpider
from pubcrawl.sites.dennikn_blog.urls import (
    article_id as dennikn_blog_article_id,
    kind as dennikn_blog_kind,
    normalize as dennikn_blog_normalize,
)
from pubcrawl.sites.diva.urls import (
    article_id as diva_article_id,
    kind as diva_kind,
    normalize as diva_normalize,
)
from pubcrawl.sites.hnonline.parser import parse_article as parse_hnonline_article
from pubcrawl.sites.hnonline.spider import HNOnlineSpider
from pubcrawl.sites.hnonline.urls import (
    article_id as hnonline_article_id,
    kind as hnonline_kind,
    normalize as hnonline_normalize,
)
from pubcrawl.sites.najmama.parser import parse_article as parse_najmama_article
from pubcrawl.sites.najmama.spider import NajmamaSpider
from pubcrawl.sites.najmama.urls import (
    article_id as najmama_article_id,
    kind as najmama_kind,
    normalize as najmama_normalize,
)
from pubcrawl.sites.koktejl.parser import parse_article as parse_koktejl_article
from pubcrawl.sites.koktejl.spider import KoktejlSpider
from pubcrawl.sites.koktejl.urls import (
    article_id as koktejl_article_id,
    kind as koktejl_kind,
    normalize as koktejl_normalize,
)
from pubcrawl.sites.pluska.parser import parse_article as parse_pluska_article
from pubcrawl.sites.pluska.spider import PluskaSpider
from pubcrawl.sites.pluska.urls import (
    article_id as pluska_article_id,
    kind as pluska_kind,
    normalize as pluska_normalize,
)
from pubcrawl.sites.pravda.parser import parse_article as parse_pravda_article
from pubcrawl.sites.pravda.spider import PravdaSpider
from pubcrawl.sites.pravda.urls import (
    article_id as pravda_article_id,
    kind as pravda_kind,
    normalize as pravda_normalize,
)
from pubcrawl.sites.pravda_blog.parser import parse_article as parse_pravda_blog_article
from pubcrawl.sites.pravda_blog.spider import PravdaBlogSpider
from pubcrawl.sites.pravda_blog.urls import (
    article_id as pravda_blog_article_id,
    kind as pravda_blog_kind,
    normalize as pravda_blog_normalize,
)
from pubcrawl.sites.sport_aktuality.parser import parse_article as parse_sport_aktuality_article
from pubcrawl.sites.sport_aktuality.spider import SportAktualitySpider
from pubcrawl.sites.sport_aktuality.urls import (
    article_id as sport_aktuality_article_id,
    kind as sport_aktuality_kind,
    normalize as sport_aktuality_normalize,
)
from pubcrawl.sites.topky.parser import parse_article
from pubcrawl.sites.topky.spider import TopkySpider
from pubcrawl.sites.topky.urls import article_id, kind, normalize
from pubcrawl.sites.zive.parser import parse_article as parse_zive_article
from pubcrawl.sites.zive.spider import ZiveSpider
from pubcrawl.sites.zive.urls import (
    article_id as zive_article_id,
    kind as zive_kind,
    normalize as zive_normalize,
)
from pubcrawl.sites.sita.parser import parse_article as parse_sita_article
from pubcrawl.sites.sita.spider import SitaSpider
from pubcrawl.sites.sita.urls import (
    article_id as sita_article_id,
    kind as sita_kind,
    normalize as sita_normalize,
)
from pubcrawl.sites.teraz.parser import parse_article as parse_teraz_article
from pubcrawl.sites.teraz.spider import TerazSpider
from pubcrawl.sites.teraz.urls import (
    article_id as teraz_article_id,
    kind as teraz_kind,
    normalize as teraz_normalize,
)
from pubcrawl.sites.hlavne_spravy.parser import parse_article as parse_hlavne_spravy_article
from pubcrawl.sites.hlavne_spravy.spider import HlavneSpravySpider
from pubcrawl.sites.hlavne_spravy.urls import (
    article_id as hlavne_spravy_article_id,
    kind as hlavne_spravy_kind,
    normalize as hlavne_spravy_normalize,
)

FIXTURE = Path(__file__).parent / "fixtures" / "article.html"
CAS_FIXTURE = Path(__file__).parent / "fixtures" / "cas_article.html"
HNONLINE_FIXTURE = Path(__file__).parent / "fixtures" / "hnonline_article.html"
KOKTEJL_FIXTURE = Path(__file__).parent / "fixtures" / "koktejl_article.html"
PLUSKA_FIXTURE = Path(__file__).parent / "fixtures" / "pluska_article.html"
PRAVDA_FIXTURE = Path(__file__).parent / "fixtures" / "pravda_article.html"
PRAVDA_BLOG_FIXTURE = Path(__file__).parent / "fixtures" / "pravda_blog_article.html"
DENNIKN_BLOG_FIXTURE = Path(__file__).parent / "fixtures" / "dennikn_blog_article.html"
SPORT_AKTUALITY_FIXTURE = Path(__file__).parent / "fixtures" / "sport_aktuality_article.html"
ZIVE_FIXTURE = Path(__file__).parent / "fixtures" / "zive_article.html"
DIVA_FIXTURE = Path(__file__).parent / "fixtures" / "diva_article.html"
NAJMAMA_FIXTURE = Path(__file__).parent / "fixtures" / "najmama_article.html"
SITA_FIXTURE = Path(__file__).parent / "fixtures" / "sita_article.html"
TERAZ_FIXTURE = Path(__file__).parent / "fixtures" / "teraz_article.html"
HLAVNE_SPRAVY_FIXTURE = Path(__file__).parent / "fixtures" / "hlavne_spravy_article.html"
URL = "https://www.topky.sk/cl/10/100/Original"


def response(body=None, url=URL):
    return HtmlResponse(url, body=body if body is not None else FIXTURE.read_bytes(), encoding="utf-8")


class ParsingTests(unittest.TestCase):
    def test_hlavne_spravy_url_rules_and_article_parser(self):
        article = "https://www.hlavnespravy.sk/kauza-graduje-banas-reaguje-na-obvinenia-lasicovej-dopustila-si-sa-niekolkych-manipulacii/4549426"
        self.assertEqual(hlavne_spravy_normalize(article.replace("https://www.", "http://")), article)
        self.assertEqual(hlavne_spravy_article_id(article), "4549426")
        self.assertEqual(hlavne_spravy_kind(article), "article")
        self.assertEqual(hlavne_spravy_kind("https://www.hlavnespravy.sk/category/titulka"), "listing")
        self.assertEqual(hlavne_spravy_kind("https://www.hlavnespravy.sk/category/titulka/page/2/"), "listing")
        self.assertEqual(hlavne_spravy_kind("https://www.hlavnespravy.sk/sitemap_index.xml"), "sitemap")
        self.assertIsNone(hlavne_spravy_kind("https://www.hlavnespravy.sk/tag/slovensko/"))
        self.assertIsNone(hlavne_spravy_normalize("https://blog.hlavnespravy.sk/"))
        self.assertIsNone(hlavne_spravy_normalize("https://example.com/"))

        item = parse_hlavne_spravy_article(
            response(HLAVNE_SPRAVY_FIXTURE.read_bytes(), article)
        )
        self.assertEqual(item["title"], "Kauza graduje. Banáš reaguje na obvinenia Lasicovej")
        self.assertEqual(item["intro"], "Jozef Banáš sa vyjadril ku konfliktu s Hanou Lasicovou.")
        self.assertIn("Jozef Banáš v najnovšom videu", item["body_text"])
        self.assertEqual(item["canonical_url"], article)
        self.assertEqual(HlavneSpravySpider().db, "data/hlavne-spravy-v2.sqlite3")

    def test_teraz_url_rules_parser_and_rss_discovery(self):
        article = "https://www.teraz.sk/slovensko/vo-volne-pohodenom-odpade-sa-najviac-na/1002857-clanok.html"
        self.assertEqual(teraz_normalize("http://teraz.sk" + article.removeprefix("https://www.teraz.sk")), article)
        self.assertEqual(teraz_article_id(article), "1002857")
        self.assertEqual(teraz_kind(article), "article")
        self.assertEqual(teraz_kind("https://www.teraz.sk/slovensko/?p=495"), "listing")
        self.assertEqual(teraz_kind("https://www.teraz.sk/rss/vsetky-spravy.rss"), "feed")
        self.assertEqual(teraz_kind("https://www.teraz.sk/sitemap.xml"), "sitemap")
        self.assertIsNone(teraz_kind("https://www.teraz.sk/rss/vsetky-spravy.rss" + "?utm_source=x&video=1"))
        self.assertIsNone(teraz_normalize("https://example.com/"))

        spider = TerazSpider()
        rss = b'''<rss><channel><item><link>http://teraz.sk/slovensko/story/123-clanok.html</link></item>
        <item><link>https://example.com/slovensko/story/123-clanok.html</link></item></channel></rss>'''
        feed = XmlResponse("https://www.teraz.sk/rss/vsetky-spravy.rss", body=rss)
        self.assertEqual(list(spider.links(feed, "feed")),
                         [("https://www.teraz.sk/slovensko/story/123-clanok.html", "article")])

        item = parse_teraz_article(response(TERAZ_FIXTURE.read_bytes(), article))
        self.assertEqual(item["title"], "ANALÝZA: Čo sa najviac nachádzalo vo voľne pohodenom odpade?")
        self.assertEqual(item["intro"], "Počas tohtoročnej analýzy sa voľne pohodený odpad zbieral celkovo v 28 lokalitách.")
        self.assertIn("cigaretové ohorky", item["body_text"])
        self.assertEqual(item["canonical_url"], article)
        self.assertEqual(item["published_at"], "2026-10-26T11:41:00+02:00")
        self.assertEqual(TerazSpider().db, "data/teraz-v2.sqlite3")

    def test_sita_url_rules_parser_and_rss_discovery(self):
        article = "https://sita.sk/vofinanciach/ruska-centralna-banka-pokracuje-v-znizovani-zlatych-rezerv-moze-to-suvisiet-s-vydavkami-na-vojnu/"
        self.assertEqual(sita_normalize("http://www.sita.sk" + article.removeprefix("https://sita.sk")), article)
        self.assertEqual(sita_kind(article), "article")
        self.assertEqual(sita_article_id(article), "/vofinanciach/ruska-centralna-banka-pokracuje-v-znizovani-zlatych-rezerv-moze-to-suvisiet-s-vydavkami-na-vojnu")
        self.assertEqual(sita_kind("https://sita.sk/vofinanciach/"), "listing")
        self.assertEqual(sita_kind("https://sita.sk/page/2/"), "listing")
        self.assertEqual(sita_kind("https://sita.sk/feed/"), "feed")
        self.assertIsNone(sita_kind("https://sita.sk/tag/zlato/"))
        self.assertIsNone(sita_normalize("https://example.com/"))

        spider = SitaSpider()
        rss = b'''<rss><channel><item><link>https://www.sita.sk/vofinanciach/story/</link></item>
        <item><link>https://sita.sk/tag/not-an-article/</link></item></channel></rss>'''
        feed = XmlResponse("https://sita.sk/feed/", body=rss)
        self.assertEqual(list(spider.links(feed, "feed")),
                         [("https://sita.sk/vofinanciach/story/", "article")])
        item = parse_sita_article(response(
            SITA_FIXTURE.read_bytes(), article,
        ))
        self.assertEqual(item["title"], "Ruská centrálna banka pokračuje v znižovaní zlatých rezerv")
        self.assertEqual(item["intro"], "Znižovanie zlatých rezerv plánuje aj Kazachstan.")
        self.assertIn("Svetové ceny zlata", item["body_text"])
        self.assertEqual(item["canonical_url"], article)
        self.assertEqual(item["published_at"], "2026-10-25T20:49:00+02:00")
        self.assertEqual(SitaSpider().db, "data/sita-v2.sqlite3")

    def test_dennikn_blog_url_rules_parser_and_discovery_boundary(self):
        article_url = (
            "http://www.dennikn.sk/blog/5650497/bellove-nerovnosti-i-dokaz-"
            "ze-zijeme-v-simulacii-alebo-dokaz-sporom/?utm_source=x#discussion"
        )
        canonical = (
            "https://dennikn.sk/blog/5650497/bellove-nerovnosti-i-dokaz-"
            "ze-zijeme-v-simulacii-alebo-dokaz-sporom/"
        )
        self.assertEqual(dennikn_blog_normalize(article_url), canonical)
        self.assertEqual(dennikn_blog_article_id(canonical), "5650497")
        self.assertEqual(dennikn_blog_kind("https://dennikn.sk/blog/"), "listing")
        self.assertEqual(dennikn_blog_kind("https://dennikn.sk/zoznam-blogerov/"), "listing")
        self.assertEqual(dennikn_blog_kind("https://dennikn.sk/autor/statocnych/"), "author")
        for excluded in (
            "https://dennikn.sk/", "https://dennikn.sk/spravy/",
            "https://dennikn.sk/api/sitemap/root", "https://example.com/blog/5650497/slug/",
        ):
            self.assertIsNone(dennikn_blog_kind(excluded))
        item = parse_dennikn_blog_article(response(DENNIKN_BLOG_FIXTURE.read_bytes(), canonical))
        self.assertEqual(item["title"], "Bellove nerovnosti a dôkaz sporom")
        self.assertEqual(item["body_text"], "Úvod článku.\n\nPrvý odsek.\n\nZáver")
        self.assertEqual(item["published_at"], "2026-10-20T08:30:00+02:00")

        spider = DennikNBlogSpider()
        directory = response(b'''<a href="/autor/statocnych/">Bloger</a>
            <a href="/spravy/politika/">News</a>''', "https://dennikn.sk/zoznam-blogerov/")
        self.assertEqual(list(spider.links(directory, "listing")), [
            ("https://dennikn.sk/autor/statocnych/", "author"),
        ])
        profile = response(b'''<a href="/blog/5650497/post/">Blog</a>
            <a href="/spravy/politika/">Paywalled news</a>
            <a href="/autor/other/">Other profile</a>''', "https://dennikn.sk/autor/statocnych/")
        self.assertEqual(list(spider.links(profile, "author")), [
            ("https://dennikn.sk/blog/5650497/post/", "article"),
        ])
        self.assertEqual(spider.db, "data/dennikn-blog-v2.sqlite3")

    def test_metadata_and_clean_body(self):
        item = parse_article(response())
        self.assertEqual(item["title"], "Slovenská správa")
        self.assertEqual(json.loads(item["authors_json"]), ["Jana Nová"])
        self.assertEqual(item["published_at"], "2026-10-12T10:30:00+02:00")
        self.assertEqual(item["source"], "TASR")
        self.assertEqual(item["section"], "Domáce")
        self.assertEqual(item["language"], "sk")
        self.assertEqual(json.loads(item["tags_json"]), ["Slovensko", "správy"])
        self.assertTrue(item["body_text"].startswith("BRATISLAVA"))
        self.assertIn("Ďalší vývoj", item["body_text"])
        self.assertNotIn("Reklama", item["body_text"])
        self.assertNotIn("Odporúčaný", item["body_text"])

    def test_missing_metadata_and_invalid_json(self):
        body = b'<script type="application/ld+json">broken</script><h1>Some <b>title</b></h1><div class="article-body"><p>Body.</p></div>'
        item = parse_article(response(body))
        self.assertEqual(item["title"], "Some title")
        self.assertEqual(item["body_text"], "Body.")
        self.assertIsNone(item["published_at"])
        self.assertEqual(json.loads(item["authors_json"]), [])

    def test_jsonld_only_and_intro_once(self):
        item = parse_article(response(b'<h1>T</h1><article><p class="perex">Intro.</p><p>Body.</p></article>'))
        self.assertEqual(item["body_text"].count("Intro."), 1)
        item = parse_article(response(b'<script type="application/ld+json">{"@type":"NewsArticle","headline":"T","articleBody":"Body."}</script>'))
        self.assertEqual(item["body_text"], "Body.")

    def test_reject_empty_article_and_foreign_canonical(self):
        with self.assertRaises(ValueError):
            parse_article(response(b"<h1>Title only</h1>"))
        body = FIXTURE.read_bytes().replace(b"/cl/10/100/Canonical-title", b"/cl/10/999/Wrong")
        self.assertIsNone(parse_article(response(body))["canonical_url"])

    def test_unicode_normalization(self):
        self.assertEqual(normalized_text("článok\n  dnes"), normalized_text("c\u030cla\u0301nok dnes"))
        self.assertNotEqual(normalized_text("Text"), normalized_text("text"))

    def test_url_rules(self):
        self.assertEqual(normalize("http://topky.sk/cl/10/100/x?utm_source=x&b=2&a=1#part"),
                         "https://www.topky.sk/cl/10/100/x?a=1&b=2")
        self.assertNotEqual(normalize("/se/10/Domace?page=1"), normalize("/se/10/Domace?page=2"))
        for url in ("https://sportky.zoznam.sk/", "https://foo.topky.sk/", "javascript:alert(1)", "https://www.topky.sk:bad/"):
            self.assertIsNone(normalize(url))
        self.assertIsNone(kind("https://www.topky.sk/cl/10/100/x/galeria/1"))

    def test_sitemap_parser_accepts_gzip_and_rejects_invalid_xml(self):
        spider = TopkySpider()
        xml = (b'<?xml version="1.0" encoding="UTF-8"?>'
               b'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
               b'<url><loc>https://www.topky.sk/cl/10/100/From-map</loc></url></urlset>')
        sitemap = response(gzip.compress(xml), "https://www.topky.sk/sitemap.xml.gz")
        self.assertEqual(list(spider.links(sitemap, "sitemap")),
                         [("https://www.topky.sk/cl/10/100/From-map", "article")])
        with self.assertRaises(ValueError):
            list(spider.links(response(b"<html>not a sitemap</html>", "https://www.topky.sk/sitemap.xml"), "sitemap"))

    def test_cas_url_rules_and_article_parser(self):
        url = "https://cas.sk/spravy/domace/novy-clanok?utm_source=x&b=2#a"
        self.assertEqual(cas_normalize(url), "https://www.cas.sk/spravy/domace/novy-clanok?b=2")
        self.assertEqual(cas_kind("https://www.cas.sk/spravy/2/"), "listing")
        self.assertEqual(cas_kind("https://www.cas.sk/spravy/domace/novy-clanok"), "article")
        self.assertIsNone(cas_kind("https://www.cas.sk/tag/slovensko"))
        self.assertEqual(cas_article_id("https://www.cas.sk/spravy/domace/novy-clanok/"), "/spravy/domace/novy-clanok")
        body = b'''<html lang="sk"><head><link rel="canonical" href="/spravy/domace/novy-clanok" />
        <meta property="article:published_time" content="2026-10-12T10:30:00+02:00" /></head>
        <body><h1>Cas clanok</h1><div class="perex">Uvod.</div>
        <div class="article-body"><p>Uvod.</p><p>Telo clanku.</p></div></body></html>'''
        item = parse_cas_article(response(body, "https://www.cas.sk/spravy/domace/novy-clanok"))
        self.assertEqual(item["canonical_url"], "https://www.cas.sk/spravy/domace/novy-clanok")
        self.assertEqual(item["body_text"].count("Uvod."), 1)
        self.assertEqual(item["published_at"], "2026-10-12T10:30:00+02:00")
        self.assertEqual(CasSpider().db, "data/cas-v2.sqlite3")

    def test_koktejl_url_rules_and_article_parser(self):
        url = ("http://koktejl.azet.sk/clanok/A7KZW8H/serialova-arabela/"
               "?utm_source=x&b=2#a")
        normalized = "https://koktejl.azet.sk/clanok/A7KZW8H/serialova-arabela/?b=2"
        self.assertEqual(koktejl_normalize(url), normalized)
        self.assertEqual(koktejl_article_id(url), "A7KZW8H")
        self.assertEqual(koktejl_kind(normalized), "article")
        self.assertEqual(koktejl_kind("https://koktejl.azet.sk/?page=2"), "listing")
        self.assertEqual(
            koktejl_kind("https://koktejl.azet.sk/celebrity/domace-promi/?page=3"),
            "listing",
        )
        for excluded in (
            "https://koktejl.azet.sk/fotogaleria/A7KZW8H/serialova-arabela/1/",
            "https://koktejl.azet.sk/clanok/A7KZW8H/serialova-arabela/gallery/",
            "https://koktejl.azet.sk/celebrity/?sort=popular",
            "https://koktejl.azet.sk/clanok/TOO-SHORT/serialova-arabela/",
        ):
            with self.subTest(excluded=excluded):
                self.assertIsNone(koktejl_kind(excluded))
        self.assertIsNone(koktejl_normalize("https://www.aktuality.sk/"))

        spider = KoktejlSpider()
        listing = b'''<a href="/celebrity/?page=2">Next</a>
        <a href="/clanok/A7KZW8H/serialova-arabela/">Article</a>
        <a href="/fotogaleria/A7KZW8H/serialova-arabela/1/">Gallery</a>
        <a href="https://example.com/clanok/1234567/foreign/">Offsite</a>'''
        self.assertEqual(
            list(spider.links(response(listing, "https://koktejl.azet.sk/celebrity/"),
                              "listing")),
            [
                ("https://koktejl.azet.sk/celebrity/?page=2", "listing"),
                ("https://koktejl.azet.sk/clanok/A7KZW8H/serialova-arabela/", "article"),
            ],
        )

        item = parse_koktejl_article(response(
            KOKTEJL_FIXTURE.read_bytes(),
            "https://koktejl.azet.sk/clanok/A7KZW8H/serialova-arabela/",
        ))
        self.assertEqual(item["title"], "FOTO Seriálová Arabela zbadala zábery z Európy")
        self.assertEqual(item["intro"], "Povedala to jasne.")
        self.assertEqual(json.loads(item["authors_json"]), ["jž"])
        self.assertEqual(item["published_at"], "2026-10-20T13:00:00+02:00")
        self.assertEqual(item["modified_at"], "2026-10-20T13:05:00+02:00")
        self.assertEqual(item["section"], "Celebrity")
        self.assertEqual(item["language"], "sk")
        self.assertEqual(json.loads(item["images_json"]),
                         ["https://img.aktuality.sk/hero.jpg"])
        self.assertEqual(
            item["canonical_url"],
            "https://koktejl.azet.sk/clanok/A7KZW8H/serialova-arabela/",
        )
        self.assertEqual(
            item["body_text"],
            "Povedala to jasne.\n\n"
            "Prvý odsek obsahuje dôležitý text a odkaz.\n\n"
            "Čo sa deje vo Francúzsku?\n\n"
            "Druhý odsek článku.\n\n"
            "Prvá položka.\n\nDruhá položka.",
        )
        self.assertEqual(item["body_text"].count("Povedala to jasne."), 1)
        for unwanted in ("Fotogaléria", "Reklama", "Odporúčaný"):
            self.assertNotIn(unwanted, item["body_text"])
        self.assertEqual(spider.db, "data/koktejl-v2.sqlite3")

    def test_cas_excludes_horoscopes_and_quizzes(self):
        spider = CasSpider()
        excluded = [
            f"https://www.cas.sk/{section}{suffix}"
            for section in ("horoskopy", "kvizy", "HOROSKOPY", "KVIZY")
            for suffix in ("", "/", "/2", "/novy-clanok", "/tema/novy-clanok?strana=2")
        ]
        for url in excluded:
            with self.subTest(url=url):
                self.assertIsNone(cas_kind(url))
        allowed = "https://www.cas.sk/prominenti/novy-clanok"
        urls = excluded + [allowed]
        html = "".join(f'<a href="{url}">Link</a>' for url in urls)
        self.assertEqual(list(spider.links(response(html.encode(), "https://www.cas.sk/"), "listing")),
                         [(allowed, "article")])
        sitemap = '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(
            f"<url><loc>{url}</loc></url>" for url in urls) + "</urlset>"
        self.assertEqual(list(spider.links(response(sitemap.encode(), "https://www.cas.sk/sitemap.xml"), "sitemap")),
                         [(allowed, "article")])
        self.assertEqual(cas_kind("https://www.cas.sk/prominenti/horoskopy-a-kvizy"), "article")
        self.assertEqual(cas_kind("https://www.cas.sk/kvizy-novinky/clanok"), "article")

    def test_cas_body_blocks_exclude_surrounding_content(self):
        url = "https://www.cas.sk/prominenti/novy-clanok"
        item = parse_cas_article(response(CAS_FIXTURE.read_bytes(), url))
        self.assertEqual(item["title"], "Celý titulok článku")
        self.assertEqual(json.loads(item["authors_json"]), ["Sára Surová"])
        self.assertEqual(item["source"], "TASR")
        self.assertEqual(item["modified_at"], "2026-10-19T15:16:07+02:00")
        self.assertEqual(item["section"], "Prominenti")
        self.assertEqual(json.loads(item["tags_json"]), ["USA", "New York"])
        self.assertEqual(json.loads(item["images_json"]), ["https://www.cas.sk/hero.jpg"])
        self.assertEqual(item["body_text"],
                         "Úvod článku.\n\n"
                         "Prvý odsek obsahuje dôležitý text a odkaz.\n\n"
                         "Tvrdá realita v USA\n\n"
                         "Druhý odsek článku.")
        self.assertEqual(item["body_text"].count("Úvod článku."), 1)
        for unwanted in ("Reklama", "Odporúčaný", "Prehrať", "Popis fotografie",
                         "Najčítanejšie", "Cudzí titulok", "Zdroj:", "19. 10. 2026",
                         "FOTO Homolu"):
            self.assertNotIn(unwanted, item["body_text"])
            self.assertNotIn(unwanted, item["normalized_text"])

    def test_cas_standalone_gallery_prompts(self):
        url = "https://www.cas.sk/prominenti/novy-clanok"
        for href in ("https://www.cas.sk/gal/prominenti/novy-clanok",
                     "https://cas.sk/galeria/novy-clanok?itm_position=1",
                     "/galerie/novy-clanok", "/foto/novy-clanok",
                     "../gal/novy-clanok"):
            for block in ("paragraphBlock", "headingBlock"):
                with self.subTest(href=href, block=block):
                    html = f'''<h1>Titulok</h1><p class="perex">Úvod.</p>
                    <section id="bodyBlockAdvertisementGeneratorComponentId">
                    <div id="paragraphBlock-1"><p>Prvý odsek.</p></div>
                    <div id="{block}-2"> <strong><a href="{href}">
                    Pozrite <em>fotografie</em></a></strong> </div>
                    <div id="paragraphBlock-3"><p>Druhý odsek.</p></div>
                    </section>'''
                    item = parse_cas_article(response(html.encode(), url))
                    self.assertEqual(item["body_text"],
                                     "Úvod.\n\nPrvý odsek.\n\nDruhý odsek.")
                    self.assertNotIn("Pozrite", item["normalized_text"])

    def test_cas_preserves_substantive_text_and_other_links(self):
        url = "https://www.cas.sk/prominenti/novy-clanok"
        contents = (
            '<h2>Fotografie z cesty</h2>',
            '<h2><a href="/prominenti/dalsi-clanok">Ďalší článok</a></h2>',
            '<p><a href="https://example.com/gal/fotky">Externý odkaz</a></p>',
            '<p><a href="/galantny-clanok">Bežný odkaz</a></p>',
            '<p>Otec navštívil dcéru. <a href="/gal/fotky">Pozrite fotografie</a>.</p>',
            '<p><a href="/gal/fotky">Fotografie</a> zachytávajú stretnutie.</p>',
            '<p><a href="/gal/fotky">Fotografie</a> a '
            '<a href="/prominenti/rozhovor">rozhovor</a></p>',
        )
        for content in contents:
            with self.subTest(content=content):
                html = f'''<h1>Titulok</h1>
                <section id="bodyBlockAdvertisementGeneratorComponentId">
                <div id="headingBlock-1">{content}</div></section>'''
                page = response(html.encode(), url)
                expected = " ".join(page.css("section").xpath("string(.)").get().split())
                self.assertEqual(parse_cas_article(page)["body_text"], expected)

    def test_cas_gallery_only_body_does_not_fall_back_to_page_text(self):
        html = b'''<article><h1>Title</h1><p>Unrelated content</p>
        <section id="bodyBlockAdvertisementGeneratorComponentId">
        <div id="headingBlock-1"><a href="/gal/photos">Gallery prompt</a></div>
        </section></article>'''
        with self.assertRaises(ValueError):
            parse_cas_article(response(html, "https://www.cas.sk/prominenti/clanok"))

    def test_pravda_url_rules_and_article_parser(self):
        url = "http://pravda.sk/spravy/domace/clanok/2061883-stary-slug?utm_source=x&b=2#a"
        self.assertEqual(
            pravda_normalize(url),
            "https://www.pravda.sk/spravy/domace/clanok/2061883-stary-slug?b=2",
        )
        self.assertEqual(pravda_article_id(url), "2061883")
        self.assertEqual(
            pravda_article_id("https://www.pravda.sk/auto/clanok/2061883-novy-slug"),
            "2061883",
        )
        self.assertEqual(pravda_kind("https://www.pravda.sk/spravy/domace?strana=2"), "listing")
        self.assertEqual(
            pravda_kind("https://www.pravda.sk/cdn/sitemap/www.pravda.sk-19.xml"),
            "sitemap",
        )
        self.assertEqual(
            pravda_kind("https://www.pravda.sk/spravy/domace/clanok/2061883-clanok"),
            "article",
        )
        self.assertIsNone(pravda_kind("https://www.pravda.sk/trendove-temy/politika"))
        self.assertIsNone(pravda_kind("https://www.pravda.sk/vyhladavanie?q=test"))
        self.assertIsNone(pravda_normalize("https://spravy.pravda.sk/domace/"))

        item = parse_pravda_article(response(
            PRAVDA_FIXTURE.read_bytes(),
            "https://www.pravda.sk/spravy/domace/clanok/2061883-pravda-clanok",
        ))
        self.assertEqual(item["title"], "Pravda titulok článku")
        self.assertEqual(item["intro"], "Úvod článku.")
        self.assertEqual(json.loads(item["authors_json"]), ["Pravda"])
        self.assertEqual(item["published_at"], "2026-10-19T15:00:00+02:00")
        self.assertEqual(item["section"], "Domáce")
        self.assertEqual(json.loads(item["tags_json"]), ["Slovensko", "Politika"])
        self.assertEqual(json.loads(item["images_json"]), ["https://www.pravda.sk/hero.jpg"])
        self.assertEqual(item["language"], "sk")
        self.assertEqual(
            item["canonical_url"],
            "https://www.pravda.sk/spravy/domace/clanok/2061883-pravda-clanok",
        )
        self.assertEqual(
            item["body_text"],
            "Úvod článku.\n\n"
            "Prvý odsek obsahuje dôležitý text a odkaz.\n\n"
            "Medzititulok článku\n\n"
            "Druhý odsek článku.\n\n"
            "Citácia v článku.\n\n"
            "Prvá položka.\n\n"
            "Druhá položka.",
        )
        self.assertEqual(item["body_text"].count("Úvod článku."), 1)
        for unwanted in ("Prehrať video", "Reuters", "Odporúčaný", "Cudzí text",
                         "Reklama", "Autorské práva", "Zdieľať"):
            self.assertNotIn(unwanted, item["body_text"])
        self.assertEqual(PravdaSpider().db, "data/pravda-v2.sqlite3")

    def test_pravda_blog_url_rules_and_article_parser(self):
        url = ("http://MULINKOVAMUDROST.blog.pravda.sk/2026/10/20/"
               "vallo-opat-zachranuje-bratislavu-tentoraz-pred-kym/?utm_source=x&b=2#a")
        normalized = ("https://mulinkovamudrost.blog.pravda.sk/2026/10/20/"
                      "vallo-opat-zachranuje-bratislavu-tentoraz-pred-kym/?b=2")
        self.assertEqual(pravda_blog_normalize(url), normalized)
        self.assertEqual(
            pravda_blog_article_id(url),
            "mulinkovamudrost.blog.pravda.sk/2026/10/20/"
            "vallo-opat-zachranuje-bratislavu-tentoraz-pred-kym",
        )
        self.assertEqual(pravda_blog_kind(normalized), "article")
        self.assertEqual(pravda_blog_kind("https://blog.pravda.sk/sitemap/sitemap_posts_01.xml"),
                         "sitemap")
        self.assertEqual(pravda_blog_kind("https://blog.pravda.sk/abecedny-zoznam-blogov/page/2/"),
                         "listing")
        self.assertEqual(pravda_blog_kind("https://autor.blog.pravda.sk/page/3/"), "listing")
        for excluded in (
            "https://autor.blog.pravda.sk/tag/politika/",
            "https://autor.blog.pravda.sk/category/nazory/",
            "https://autor.blog.pravda.sk/wp-json/wp/v2/posts/1",
            "https://spravy.pravda.sk/domace/",
            "https://nested.autor.blog.pravda.sk/2026/10/20/clanok/",
        ):
            self.assertIsNone(pravda_blog_normalize(excluded) if "nested." in excluded or
                              "spravy." in excluded else pravda_blog_kind(excluded))

        item = parse_pravda_blog_article(response(PRAVDA_BLOG_FIXTURE.read_bytes(), normalized))
        self.assertEqual(item["title"], "Vallo opäť zachraňuje Bratislavu. Tentoraz pred kým?")
        self.assertEqual(json.loads(item["authors_json"]), ["mulinkovamudrost"])
        self.assertEqual(item["published_at"], "2026-10-20T12:09:00+02:00")
        self.assertEqual(item["section"], "Nezaradené")
        self.assertEqual(json.loads(item["tags_json"]), ["Bratislava", "Vallo"])
        self.assertEqual(item["language"], "sk-SK")
        self.assertEqual(
            item["body_text"],
            "Úvod blogového článku.\n\n"
            "Prvý odsek obsahuje dôležitý text a odkaz.\n\n"
            "Medzititulok\n\nCitácia.\n\nPrvá položka.\n\nDruhá položka.",
        )
        self.assertNotIn("Reklama", item["body_text"])
        self.assertEqual(PravdaBlogSpider().db, "data/pravda-blog-v2.sqlite3")

    def test_pravda_blog_sitemap_discovers_cross_subdomain_urls(self):
        spider = PravdaBlogSpider()
        xml = b'''<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url><loc>https://autor.blog.pravda.sk</loc></url>
        <url><loc>https://autor.blog.pravda.sk/2020/01/02/starsi-clanok/</loc></url>
        <url><loc>https://spravy.pravda.sk/domace/</loc></url></urlset>'''
        page = response(xml, "https://blog.pravda.sk/sitemap/sitemap_posts_01.xml")
        self.assertEqual(list(spider.links(page, "sitemap")), [
            ("https://autor.blog.pravda.sk/", "listing"),
            ("https://autor.blog.pravda.sk/2020/01/02/starsi-clanok/", "article"),
        ])

    def test_hnonline_url_rules_and_article_parser(self):
        url = ("http://www.hnonline.sk/finweb/ekonomika/96264906-stary-slug"
               "?utm_source=x&b=2#a")
        self.assertEqual(
            hnonline_normalize(url),
            "https://hnonline.sk/finweb/ekonomika/96264906-stary-slug?b=2",
        )
        self.assertEqual(hnonline_article_id(url), "96264906")
        self.assertEqual(
            hnonline_article_id("https://hnonline.sk/svet/7-historicky-clanok"),
            "7",
        )
        self.assertEqual(hnonline_kind("https://hnonline.sk/finweb/ekonomika"), "listing")
        self.assertEqual(
            hnonline_kind("https://hnonline.sk/sitemap-hnonline-sk-21.xml.gz"),
            "sitemap",
        )
        self.assertEqual(
            hnonline_kind("https://hnonline.sk/finweb/ekonomika/96264906-clanok"),
            "article",
        )
        for excluded in (
            "https://hnonline.sk/tag/deficit",
            "https://hnonline.sk/autor/tasr-5963",
            "https://hnonline.sk/predplatne/tlacene-tituly/96016056-diabetik",
            "https://hnonline.sk/cdn-cgi/content",
            "https://hnonline.sk/hn24",
            "https://hnonline.sk/tv/kategorie/aktualne-videa/48014293-epidemiologicka-do-exotiky-mieria-plne-lietadla-slovakov-polovica-pasazierov-jedneho-letu-sa-vratila",
        ):
            with self.subTest(excluded=excluded):
                self.assertIsNone(hnonline_kind(excluded))
        self.assertIsNone(hnonline_normalize("https://hn24.hnonline.sk/hn24"))

        article_url = ("https://hnonline.sk/finweb/ekonomika/"
                       "96264906-bez-dalsej-konsolidacie")
        item = parse_hnonline_article(response(HNONLINE_FIXTURE.read_bytes(), article_url))
        self.assertEqual(
            item["title"],
            "Bez ďalšej konsolidácie sa deficit v budúcom roku vráti nad päť percent HDP",
        )
        self.assertEqual(
            item["intro"],
            "Z tohtoročných 4,5 percenta by mal budúci rok narásť na 5,3 percenta HDP.",
        )
        self.assertEqual(json.loads(item["authors_json"]), ["TASR"])
        self.assertEqual(item["published_at"], "2026-02-13T09:42:00+01:00")
        self.assertEqual(item["modified_at"], "2026-02-13T09:43:49+01:00")
        self.assertEqual(item["section"], "Finweb")
        self.assertEqual(item["language"], "sk-sk")
        self.assertEqual(
            json.loads(item["tags_json"]),
            ["Rada pre rozpočtovú zodpovednosť", "deficit", "kosnolidácia", "konsolidačný balíček"],
        )
        self.assertEqual(
            json.loads(item["images_json"]),
            ["https://static.hnonline.sk/images/slike/2026/02/13/o_6013950_1024.jpg"],
        )
        self.assertEqual(
            item["canonical_url"],
            ("https://hnonline.sk/finweb/ekonomika/96264906-"
             "bez-dalsej-konsolidacie-sa-deficit-v-buducom-roku-vrati-nad-pat-percent-hdp"),
        )
        self.assertEqual(
            item["body_text"],
            "Z tohtoročných 4,5 percenta by mal budúci rok narásť na 5,3 percenta HDP.\n\n"
            "Bez dodatočných opatrení vzrastie deficit slovenských verejných financií.\n\n"
            "Potrebné budú ďalšie opatrenia\n\n"
            "Predikcia vychádza z aktuálneho stavu legislatívy.\n\n"
            "Deficity zostanú na neudržateľne vysokých úrovniach.\n\n"
            "Prvý dôsledok.\n\nDruhý dôsledok.",
        )
        self.assertEqual(item["body_text"].count(item["intro"]), 1)
        for unwanted in ("Text vloženého widgetu", "Odporúčaný cudzí článok"):
            self.assertNotIn(unwanted, item["body_text"])
        self.assertEqual(HNOnlineSpider().db, "data/hnonline-v2.sqlite3")

    def test_hnonline_sitemap_index_and_child_discovery(self):
        spider = HNOnlineSpider()
        index = b'''<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <sitemap><loc>https://hnonline.sk/sitemap-hnonline-sk-21.xml.gz</loc></sitemap>
        </sitemapindex>'''
        page = response(index, "https://hnonline.sk/sitemap-index-hnonline-sk.xml.gz")
        self.assertEqual(list(spider.links(page, "sitemap")), [
            ("https://hnonline.sk/sitemap-hnonline-sk-21.xml.gz", "sitemap"),
        ])
        child = b'''<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url><loc>https://hnonline.sk/finweb/podniky-a-trhy/9750-starsi-clanok</loc></url>
        <url><loc>https://hnonline.sk/predplatne/tlacene-tituly/96016056-diabetik</loc></url>
        </urlset>'''
        page = response(child, "https://hnonline.sk/sitemap-hnonline-sk-21.xml.gz")
        self.assertEqual(list(spider.links(page, "sitemap")), [
            ("https://hnonline.sk/finweb/podniky-a-trhy/9750-starsi-clanok", "article"),
        ])

    def test_sport_aktuality_url_rules_and_article_parser(self):
        url = ("http://sport.aktuality.sk/hokej/clanok/montreal-canadiens-kirby-dach-"
               "hlada-centra-nhl-2026102008300986634?utm_source=x&b=2#a")
        normalized = ("https://sport.aktuality.sk/hokej/clanok/montreal-canadiens-kirby-dach-"
                      "hlada-centra-nhl-2026102008300986634?b=2")
        self.assertEqual(sport_aktuality_normalize(url), normalized)
        self.assertEqual(sport_aktuality_article_id(url), "2026102008300986634")
        self.assertEqual(sport_aktuality_kind(normalized), "article")
        self.assertEqual(
            sport_aktuality_kind("https://sport.aktuality.sk/najnovsie-spravy?page=109"),
            "listing",
        )
        self.assertEqual(sport_aktuality_kind("https://sport.aktuality.sk/hokej-nhl"),
                         "listing")
        self.assertEqual(
            sport_aktuality_kind("https://sport.aktuality.sk/autor/sportsk-2023042410242333744"),
            "listing",
        )
        for excluded in (
            "https://sport.aktuality.sk/hokej/clanok/example-2026102008300986634/comments",
            "https://sport.aktuality.sk/futbal/zapasy",
            "https://sport.aktuality.sk/page/o-nas",
            "https://sport.aktuality.sk/rss/hokej/",
        ):
            with self.subTest(excluded=excluded):
                self.assertIsNone(sport_aktuality_kind(excluded))
        self.assertIsNone(sport_aktuality_normalize("https://www.aktuality.sk/"))

        item = parse_sport_aktuality_article(response(
            SPORT_AKTUALITY_FIXTURE.read_bytes(), normalized,
        ))
        self.assertEqual(item["title"], "Zemetrasenie v Montreale")
        self.assertEqual(item["intro"], "Úvod športového článku.")
        self.assertEqual(json.loads(item["authors_json"]), ["(mh)", "ŠPORT.sk"])
        self.assertEqual(item["published_at"], "2026-10-20T11:15:00+02:00")
        self.assertEqual(item["modified_at"], "2026-10-20T11:18:16+02:00")
        self.assertEqual(item["section"], "HOKEJ, NHL")
        self.assertEqual(json.loads(item["tags_json"]),
                         ["Montreal Canadiens", "NHL", "kirby dach"])
        self.assertEqual(item["language"], "sk")
        self.assertEqual(json.loads(item["images_json"]), ["https://images.example/sport.jpg"])
        self.assertEqual(item["canonical_url"], normalized.split("?", 1)[0])
        self.assertEqual(
            item["body_text"],
            "Úvod športového článku.\n\n"
            "Prvý medzititulok\n\n"
            "Prvý odsek obsahuje dôležitý text.\n\n"
            "Druhý odsek článku.\n\n"
            "Prvá položka.\n\nDruhá položka.",
        )
        for unwanted in ("Reklama", "widgetu", "sociálneho", "Odporúčaný", "Cudzí", "Diskusia"):
            self.assertNotIn(unwanted, item["body_text"])
        self.assertEqual(SportAktualitySpider().db, "data/sport-aktuality-v2.sqlite3")

    def test_zive_url_rules_and_article_parser(self):
        url = ("http://zive.aktuality.sk/clanok/6BmffxT/chysta-samsung-pri-galaxy-s27-"
               "neprijemne-prekvapenie-tykat-sa-ma-pamati/?utm_source=x&b=2#article")
        normalized = ("https://zive.aktuality.sk/clanok/6BmffxT/chysta-samsung-pri-galaxy-s27-"
                      "neprijemne-prekvapenie-tykat-sa-ma-pamati/?b=2")
        self.assertEqual(zive_normalize(url), normalized)
        self.assertEqual(zive_article_id(normalized), "6BmffxT")
        self.assertEqual(zive_kind(normalized), "article")
        self.assertEqual(zive_kind("https://zive.aktuality.sk/spravy?page=3"), "listing")
        self.assertEqual(zive_kind("https://zive.aktuality.sk/robots.txt"), "robots")
        self.assertEqual(zive_kind("https://zive.aktuality.sk/sitemap-news.xml.gz"), "sitemap")
        for excluded in (
            "https://zive.aktuality.sk/autor/redakcia",
            "https://zive.aktuality.sk/tag/samsung",
            "https://zive.aktuality.sk/clanok/6BmffxT/slug/diskusia",
            "https://zive.aktuality.sk/spravy?search=query",
        ):
            with self.subTest(excluded=excluded):
                self.assertIsNone(zive_kind(excluded))
        self.assertIsNone(zive_normalize("https://www.aktuality.sk/"))

        item = parse_zive_article(response(
            ZIVE_FIXTURE.read_bytes(), normalized.split("?", 1)[0],
        ))
        self.assertEqual(item["title"], "Chystá Samsung pri Galaxy S27 nepríjemné prekvapenie? Týkať sa má pamätí")
        self.assertEqual(item["intro"], "Línia Galaxy S27 bude uvedená v budúcom roku.")
        self.assertEqual(json.loads(item["authors_json"]), ["redakcia Živé.sk"])
        self.assertEqual(item["published_at"], "2026-10-21T19:13:00+02:00")
        self.assertEqual(item["section"], "Mobilmania")
        self.assertEqual(json.loads(item["tags_json"]), ["Samsung", "Galaxy S27"])
        self.assertEqual(item["language"], "sk")
        self.assertEqual(json.loads(item["images_json"]), ["https://images.example/galaxy.jpg"])
        self.assertEqual(item["canonical_url"], normalized.split("?", 1)[0])
        self.assertIn("Len 8 GB RAM?", item["body_text"])
        self.assertNotIn("Odporúčaný obsah", item["body_text"])
        spider = ZiveSpider()
        self.assertEqual(spider.db, "data/zive-v2.sqlite3")
        self.assertEqual(list(spider.links(response(
            b'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            b'<url><loc>https://zive.aktuality.sk/clanok/6BmffxT/slug/</loc></url>'
            b'<url><loc>https://zive.aktuality.sk/tag/test</loc></url></urlset>',
            "https://zive.aktuality.sk/sitemap-news.xml",
        ), "sitemap")), [("https://zive.aktuality.sk/clanok/6BmffxT/slug/", "article")])

    def test_diva_url_rules_and_article_parser(self):
        url = ("http://diva.aktuality.sk/clanok/62x73dB/odmietala-ho-objat-aj-ked-ju-o-to-"
               "pocas-boja-so-zakernou-chorobou-prosil-az-dnes-hovori-o-rozvode-zivot-po-"
               "jej-boku-nebol-idealny/?utm_source=x&b=2#article")
        normalized = ("https://diva.aktuality.sk/clanok/62x73dB/odmietala-ho-objat-aj-ked-ju-o-to-"
                      "pocas-boja-so-zakernou-chorobou-prosil-az-dnes-hovori-o-rozvode-zivot-po-"
                      "jej-boku-nebol-idealny/?b=2")
        self.assertEqual(diva_normalize(url), normalized)
        self.assertEqual(diva_article_id(normalized), "62x73dB")
        self.assertEqual(diva_kind(normalized), "article")
        self.assertEqual(diva_kind("https://diva.aktuality.sk/celebrity/2"), "listing")
        self.assertEqual(diva_kind("https://diva.aktuality.sk/tema/kriza/"), "listing")
        self.assertEqual(diva_kind("https://diva.aktuality.sk/autor/redakcia-divask/59/"), "listing")
        self.assertEqual(diva_kind("https://diva.aktuality.sk/robots.txt"), "robots")
        self.assertEqual(diva_kind("https://diva.aktuality.sk/sitemap-index.xml.gz"), "sitemap")
        for excluded in (
            "https://diva.aktuality.sk/forum/",
            "https://diva.aktuality.sk/katalog/",
            "https://diva.aktuality.sk/tag/rozvod/",
            "https://diva.aktuality.sk/clanok/62x73dB/slug/diskusia",
            "https://diva.aktuality.sk/celebrity?search=here",
        ):
            with self.subTest(excluded=excluded):
                self.assertIsNone(diva_kind(excluded))
        self.assertIsNone(diva_normalize("https://www.aktuality.sk/"))

        item = parse_diva_article(response(
            DIVA_FIXTURE.read_bytes(), normalized.split("?", 1)[0],
        ))
        self.assertEqual(item["title"], "Odmietala ho objať, aj keď ju o to počas boja so zákernou chorobou prosil")
        self.assertEqual(item["intro"], "Až dnes hovorí o rozvode a živote po jej boku.")
        self.assertEqual(json.loads(item["authors_json"]), ["Redakcia Diva.sk"])
        self.assertEqual(item["published_at"], "2026-10-25T10:30:00+02:00")
        self.assertEqual(item["section"], "Celebrity")
        self.assertEqual(json.loads(item["tags_json"]), ["rozvod", "vzťahy"])
        self.assertEqual(item["language"], "sk")
        self.assertEqual(json.loads(item["images_json"]), ["https://images.example/diva-story.jpg"])
        self.assertEqual(item["canonical_url"], normalized.split("?", 1)[0])
        self.assertIn("Život po jej boku nebol ideálny", item["body_text"])
        self.assertNotIn("Odporúčaný obsah", item["body_text"])

        spider = DivaSpider()
        self.assertEqual(spider.db, "data/diva-v2.sqlite3")
        self.assertEqual(list(spider.links(response(
            b'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            b'<url><loc>https://diva.aktuality.sk/clanok/62x73dB/slug/</loc></url>'
            b'<url><loc>https://diva.aktuality.sk/forum/</loc></url></urlset>',
            "https://diva.aktuality.sk/sitemap-index.xml",
        ), "sitemap")), [("https://diva.aktuality.sk/clanok/62x73dB/slug/", "article")])

    def test_najmama_url_rules_and_article_parser(self):
        url = ("http://najmama.aktuality.sk/clanok/9qfg4aJ/preco-babatka-casto-stikutaju-"
               "kychaju-ci-hlasno-dychaju-7-zvlastnych-ale-uplne-prirodzenych-veci-ktore-"
               "robia-novorodeniatka/?utm_source=x&b=2#article")
        normalized = ("https://najmama.aktuality.sk/clanok/9qfg4aJ/preco-babatka-casto-stikutaju-"
                      "kychaju-ci-hlasno-dychaju-7-zvlastnych-ale-uplne-prirodzenych-veci-ktore-"
                      "robia-novorodeniatka/?b=2")
        self.assertEqual(najmama_normalize(url), normalized)
        self.assertEqual(najmama_article_id(normalized), "9qfg4aJ")
        self.assertEqual(najmama_kind(normalized), "article")
        self.assertEqual(najmama_kind("https://najmama.aktuality.sk/tehotenstvo/2"), "listing")
        self.assertEqual(najmama_kind("https://najmama.aktuality.sk/temy/"), "listing")
        self.assertEqual(najmama_kind("https://najmama.aktuality.sk/tema/novorodeniatka/"), "listing")
        self.assertEqual(najmama_kind("https://najmama.aktuality.sk/autor/redakcia/3/"), "listing")
        self.assertEqual(najmama_kind("https://najmama.aktuality.sk/robots.txt"), "robots")
        self.assertEqual(najmama_kind("https://najmama.aktuality.sk/sitemap-main.xml.gz"), "sitemap")
        for excluded in (
            "https://najmama.aktuality.sk/forum/",
            "https://najmama.aktuality.sk/katalog/",
            "https://najmama.aktuality.sk/tag/babatka/",
            "https://najmama.aktuality.sk/clanok/9qfg4aJ/slug/diskusia",
            "https://najmama.aktuality.sk/tehotenstvo?search=here",
        ):
            with self.subTest(excluded=excluded):
                self.assertIsNone(najmama_kind(excluded))
        self.assertIsNone(najmama_normalize("https://www.aktuality.sk/"))

        item = parse_najmama_article(response(
            NAJMAMA_FIXTURE.read_bytes(), normalized.split("?", 1)[0],
        ))
        self.assertEqual(item["title"], "Prečo bábätká často štikútajú, kýchajú či hlasno dýchajú? 7 zvláštnych, ale úplne prirodzených vecí, ktoré robia novorodeniatka")
        self.assertEqual(item["intro"], "Aj vás to ako čerstvú mamičku prekvapilo?")
        self.assertEqual(json.loads(item["authors_json"]), ["Mária Sanatová"])
        self.assertEqual(item["published_at"], "2025-11-05T06:30:00+01:00")
        self.assertEqual(item["section"], "Dojčatá")
        self.assertEqual(json.loads(item["tags_json"]), ["bábätká", "novorodeniatka"])
        self.assertEqual(item["language"], "sk")
        self.assertEqual(json.loads(item["images_json"]), ["https://images.example/novorodeniatka.jpg"])
        self.assertEqual(item["canonical_url"], normalized.split("?", 1)[0])
        self.assertIn("Hlasné dýchanie a čudné zvuky", item["body_text"])
        self.assertNotIn("Podobné články", item["body_text"])

        spider = NajmamaSpider()
        self.assertEqual(spider.db, "data/najmama-v2.sqlite3")
        self.assertEqual(list(spider.links(response(
            b'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            b'<url><loc>https://najmama.aktuality.sk/clanok/9qfg4aJ/slug/</loc></url>'
            b'<url><loc>https://najmama.aktuality.sk/forum/</loc></url></urlset>',
            "https://najmama.aktuality.sk/sitemap-main.xml",
        ), "sitemap")), [("https://najmama.aktuality.sk/clanok/9qfg4aJ/slug/", "article")])

    def test_pluska_url_rules_article_parser_and_sitemap_discovery(self):
        tracked = (
            "http://pluska.sk/regiony/znamu-banku-zasiahol-vypadok-ludia-sa-"
            "nevedia-dostat-k-peniazom?itm_modul=list&b=2&utm_source=x#gallery"
        )
        article_url = (
            "https://www1.pluska.sk/regiony/znamu-banku-zasiahol-vypadok-ludia-sa-"
            "nevedia-dostat-k-peniazom?b=2"
        )
        self.assertEqual(pluska_normalize(tracked), article_url)
        self.assertEqual(
            pluska_article_id(article_url),
            "/regiony/znamu-banku-zasiahol-vypadok-ludia-sa-nevedia-dostat-k-peniazom",
        )
        self.assertEqual(pluska_kind(article_url), "article")
        self.assertEqual(pluska_kind("https://www1.pluska.sk/r/regiony?page=2"), "listing")
        self.assertEqual(
            pluska_kind("https://www1.pluska.sk/premium/regiony/premium-clanok"),
            "article",
        )
        for excluded in (
            "https://www1.pluska.sk/tag/slovensko",
            "https://www1.pluska.sk/autor/erika-vojtasakova",
            "https://www1.pluska.sk/gal/regiony/clanok/2",
            "https://www1.pluska.sk/diskusia/regiony/clanok",
            "https://www1.pluska.sk/premium/predplatne",
        ):
            with self.subTest(excluded=excluded):
                self.assertIsNone(pluska_kind(excluded))
        self.assertIsNone(pluska_normalize("https://sport24.pluska.sk/clanok"))

        item = parse_pluska_article(response(PLUSKA_FIXTURE.read_bytes(), article_url))
        self.assertEqual(
            item["title"],
            "Známu banku zasiahol výpadok: Ľudia sa nevedia dostať k peniazom",
        )
        self.assertEqual(item["intro"], "Známa banka hlási výpadok.")
        self.assertEqual(json.loads(item["authors_json"]), ["Erika Vojtašáková"])
        self.assertEqual(item["published_at"], "2026-10-20T13:18:44+02:00")
        self.assertEqual(item["modified_at"], "2026-10-20T13:19:00+02:00")
        self.assertEqual(item["section"], "Regióny")
        self.assertEqual(item["language"], "sk")
        self.assertEqual(json.loads(item["tags_json"]), ["Slovensko", "Peniaze"])
        self.assertEqual(json.loads(item["images_json"]),
                         ["https://images.example/revolut.jpg"])
        self.assertEqual(item["canonical_url"], article_url.split("?", 1)[0])
        self.assertEqual(
            item["body_text"],
            "Známa banka hlási výpadok.\n\n"
            "Výpadok Revolutu\n\n"
            "Prvý odsek obsahuje dôležitý text a odkaz.\n\n"
            "Problémy hlásia aj Slováci\n\n"
            "Druhý odsek článku.",
        )
        for unwanted in ("Zhrnutie", "Odporúčaný", "Newsletter"):
            self.assertNotIn(unwanted, item["body_text"])
        self.assertEqual(PluskaSpider().db, "data/pluska-v2.sqlite3")

        spider = PluskaSpider()
        index = b'''<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <sitemap><loc>https://www1.pluska.sk/sitemaps/plus1-articles-index.xml</loc></sitemap>
        </sitemapindex>'''
        self.assertEqual(list(spider.links(response(
            index, "https://www1.pluska.sk/sitemaps/plus1-sitemap.xml"), "sitemap")), [
                ("https://www1.pluska.sk/sitemaps/plus1-articles-index.xml", "sitemap"),
            ])
        child = b'''<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url><loc>https://www1.pluska.sk/regiony/novy-clanok</loc></url>
        <url><loc>https://www1.pluska.sk/tag/slovensko</loc></url>
        </urlset>'''
        self.assertEqual(list(spider.links(response(
            child, "https://www1.pluska.sk/sitemaps/plus1-articles-1.xml"), "sitemap")), [
                ("https://www1.pluska.sk/regiony/novy-clanok", "article"),
            ])


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "test.sqlite3"
        self.store = Store(self.path, article_id)

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def save(self, res):
        with self.store.db:
            return self.store.save_article(parse_article(res), res, res.url)

    def test_duplicates_preserve_html_and_metadata(self):
        first = response()
        second = response(FIXTURE.read_bytes().replace(b"<head>", b"<head><!--changed markup-->"),
                          "https://www.topky.sk/cl/11/101/Copy")
        self.save(first)
        self.save(second)
        self.save(first)
        db = self.store.db
        self.assertEqual(db.execute("SELECT count(*) FROM articles").fetchone()[0], 2)
        self.assertEqual(db.execute("SELECT count(*) FROM content").fetchone()[0], 1)
        self.assertEqual(db.execute("SELECT count(*) FROM html_blobs").fetchone()[0], 2)
        self.assertEqual(db.execute("SELECT count(*) FROM duplicate_content").fetchone()[0], 2)
        blob = db.execute("SELECT data FROM html_blobs ORDER BY id LIMIT 1").fetchone()[0]
        self.assertEqual(gzip.decompress(blob), first.body)
        third = response(FIXTURE.read_bytes().replace(b"Druh", b"Treti"), "https://www.topky.sk/cl/10/102/Different")
        self.save(third)
        self.assertEqual(db.execute("SELECT count(*) FROM content").fetchone()[0], 2)

    def test_transaction_rollback_and_recovery(self):
        with self.store.db:
            self.store.discover(URL, "article")
            self.store.db.execute("UPDATE crawl_queue SET state='in_flight'")
        with self.assertRaises(RuntimeError):
            with self.store.db:
                self.store.save_article(parse_article(response()), response(), URL)
                self.store.discover("https://www.topky.sk/cl/10/102/Child", "article")
                self.store.finish(1)
                raise RuntimeError("simulated crash before commit")
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM articles").fetchone()[0], 0)
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM crawl_queue").fetchone()[0], 1)
        self.store.recover()
        self.assertEqual(self.store.db.execute("SELECT state FROM crawl_queue").fetchone()[0], "pending")

    def test_exclusive_lock(self):
        with self.assertRaisesRegex(RuntimeError, "Another crawler"):
            Store(self.path, article_id)

    def test_scheduler_retry_and_saved_alias(self):
        scheduler = SQLiteScheduler()
        scheduler.spider = TopkySpider()
        scheduler.store = self.store
        self.assertTrue(scheduler.enqueue_request(Request(URL)))
        self.assertFalse(scheduler.enqueue_request(Request(URL + "#anchor")))
        request = scheduler.next_request()
        request.meta["retry_times"] = 2
        scheduler.enqueue_request(request)
        self.store.recover()
        self.assertEqual(scheduler.next_request().meta["retry_times"], 2)
        with self.store.db:
            self.store.finish(1)
        self.save(response())
        self.assertFalse(scheduler.enqueue_request(Request("https://www.topky.sk/cl/10/100/Other-slug")))
        self.assertIsNotNone(self.store.saved_article("https://www.topky.sk/cl/10/100/Other-slug"))

    def test_scheduler_uses_shared_errback_for_cas(self):
        scheduler = SQLiteScheduler()
        scheduler.spider = CasSpider()
        scheduler.store = self.store
        url = "https://www.cas.sk/spravy/domace/novy-clanok"
        self.assertTrue(scheduler.enqueue_request(Request(url)))
        request = scheduler.next_request()
        self.assertEqual(request.errback.__self__, scheduler.spider)
        self.assertEqual(request.errback.__func__, CasSpider.failed)

    def test_offsite_redirect_is_terminal(self):
        scheduler = SQLiteScheduler()
        scheduler.spider = TopkySpider()
        scheduler.store = self.store
        scheduler.enqueue_request(Request(URL))
        request = scheduler.next_request()
        self.assertFalse(scheduler.enqueue_request(request.replace(url="https://example.com/")))
        self.assertEqual(self.store.db.execute("SELECT state FROM crawl_queue").fetchone()[0], "blocked")

    def test_queued_alias_is_skipped_after_article_saved(self):
        scheduler = SQLiteScheduler()
        scheduler.spider = TopkySpider()
        scheduler.store = self.store
        scheduler.enqueue_request(Request("https://www.topky.sk/cl/10/100/Other-slug"))
        self.save(response())
        self.assertIsNone(scheduler.next_request())
        self.assertFalse(scheduler.has_pending_requests())
        self.assertEqual(self.store.db.execute("SELECT state FROM crawl_queue").fetchone()[0], "completed")

    def test_refresh_and_retry_flags(self):
        with self.store.db:
            self.store.discover(URL, "article")
            self.store.discover("https://www.topky.sk/", "listing")
            self.store.discover("https://www.topky.sk/sitemap.xml", "sitemap")
            self.store.db.execute("UPDATE crawl_queue SET state='in_flight'")
            self.store.finish(1)
            self.store.finish(2)
            self.store.finish(3, "failed", "HTTP 503")
        self.store.recover(refresh=True, retry_failed=True)
        self.assertEqual([r[0] for r in self.store.db.execute("SELECT state FROM crawl_queue ORDER BY id")],
                         ["completed", "pending", "pending"])

    def test_runs_and_attempts_are_recorded(self):
        with self.store.db:
            self.store.discover(URL, "article")
            run_id = self.store.start_run("test", "{}")
        scheduler = SQLiteScheduler()
        scheduler.spider = TopkySpider()
        scheduler.store = self.store
        scheduler.run_id = run_id
        request = scheduler.next_request()
        with self.store.db:
            self.store.finish(request.meta["_queue_id"], response=response(), attempt_id=request.meta["_attempt_id"])
            self.store.end_run(run_id, "finished", "{}")
        self.assertEqual(self.store.db.execute("SELECT close_reason FROM crawl_runs").fetchone()[0], "finished")
        self.assertEqual(tuple(self.store.db.execute("SELECT outcome,http_status FROM crawl_attempts").fetchone()),
                         ("completed", 200))


if __name__ == "__main__":
    unittest.main()
