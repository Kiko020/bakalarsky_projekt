"""Hlavné správy adapter over the shared metadata-first article parser."""

from ...common.parser import clean, parse_article as _parse_article, text_blocks
from .urls import article_id, normalize


_BODY_SELECTORS = (
    "[itemprop='articleBody']", ".td-post-content", ".entry-content",
    ".article-content", ".article-body", ".post-content", "article",
)
_INTRO_SELECTORS = (
    ".td-post-sub-title", ".entry-summary", ".article-intro", ".perex",
    "[itemprop='description']",
)


def _intro(response):
    for selector in _INTRO_SELECTORS:
        nodes = response.css(selector)
        if nodes:
            value = clean(nodes[0].xpath("string(.)").get())
            if value:
                return value
    return ""


def _body_text(response):
    for selector in _BODY_SELECTORS:
        nodes = response.css(selector)
        if nodes:
            body = text_blocks(nodes[0])
            if body:
                return body
    return ""


def parse_article(response):
    item = _parse_article(
        response,
        normalize_url=normalize,
        article_identifier=article_id,
        body_extractor=_body_text,
    )
    item["intro"] = _intro(response) or item["intro"]
    return item
