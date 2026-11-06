"""Bratislavské noviny's c-rte article layout and visible date metadata."""

import json
from datetime import timedelta
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo

from parsel import Selector

from ...common.parser import clean, normalized_text, parse_article as _parse_article, text_blocks, timestamp
from .urls import article_id, normalize


def _article_node(response):
    nodes = response.css(".c-rte").xpath("self::*[h1]")
    if not nodes:
        raise ValueError("Missing Bratislavské noviny article container")
    return nodes[0]


def _body_text(response):
    root = Selector(text=_article_node(response).get())
    for node in root.css(".info, .img, .src, .socials, .c-article, .c-article-wrapper, .text-center, figure"):
        node.drop()
    return text_blocks(root)


def _published_at(response, node):
    date = node.css(".info .date")
    if not date:
        return None
    value = clean(date[0].xpath("string(.)").get())
    for label, days in (("Dnes", 0), ("Včera", 1)):
        if value.startswith(label):
            header = response.headers.get("Date")
            if not header:
                return None
            try:
                reference = parsedate_to_datetime(header.decode("ascii"))
                if reference.tzinfo is None:
                    return None
                day = reference.astimezone(ZoneInfo("Europe/Bratislava")).date() - timedelta(days=days)
            except (ValueError, TypeError, UnicodeError, OverflowError):
                return None
            clock = date[0].css("time::attr(datetime)").get()
            return timestamp(f"{day.isoformat()}T{clock}") if clock else None
    return timestamp(value)


def parse_article(response):
    node = _article_node(response)
    body = _body_text(response)
    if not body:
        raise ValueError("Article requires a nonempty body")
    item = _parse_article(response, normalize_url=normalize,
                          article_identifier=article_id, body_extractor=lambda _: body)
    # Listing cards elsewhere on the page also contain .perex elements.
    item["body_text"] = body
    item["normalized_text"] = normalized_text(body)
    intro = node.css(".lead, .e-perex")
    item["intro"] = clean(intro[0].xpath("string(.)").get()) if intro else None
    item["section"] = item["section"] or clean(node.css(".info .category").xpath("string(.)").get()) or None
    item["published_at"] = item["published_at"] or _published_at(response, node)
    metadata = json.loads(item["metadata_json"])
    metadata["visible_date"] = clean(node.css(".info .date").xpath("string(.)").get()) or None
    item["metadata_json"] = json.dumps(metadata, ensure_ascii=False)
    return item
