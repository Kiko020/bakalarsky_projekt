import re
from urllib.parse import parse_qsl, urlsplit

from ...common.urls import normalize_url


ARTICLE = re.compile(r"/(\d+)-[^/]+/?$")
LISTING_ROOTS = {
    "aktuality", "bedeker-gurmana", "dobre-tipy", "doprava", "ekonomika",
    "historia", "komunalne-volby-2026", "kultura", "nasa-tema", "policia",
    "rozhovory", "samosprava", "sport", "vystavba", "zdravie-a-zivotny-styl",
    "zivot-v-meste",
}
EXCLUDED_ROOTS = {
    "o-nas", "inzercia", "vydania", "feed", "diskusia", "galeria", "foto",
    "video", "vyhladavanie", "search", "html",
}
EXCLUDED_QUERY_PARAMETERS = {"back_url", "comments", "diskusia", "gallery", "foto", "video", "search", "q"}


def normalize(url, base="https://www.bratislavskenoviny.sk/"):
    return normalize_url(url, base=base,
                         hosts={"bratislavskenoviny.sk", "www.bratislavskenoviny.sk"},
                         canonical_host="www.bratislavskenoviny.sk")


def article_id(url):
    match = ARTICLE.search(urlsplit(url).path)
    return match.group(1) if match else None


def kind(url):
    parts = urlsplit(url)
    path = parts.path.rstrip("/") or "/"
    segments = [segment.lower() for segment in path.split("/") if segment]
    query_keys = {key.lower() for key, _ in parse_qsl(parts.query)}
    if query_keys & EXCLUDED_QUERY_PARAMETERS:
        return None
    if path == "/robots.txt":
        return "robots"
    if path.endswith((".xml", ".xml.gz")) and "sitemap" in path.lower():
        return "sitemap"
    if segments and segments[0] in EXCLUDED_ROOTS:
        return None
    if article_id(url):
        return "article"
    if query_keys:
        return None
    if path == "/":
        return "listing"
    if segments and re.fullmatch(r"strana-[1-9]\d*", segments[-1]):
        segments = segments[:-1]
    if len(segments) == 1 and segments[0] in LISTING_ROOTS:
        return "listing"
    if len(segments) == 2 and segments[0] == "aktuality" and re.fullmatch(r"[a-z]+(?:-[a-z]+)*", segments[1]):
        return "listing"
    return None
