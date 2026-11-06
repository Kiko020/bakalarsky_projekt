from ...common.spider import ArchiveSpider
from .parser import parse_article
from .urls import article_id, kind, normalize


class TopkySpider(ArchiveSpider):
    name = "topky"
    allowed_domains = ["topky.sk", "www.topky.sk"]
    default_db = "data/topky-v2.sqlite3"
    start_urls = (
        "https://www.topky.sk/",
        "https://www.topky.sk/robots.txt",
        "https://www.topky.sk/sitemap.xml",
    )
    normalize = staticmethod(normalize)
    kind = staticmethod(kind)
    article_id = staticmethod(article_id)
    parse_article = staticmethod(parse_article)
