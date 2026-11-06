import re
from urllib.parse import parse_qsl, urlsplit

from ...common.urls import normalize_url


ARTICLE = re.compile(r"/(\d+)-[^/]+/?$", re.I)
EXCLUDED_ROOTS = {
    "administrator", "article-preview", "autor", "bin", "cache", "cdn-cgi",
    "cli", "component", "components", "hn24", "includes", "installation", "language",
    "layouts", "libraries", "logs", "modules", "newsletter", "plugins",
    "predplatne", "search", "tag", "tmp", "users", "vyhladavanie",
}
LISTING_ROOTS = {
    "auto", "carovne-slovensko", "dennik", "dia", "finweb", "focus", "history",
    "hn-nativ", "hn-special", "hn-wiki", "hnporadna", "komentare",
    "magazin", "news", "notsorry", "prakticke-hn", "pr-clanky", "preco-nie",
    "science", "slovensko", "solventne-firmy", "sport", "style", "svet", "tema",
    "tv", "volby-2026", "zdn",
}
EXCLUDED_QUERY_PARAMETERS = {"diskusia", "gallery", "foto", "video"}


def normalize(url, base="https://hnonline.sk/"):
    return normalize_url(
        url,
        base=base,
        hosts={"hnonline.sk", "www.hnonline.sk"},
        canonical_host="hnonline.sk",
    )


def article_id(url):
    match = ARTICLE.search(urlsplit(url).path)
    return match.group(1) if match else None


def kind(url):
    parts = urlsplit(url)
    path = parts.path.rstrip("/") or "/"
    segments = [segment.lower() for segment in path.split("/") if segment]
    if segments and segments[0] in EXCLUDED_ROOTS:
        return None
    # HN's TV section contains video pages with article-like numeric slugs.
    # Keep the section listing crawlable, but do not archive its individual
    # video pages as articles.
    if len(segments) > 1 and segments[0] == "tv" and article_id(url):
        return None
    if any(key.lower() in EXCLUDED_QUERY_PARAMETERS for key, _ in parse_qsl(parts.query)):
        return None
    if article_id(url):
        return "article"
    if path == "/robots.txt":
        return "robots"
    if path.endswith((".xml", ".xml.gz")) and "sitemap" in path.lower():
        return "sitemap"
    if path == "/":
        return "listing"
    return "listing" if segments and segments[0] in LISTING_ROOTS else None
