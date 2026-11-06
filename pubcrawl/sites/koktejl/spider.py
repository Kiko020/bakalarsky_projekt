from ...common.spider import ArchiveSpider
from .parser import parse_article
from .urls import article_id, kind, normalize


class KoktejlSpider(ArchiveSpider):
    name = "koktejl"
    allowed_domains = ["koktejl.azet.sk"]
    default_db = "data/koktejl-v2.sqlite3"
    start_urls = (
        "https://koktejl.azet.sk/",
        "https://koktejl.azet.sk/robots.txt",
    )
    normalize = staticmethod(normalize)
    kind = staticmethod(kind)
    article_id = staticmethod(article_id)
    parse_article = staticmethod(parse_article)
    custom_settings = {
        "USER_AGENT": "KoktejlArchiveBot/0.2",
        "ROBOTSTXT_USER_AGENT": "KoktejlArchiveBot",
    }
