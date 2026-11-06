"""Pravda.sk adapter over the shared metadata-first article parser."""
import json

from ...common.parser import clean, parse_article as _parse_article
from .urls import article_id, normalize


_BODY_BLOCKS = (
    ".detail_text_items > p, "
    ".detail_text_items > h2, "
    ".detail_text_items > h3, "
    ".detail_text_items > blockquote, "
    ".detail_text_items > ul > li, "
    ".detail_text_items > ol > li"
)


def _body_text(response):
    blocks = []
    for node in response.css(_BODY_BLOCKS):
        text = clean(node.xpath("string(.)").get())
        if text:
            blocks.append(text)
    return "\n\n".join(blocks)


def _node_text(node):
    return clean(node.xpath("string(.)").get()) if node else ""


def _pravda_metadata(response, item):
    authors = json.loads(item["authors_json"])
    if not authors:
        authors = [_node_text(node) for node in response.css(".detail_author_item")]
        item["authors_json"] = json.dumps(
            list(dict.fromkeys(filter(None, authors))), ensure_ascii=False)

    tags = [_node_text(node) for node in response.css(".detail_hashtags a")]
    if tags:
        item["tags_json"] = json.dumps(
            list(dict.fromkeys(filter(None, tags))), ensure_ascii=False)

    sections = [_node_text(node) for node in response.css(".detail_sections a")]
    if any(sections):
        item["section"] = next(filter(None, reversed(sections)))
    return item


def parse_article(response):
    item = _parse_article(
        response,
        normalize_url=normalize,
        article_identifier=article_id,
        body_extractor=_body_text,
    )
    return _pravda_metadata(response, item)
