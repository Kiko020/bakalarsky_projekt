import json
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from parsel import Selector

from ...common.parser import clean, parse_article as _parse_article
from .urls import article_id, normalize


SLOVAK_MONTHS = {
    "januára": 1,
    "februára": 2,
    "marca": 3,
    "apríla": 4,
    "mája": 5,
    "júna": 6,
    "júla": 7,
    "augusta": 8,
    "septembra": 9,
    "októbra": 10,
    "novembra": 11,
    "decembra": 12,
}
SLOVAK_DATE = re.compile(
    r"^(\d{1,2})\.\s+([^\s]+)\s+(\d{4})(?:\s+(\d{1,2}):(\d{2}))?$",
    re.I,
)


def _body_text(response):
    body = response.css('[itemprop="articleBody"]')
    if not body:
        return ""
    root = Selector(text=body[0].get()).root
    for child in list(root.xpath(".//script|.//style|.//nav|.//aside|.//footer|.//header|.//form")):
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
    selected = set(blocks)
    return "\n\n".join(filter(None, (
        clean("".join(node.itertext()))
        for node in blocks
        if not any(parent in selected for parent in node.iterancestors())
    )))


def _published_at(value):
    match = SLOVAK_DATE.match(clean(value))
    if not match:
        return None
    day, month_name, year, hour, minute = match.groups()
    month = SLOVAK_MONTHS.get(month_name.lower())
    if month is None:
        return None
    try:
        result = datetime(
            int(year), month, int(day), int(hour or 0), int(minute or 0),
            tzinfo=ZoneInfo("Europe/Bratislava"),
        )
    except ValueError:
        return None
    return result.isoformat()


def _texts(nodes):
    return list(dict.fromkeys(filter(None, (clean(node.xpath("string(.)").get()) for node in nodes))))


def parse_article(response):
    item = _parse_article(
        response,
        normalize_url=normalize,
        article_identifier=article_id,
        body_extractor=_body_text,
    )
    title_node = response.css('.post-title [itemprop~="headline"], '
                              '.post-title h1, .post-title h2')
    title = clean(title_node[0].xpath("string(.)").get()) if title_node else ""
    if not title:
        raise ValueError("Blog article requires a nonempty post title")
    item["title"] = title

    published = _published_at(response.css('[itemprop="datePublished"]::text').get())
    if published:
        item["published_at"] = published

    authors = _texts(response.css('[itemprop="author"] [itemprop="name"]'))
    if authors:
        item["authors_json"] = json.dumps(authors, ensure_ascii=False)

    categories = _texts(response.css('.post-date [itemprop="keywords"] a'))
    if categories:
        item["section"] = categories[-1]

    tags = _texts(response.css(".tagsSingle a"))
    item["tags_json"] = json.dumps(tags, ensure_ascii=False)
    return item
