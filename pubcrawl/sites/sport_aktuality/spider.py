from ...common.spider import ArchiveSpider
from .parser import parse_article
from .urls import article_id, kind, normalize


class SportAktualitySpider(ArchiveSpider):
    name = "sport_aktuality"
    allowed_domains = ["sport.aktuality.sk"]
    default_db = "data/sport-aktuality-v2.sqlite3"
    start_urls = (
        "https://sport.aktuality.sk/",
        "https://sport.aktuality.sk/najnovsie-spravy",
        "https://sport.aktuality.sk/robots.txt",
    )
    normalize = staticmethod(normalize)
    kind = staticmethod(kind)
    article_id = staticmethod(article_id)
    parse_article = staticmethod(parse_article)
    custom_settings = {
        "USER_AGENT": "SportAktualityArchiveBot/0.2",
        "ROBOTSTXT_USER_AGENT": "SportAktualityArchiveBot",
    }
