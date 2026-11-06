from ...common.spider import ArchiveSpider
from .parser import parse_article
from .urls import article_id, kind, normalize


class SitaSpider(ArchiveSpider):
    name = "sita"
    allowed_domains = ["sita.sk", "www.sita.sk"]
    default_db = "data/sita-v2.sqlite3"
    start_urls = (
        "https://sita.sk/",
        "https://sita.sk/robots.txt",
        "https://sita.sk/feed/",
    )
    normalize = staticmethod(normalize)
    kind = staticmethod(kind)
    article_id = staticmethod(article_id)
    parse_article = staticmethod(parse_article)
    custom_settings = {
        "USER_AGENT": "SitaArchiveBot/0.2",
        "ROBOTSTXT_USER_AGENT": "SitaArchiveBot",
    }

    def links(self, response, page_kind):
        if page_kind != "feed":
            yield from super().links(response, page_kind)
            return
        for element in response.xpath("//*[local-name()='item']/*[local-name()='link']/text() | //*[local-name()='entry']/*[local-name()='link']/@href"):
            url = self.normalize(element.get().strip(), response.url)
            if url and self.kind(url) == "article":
                yield url, "article"
