"""Cas.sk adapter over the shared metadata-first article parser."""
import json
from urllib.parse import urlsplit

from ...common.parser import clean, parse_article as _parse_article
from .urls import article_id, normalize


_BODY_BLOCKS = (
    "#bodyBlockAdvertisementGeneratorComponentId [id^='paragraphBlock-'], "
    "#bodyBlockAdvertisementGeneratorComponentId [id^='headingBlock-']"
)
_GALLERY_ROOTS = {"gal", "galeria", "galerie", "foto"}


def _is_gallery_prompt(node, response):
    """Only discard blocks whose nonempty text belongs entirely to gallery links."""
    text_count = sum(bool(clean(text)) for text in node.xpath(".//text()").getall())
    gallery_text_count = 0
    for link in node.css("a[href]"):
        url = normalize(link.attrib["href"], response.url)
        if url and urlsplit(url).path.split("/")[1].lower() in _GALLERY_ROOTS:
            gallery_text_count += sum(
                bool(clean(text)) for text in link.xpath(".//text()").getall())
    return text_count > 0 and text_count == gallery_text_count


def _body_text(response):
    blocks = []
    nodes = response.css(_BODY_BLOCKS)
    for node in nodes:
        text = clean(node.xpath("string(.)").get())
        if text and not _is_gallery_prompt(node, response):
            blocks.append(text)
    if nodes and not blocks:
        raise ValueError("Article requires a nonempty body after removing gallery prompts")
    return "\n\n".join(blocks)


def _node_text(node):
    return clean(node.xpath("string(.)").get()) if node else ""


def _next_article(response):
    """Return Cas's article payload when JSON-LD/HTML omit a field."""
    raw = response.css("script#__NEXT_DATA__::text").get()
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        article = data["props"]["pageProps"]["initialState"]["api"]["article"]["receivedData"]
        return article if isinstance(article, dict) else {}
    except (KeyError, TypeError, ValueError):
        return {}


def _cas_metadata(response, item):
    payload = _next_article(response)
    field = payload.get("field") if isinstance(payload.get("field"), dict) else {}

    # Cas currently truncates JSON-LD headlines to its subtitle. The visible H1,
    # Open Graph value, and Next payload contain the actual article title.
    headings = response.css("h1[data-don='article_title'], h1")
    title = _node_text(headings[0]) if headings else ""
    title = title or clean(response.css('meta[property="og:title"]::attr(content)').get())
    title = title or clean(field.get("title"))
    if title:
        item["title"] = title

    authors = json.loads(item["authors_json"])
    if not authors:
        authors = [_node_text(node) for node in response.css(".author-header-name")]
        if not any(authors):
            payload_authors = payload.get("authors")
            payload_authors = payload_authors if isinstance(payload_authors, list) else []
            authors = [clean(author.get("name")) for author in payload_authors
                       if isinstance(author, dict)]
        item["authors_json"] = json.dumps(
            list(dict.fromkeys(filter(None, authors))), ensure_ascii=False)

    tags = [_node_text(node) for node in response.css("#relatedTagsId a")]
    if tags:
        item["tags_json"] = json.dumps(
            list(dict.fromkeys(filter(None, tags))), ensure_ascii=False)

    if not item["source"]:
        item["source"] = clean(field.get("source")) or None
    return item


def parse_article(response):
    item = _parse_article(response, normalize_url=normalize, article_identifier=article_id,
                          body_extractor=_body_text)
    return _cas_metadata(response, item)
