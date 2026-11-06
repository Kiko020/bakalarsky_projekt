from ...common.parser import clean, parse_article as _parse_article
from .urls import article_id, normalize


def _body_text(response):
    for selector in (
        '[itemprop="articleBody"]',
        ".article-body",
        ".article__body",
        ".post-content",
        "article",
    ):
        nodes = response.css(selector)
        if not nodes:
            continue
        blocks = []
        for node in nodes[0].css("p, h2, h3, li, blockquote"):
            text = clean(node.xpath("string(.)").get())
            if text:
                blocks.append(text)
        if blocks:
            return "\n\n".join(blocks)
    return ""


def parse_article(response):
    return _parse_article(
        response,
        normalize_url=normalize,
        article_identifier=article_id,
        body_extractor=_body_text,
    )
