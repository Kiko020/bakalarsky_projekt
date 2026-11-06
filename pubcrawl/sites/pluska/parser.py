"""Pluska.sk adapter over the shared metadata-first article parser."""
import json
from urllib.parse import urlsplit

from ...common.parser import clean, parse_article as _parse_article
from .urls import article_id, normalize


def _body_text(response):
    root = response.css("#bodyBlockAdvertisementGeneratorComponentId")
    if not root:
        raise ValueError("Article requires a Pluska.sk article body")
    blocks = []
    for node in root[0].xpath("./*"):
        marker = node.attrib.get("id", "")
        classes = node.attrib.get("class", "")
        if not (marker.startswith("paragraphBlock-") or "HeadingBlock_wrapper__" in classes):
            continue
        # The newsletter call-to-action is represented as an ordinary paragraph
        # block but is not article text.
        external_hosts = {
            urlsplit(href).hostname
            for href in node.css("a::attr(href)").getall()
            if urlsplit(href).hostname
        }
        if "redakcienmh.ecomailapp.cz" in external_hosts:
            continue
        text = clean(node.xpath("string(.)").get())
        if text:
            blocks.append(text)
    if not blocks:
        raise ValueError("Article requires a nonempty Pluska.sk article body")
    return "\n\n".join(blocks)


def parse_article(response):
    item = _parse_article(
        response,
        normalize_url=normalize,
        article_identifier=article_id,
        body_extractor=_body_text,
    )
    # Pluska's JSON-LD headline can contain the shorter print subtitle. The H1
    # and Open Graph title represent the public web headline.
    heading = response.css("h1[data-don='article_title'], h1")
    if heading:
        item["title"] = clean(heading[0].xpath("string(.)").get()) or item["title"]
    tags = [clean(node.xpath("string(.)").get()) for node in response.css("#relatedTagsId a")]
    if any(tags):
        item["tags_json"] = json.dumps(
            list(dict.fromkeys(filter(None, tags))), ensure_ascii=False)
    return item
