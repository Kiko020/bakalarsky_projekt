from ...common.spider import ArchiveSpider
from .parser import parse_article
from .urls import article_id, kind, normalize


class PravdaBlogSpider(ArchiveSpider):
    name = "pravda_blog"
    allowed_domains = ["blog.pravda.sk"]
    default_db = "data/pravda-blog-v2.sqlite3"
    start_urls = (
        "https://blog.pravda.sk/",
        "https://blog.pravda.sk/sitemap.xml",
    )
    normalize = staticmethod(normalize)
    kind = staticmethod(kind)
    article_id = staticmethod(article_id)
    parse_article = staticmethod(parse_article)
    custom_settings = {
        "USER_AGENT": "PravdaBlogArchiveBot/0.2",
        "ROBOTSTXT_USER_AGENT": "PravdaBlogArchiveBot",
    }
