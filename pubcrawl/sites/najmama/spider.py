from ...common.spider import ArchiveSpider
from .parser import parse_article
from .urls import article_id, kind, normalize


class NajmamaSpider(ArchiveSpider):
    name = "najmama"
    allowed_domains = ["najmama.aktuality.sk"]
    default_db = "data/najmama-v2.sqlite3"
    start_urls = (
        "https://najmama.aktuality.sk/",
        "https://najmama.aktuality.sk/robots.txt",
    )
    normalize = staticmethod(normalize)
    kind = staticmethod(kind)
    article_id = staticmethod(article_id)
    parse_article = staticmethod(parse_article)
    custom_settings = {
        "USER_AGENT": "NajmamaArchiveBot/0.2",
        "ROBOTSTXT_USER_AGENT": "NajmamaArchiveBot",
    }
