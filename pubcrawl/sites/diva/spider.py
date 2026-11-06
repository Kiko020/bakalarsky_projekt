from ...common.spider import ArchiveSpider
from .parser import parse_article
from .urls import article_id, kind, normalize


class DivaSpider(ArchiveSpider):
    name = "diva"
    allowed_domains = ["diva.aktuality.sk"]
    default_db = "data/diva-v2.sqlite3"
    start_urls = (
        "https://diva.aktuality.sk/",
        "https://diva.aktuality.sk/robots.txt",
    )
    normalize = staticmethod(normalize)
    kind = staticmethod(kind)
    article_id = staticmethod(article_id)
    parse_article = staticmethod(parse_article)
    custom_settings = {
        "USER_AGENT": "DivaArchiveBot/0.2",
        "ROBOTSTXT_USER_AGENT": "DivaArchiveBot",
    }
