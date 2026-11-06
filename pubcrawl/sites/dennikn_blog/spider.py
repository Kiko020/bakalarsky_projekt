from urllib.parse import urlsplit

from ...common.spider import ArchiveSpider
from .parser import parse_article
from .urls import article_id, kind, normalize


class DennikNBlogSpider(ArchiveSpider):
    name = "dennikn_blog"
    allowed_domains = ["dennikn.sk", "www.dennikn.sk"]
    default_db = "data/dennikn-blog-v2.sqlite3"
    start_urls = (
        "https://dennikn.sk/blog/",
        "https://dennikn.sk/zoznam-blogerov/",
    )
    normalize = staticmethod(normalize)
    kind = staticmethod(kind)
    article_id = staticmethod(article_id)
    parse_article = staticmethod(parse_article)

    def links(self, response, page_kind):
        source_path = urlsplit(response.url).path
        is_directory = source_path.rstrip("/") == "/zoznam-blogerov"
        is_author = self.kind(response.url) == "author"
        for href in response.css("a::attr(href)").getall():
            normalized = self.normalize(href, response.url)
            entry_kind = self.kind(normalized) if normalized else None
            if entry_kind == "article":
                yield normalized, entry_kind
            elif entry_kind == "listing":
                # The only directory links accepted are its own pagination.
                if is_directory and "/zoznam-blogerov" in urlsplit(normalized).path:
                    yield normalized, entry_kind
                elif "/blog/" in urlsplit(normalized).path:
                    yield normalized, entry_kind
            elif entry_kind == "author" and is_directory:
                yield normalized, entry_kind
            elif entry_kind == "author" and is_author and urlsplit(normalized).path == source_path:
                # Allow pagination on the profile currently being visited, without
                # traversing to unrelated author profiles.
                yield normalized, entry_kind

    custom_settings = {
        "USER_AGENT": "DennikNBlogArchiveBot/0.2",
        "ROBOTSTXT_USER_AGENT": "DennikNBlogArchiveBot",
    }
