"""Sport.aktuality.sk adapter over the shared metadata-first parser."""

from ...common.parser import clean, parse_article as _parse_article
from .urls import article_id, normalize


_BODY_BLOCKS = (
    "div[id^='single-news-content-'] > h5, "
    "div[id^='single-news-content-'] > h2, "
    "div[id^='single-news-content-'] > h3, "
    "div[id^='single-news-content-'] > p, "
    "div[id^='single-news-content-'] > blockquote, "
    "div[id^='single-news-content-'] > ul > li, "
    "div[id^='single-news-content-'] > ol > li"
)


def _intro(response):
    node = response.css("div[id^='single-news-content-'] > h5")
    return clean(node[0].xpath("string(.)").get()) if node else ""


def _body_text(response):
    blocks = [
        clean(node.xpath("string(.)").get())
        for node in response.css(_BODY_BLOCKS)
    ]
    body = "\n\n".join(filter(None, blocks))
    if not body:
        raise ValueError("Article requires a nonempty Sport.sk article body")
    return body


def parse_article(response):
    item = _parse_article(
        response,
        normalize_url=normalize,
        article_identifier=article_id,
        body_extractor=_body_text,
    )
    item["intro"] = _intro(response) or None
    heading = response.css("h1.single-news-title")
    if heading:
        item["title"] = clean(heading[0].xpath("string(.)").get()) or item["title"]
    sections = [clean(node.xpath("string(.)").get()) for node in response.css(".breadcrumbs a")]
    sections = list(dict.fromkeys(filter(None, sections)))
    if sections:
        item["section"] = ", ".join(sections)
    return item
