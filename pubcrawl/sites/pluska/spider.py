from ...common.spider import ArchiveSpider
from .parser import parse_article
from .urls import article_id, kind, normalize


class PluskaSpider(ArchiveSpider):
    name = "pluska"
    allowed_domains = ["pluska.sk", "www.pluska.sk", "www1.pluska.sk"]
    default_db = "data/pluska-v2.sqlite3"
    start_urls = (
        "https://www1.pluska.sk/",
        "https://www1.pluska.sk/robots.txt",
        "https://www1.pluska.sk/sitemaps/plus1-sitemap.xml",
    )
    normalize = staticmethod(normalize)
    kind = staticmethod(kind)
    article_id = staticmethod(article_id)
    parse_article = staticmethod(parse_article)
    custom_settings = {
        "USER_AGENT": "PluskaArchiveBot/0.2",
        "ROBOTSTXT_USER_AGENT": "PluskaArchiveBot",
    }
