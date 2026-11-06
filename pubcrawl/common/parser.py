import json
import re
import unicodedata
from datetime import datetime
from zoneinfo import ZoneInfo

from parsel import Selector


def clean(value):
    return " ".join(str(value or "").split())


def normalized_text(value):
    return clean(unicodedata.normalize("NFC", value))


def walk_json(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_json(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_json(child)


def names(value):
    if not isinstance(value, list):
        value = [value] if value else []
    return list(dict.fromkeys(clean(v.get("name")) if isinstance(v, dict) else clean(v) for v in value if v))


def timestamp(value):
    value = clean(value)
    if not value:
        return None
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        result = None
        for fmt in ("%d.%m.%Y %H:%M", "%d. %m. %Y %H:%M", "%d.%m.%Y", "%d. %m. %Y"):
            try:
                result = datetime.strptime(value, fmt)
                break
            except ValueError:
                pass
        if result is None:
            return None
    if result.tzinfo is None:
        result = result.replace(tzinfo=ZoneInfo("Europe/Bratislava"))
    return result.isoformat()


def text_blocks(node):
    # Work on a copy so link discovery still sees the complete original page.
    root = Selector(text=node.get()).root
    for child in list(root.xpath(".//script|.//style|.//nav|.//aside|.//footer|.//header|.//h1|.//form")):
        parent = child.getparent()
        if parent is not None:
            parent.remove(child)
    for child in list(root.xpath(".//*[@class or @id]")):
        marker = (child.get("class", "") + " " + child.get("id", "")).lower()
        if re.search(r"related|recommend|advert|(^|[ _-])ads?([ _-]|$)|social|share|gallery|diskusi|newsletter", marker):
            parent = child.getparent()
            if parent is not None:
                parent.remove(child)
    blocks = root.xpath(".//p|.//h2|.//h3|.//li|.//blockquote[not(.//p)]")
    if not blocks:
        return clean(" ".join(root.itertext()))
    # Avoid counting nested paragraph/list/quote text more than once.
    selected = set(blocks)
    return "\n\n".join(filter(None, (clean(" ".join(el.itertext())) for el in blocks
                                     if not any(parent in selected for parent in el.iterancestors()))))


def parse_article(response, *, normalize_url, article_identifier, body_extractor=None):
    meta = {}
    for node in response.css("meta"):
        key = node.attrib.get("property") or node.attrib.get("name")
        if key and node.attrib.get("content"):
            meta.setdefault(key.lower(), node.attrib["content"])
    structured = []
    for raw in response.css('script[type="application/ld+json"]::text').getall():
        try:
            structured.extend(walk_json(json.loads(raw)))
        except (ValueError, TypeError):
            continue
    article = next((node for node in structured if any(isinstance(t, str) and t in {"NewsArticle", "Article", "ReportageNewsArticle"}
                    for t in (node.get("@type") if isinstance(node.get("@type"), list) else [node.get("@type")]))), {})
    title = (clean(article.get("headline"))
             or clean(" ".join(response.css("h1 ::text").getall()))
             or clean(meta.get("og:title")))
    intro_nodes = response.css(".perex, .article-perex, .article__perex, .detail_perex, [itemprop='description']")
    intro = clean(" ".join(intro_nodes[0].css("::text, *::text").getall())) if intro_nodes else ""
    body = body_extractor(response) if body_extractor else ""
    body = body or ""
    if not body:
        for selector in ("[itemprop='articleBody']", ".article-body", ".article__body", ".article-content",
                         ".article__content", "#article-body", "#article_body", ".article-text", ".articleText",
                         "article .text", ".article .text", "article"):
            node = response.css(selector)
            if node:
                body = text_blocks(node[0])
                if body:
                    break
    if not body:
        body = str(article.get("articleBody") or "").strip()
    if intro and not normalized_text(body).startswith(normalized_text(intro)):
        body = intro + "\n\n" + body if body else ""
    if not title or not body:
        raise ValueError("Article requires a nonempty title and body; selectors may need updating")
    canonical_raw = response.css('link[rel="canonical"]::attr(href)').get()
    canonical = normalize_url(canonical_raw, response.url) if canonical_raw else None
    if canonical and article_identifier(canonical) != article_identifier(response.url):
        canonical = None
    author = names(article.get("author") or meta.get("author") or response.css('[rel="author"]::text').getall())
    keywords = article.get("keywords") or meta.get("news_keywords") or meta.get("keywords") or []
    tags = [clean(v) for v in keywords.split(",")] if isinstance(keywords, str) else names(keywords)
    images = article.get("image") or meta.get("og:image") or []
    if not isinstance(images, list):
        images = [images]
    image_urls = [response.urljoin(v.get("url") or v.get("contentUrl")) if isinstance(v, dict)
                  else response.urljoin(v) for v in images if v and (not isinstance(v, dict) or v.get("url") or v.get("contentUrl"))]
    published = article.get("datePublished") or meta.get("article:published_time") or response.css("time::attr(datetime)").get()
    modified = article.get("dateModified") or meta.get("article:modified_time")
    section = article.get("articleSection") or meta.get("article:section")
    if isinstance(section, list):
        section = ", ".join(map(str, section))
    source = article.get("sourceOrganization") or meta.get("source")
    if isinstance(source, dict):
        source = source.get("name")
    return dict(title=title, intro=intro or None, body_text=body, normalized_text=normalized_text(body),
                canonical_url=canonical, authors_json=json.dumps(author, ensure_ascii=False), source=clean(source) or None,
                published_at=timestamp(published), modified_at=timestamp(modified), section=section,
                tags_json=json.dumps(list(dict.fromkeys(filter(None, tags))), ensure_ascii=False),
                language=article.get("inLanguage") or response.css("html::attr(lang)").get() or meta.get("og:locale"),
                images_json=json.dumps(image_urls, ensure_ascii=False),
                metadata_json=json.dumps({"meta": meta, "article_jsonld": article}, ensure_ascii=False))
