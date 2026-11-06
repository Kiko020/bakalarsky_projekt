"""SITA.sk adapter over the shared metadata-first article parser."""

from ...common.parser import clean, parse_article as _parse_article
from .urls import article_id, normalize


_BODY_SELECTORS = (
    "[itemprop='articleBody']", ".entry-content", ".article-content",
    ".article-body", ".post-content", ".article__body",
)


def _intro(response):
    for selector in (".article-perex", ".entry-summary", ".post-excerpt", ".perex",
                     "[itemprop='description']"):
        nodes = response.css(selector)
        if nodes:
            return clean(nodes[0].xpath("string(.)").get())
    return ""


def _body_text(response):
    from ...common.parser import text_blocks

    for selector in _BODY_SELECTORS:
        nodes = response.css(selector)
        if nodes:
            body = text_blocks(nodes[0])
            if body:
                return body
    raise ValueError("Article requires a nonempty SITA article body")


def parse_article(response):
    item = _parse_article(
        response,
        normalize_url=normalize,
        article_identifier=article_id,
        body_extractor=_body_text,
    )
    item["intro"] = _intro(response) or item["intro"]
    return item
