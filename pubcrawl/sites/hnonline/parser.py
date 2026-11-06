"""HNOnline.sk adapter over the shared metadata-first article parser."""

from ...common.parser import clean, normalized_text, parse_article as _parse_article
from .urls import article_id, normalize


_BODY_BLOCKS = (
    ".itemFullText > p, "
    ".itemFullText > h2, "
    ".itemFullText > h3, "
    ".itemFullText > blockquote, "
    ".itemFullText > ul > li, "
    ".itemFullText > ol > li"
)
_PAYWALL_MARKERS = (
    "Tento článok je určený pre predplatiteľov",
    "Dostupné pre predplatiteľov",
    "Zostáva vám",
)


def paywall_reason(response):
    """Detect HN Online's subscriber-only article notice in rendered HTML."""
    text = normalized_text(response.text).casefold()
    if any(normalized_text(marker).casefold() in text for marker in _PAYWALL_MARKERS):
        return "HN Online subscriber-only paywall"
    return None


def _intro(response):
    node = response.css(".item__subtitle")
    return clean(node[0].xpath("string(.)").get()) if node else ""


def _body_text(response):
    intro = _intro(response)
    normalized_intro = normalized_text(intro)
    blocks = []
    for node in response.css(_BODY_BLOCKS):
        text = clean(node.xpath("string(.)").get())
        if text and normalized_text(text) != normalized_intro:
            blocks.append(text)
    if intro:
        blocks.insert(0, intro)
    if not blocks:
        raise ValueError("Article requires a nonempty HN Online article body")
    return "\n\n".join(blocks)


def parse_article(response):
    item = _parse_article(
        response,
        normalize_url=normalize,
        article_identifier=article_id,
        body_extractor=_body_text,
    )
    item["intro"] = _intro(response) or None
    return item
