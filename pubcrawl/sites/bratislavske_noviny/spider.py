from ...common.spider import ArchiveSpider
from .parser import parse_article
from .urls import article_id, kind, normalize


class BratislavskeNovinySpider(ArchiveSpider):
    name = "bratislavske_noviny"
    allowed_domains = ["bratislavskenoviny.sk", "www.bratislavskenoviny.sk"]
    default_db = "data/bratislavske-noviny-v2.sqlite3"
    start_urls = (
        "https://www.bratislavskenoviny.sk/",
        "https://www.bratislavskenoviny.sk/robots.txt",
    )
    normalize = staticmethod(normalize)
    kind = staticmethod(kind)
    article_id = staticmethod(article_id)
    parse_article = staticmethod(parse_article)
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
    }
