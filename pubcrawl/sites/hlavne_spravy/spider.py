from ...common.spider import ArchiveSpider
from .parser import parse_article
from .urls import article_id, kind, normalize


class HlavneSpravySpider(ArchiveSpider):
    name = "hlavne_spravy"
    allowed_domains = ["hlavnespravy.sk", "www.hlavnespravy.sk"]
    default_db = "data/hlavne-spravy-v2.sqlite3"
    start_urls = (
        "https://www.hlavnespravy.sk/",
        "https://www.hlavnespravy.sk/robots.txt",
        "https://www.hlavnespravy.sk/sitemap_index.xml",
    )
    normalize = staticmethod(normalize)
    kind = staticmethod(kind)
    article_id = staticmethod(article_id)
    parse_article = staticmethod(parse_article)
    custom_settings = {
        "USER_AGENT": "HlavneSpravyArchiveBot/0.2",
        "ROBOTSTXT_USER_AGENT": "HlavneSpravyArchiveBot",
    }
