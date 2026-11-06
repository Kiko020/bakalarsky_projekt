from ...common.spider import ArchiveSpider
from .parser import parse_article
from .urls import article_id, kind, normalize


class TerazSpider(ArchiveSpider):
    name = "teraz"
    allowed_domains = ["teraz.sk", "www.teraz.sk"]
    default_db = "data/teraz-v2.sqlite3"
    start_urls = (
        "https://www.teraz.sk/",
        "https://www.teraz.sk/najnovsie",
        "https://www.teraz.sk/robots.txt",
        "https://www.teraz.sk/rss/vsetky-spravy.rss",
    )
    normalize = staticmethod(normalize)
    kind = staticmethod(kind)
    article_id = staticmethod(article_id)
    parse_article = staticmethod(parse_article)
    custom_settings = {
        "USER_AGENT": "TerazArchiveBot/0.2",
        "ROBOTSTXT_USER_AGENT": "TerazArchiveBot",
    }

    def links(self, response, page_kind):
        if page_kind != "feed":
            yield from super().links(response, page_kind)
            return
        selector = "//*[local-name()='item']/*[local-name()='link']/text() | //*[local-name()='entry']/*[local-name()='link']/@href"
        for node in response.xpath(selector):
            url = self.normalize(node.get().strip(), response.url)
            if url and self.kind(url) == "article":
                yield url, "article"
