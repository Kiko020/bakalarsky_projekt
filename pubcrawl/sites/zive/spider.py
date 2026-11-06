from ...common.spider import ArchiveSpider
from .parser import parse_article
from .urls import article_id, kind, normalize


class ZiveSpider(ArchiveSpider):
    name = "zive"
    allowed_domains = ["zive.aktuality.sk"]
    default_db = "data/zive-v2.sqlite3"
    start_urls = (
        "https://zive.aktuality.sk/",
        "https://zive.aktuality.sk/robots.txt",
    )
    normalize = staticmethod(normalize)
    kind = staticmethod(kind)
    article_id = staticmethod(article_id)
    parse_article = staticmethod(parse_article)
    custom_settings = {
        "USER_AGENT": "ZiveArchiveBot/0.2",
        "ROBOTSTXT_USER_AGENT": "ZiveArchiveBot",
    }
