"""Diva.sk adapter over the shared metadata-first article parser."""

from ...common.parser import clean, parse_article as _parse_article, text_blocks
from .urls import article_id, normalize


def _intro(response):
    for selector in (".article-perex", ".article__perex", ".perex", "[itemprop='description']"):
        node = response.css(selector)
        if node:
            return clean(node[0].xpath("string(.)").get())
    heading = response.css("h1")
    candidate = heading[0].xpath("following::p[1]") if heading else []
    return clean(candidate[0].xpath("string(.)").get()) if candidate else ""


def _body_text(response):
    for selector in ("[itemprop='articleBody']", ".article-content", ".article__content", "article"):
        nodes = response.css(selector)
        if nodes:
            body = text_blocks(nodes[0])
            if body:
                return body
    raise ValueError("Article requires a nonempty Diva.sk article body")


def parse_article(response):
    intro = _intro(response)
    item = _parse_article(
        response,
        normalize_url=normalize,
        article_identifier=article_id,
        body_extractor=_body_text,
    )
    item["intro"] = intro or item["intro"]
    return item
