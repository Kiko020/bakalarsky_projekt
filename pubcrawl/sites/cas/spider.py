from ...common.spider import ArchiveSpider
from .parser import parse_article
from .urls import article_id, kind, normalize


class CasSpider(ArchiveSpider):
    name = "cas"
    allowed_domains = ["cas.sk", "www.cas.sk"]
    default_db = "data/cas-v2.sqlite3"
    start_urls = ("https://www.cas.sk/", "https://www.cas.sk/robots.txt", "https://www.cas.sk/sitemap.xml")
    normalize = staticmethod(normalize)
    kind = staticmethod(kind)
    article_id = staticmethod(article_id)
    parse_article = staticmethod(parse_article)
    custom_settings = {
        "USER_AGENT": "CasArchiveBot/0.2",
        "ROBOTSTXT_USER_AGENT": "CasArchiveBot",
    }
