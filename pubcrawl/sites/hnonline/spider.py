from ...common.spider import ArchiveSpider
from .parser import parse_article, paywall_reason
from .urls import article_id, kind, normalize


class HNOnlineSpider(ArchiveSpider):
    name = "hnonline"
    allowed_domains = ["hnonline.sk", "www.hnonline.sk"]
    default_db = "data/hnonline-v2.sqlite3"
    start_urls = (
        "https://hnonline.sk/",
        "https://hnonline.sk/robots.txt",
        "https://hnonline.sk/sitemap-index-hnonline-sk.xml.gz",
    )
    normalize = staticmethod(normalize)
    kind = staticmethod(kind)
    article_id = staticmethod(article_id)
    parse_article = staticmethod(parse_article)

    def blacklist_reason(self, response):
        if response.meta.get("_kind") == "article":
            return paywall_reason(response)
        return None
    custom_settings = {
        "USER_AGENT": "HNOnlineArchiveBot/0.2",
        "ROBOTSTXT_USER_AGENT": "HNOnlineArchiveBot",
    }
