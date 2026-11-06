from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from ...common.urls import normalize_url


EXCLUDED_ROOTS = {
    "_next", "ajax", "api", "articlevideo", "autor", "cookies", "diskusia",
    "export", "files", "gal", "galeria", "icons", "iframevideo", "predplatne",
    "preview", "tag", "tip-redakcii",
}
EXCLUDED_QUERY_PARAMETERS = {"comments", "diskusia", "foto", "gallery", "video"}


def normalize(url, base="https://www1.pluska.sk/"):
    normalized = normalize_url(
        url,
        base=base,
        hosts={"pluska.sk", "www.pluska.sk", "www1.pluska.sk"},
        canonical_host="www1.pluska.sk",
    )
    if not normalized:
        return None
    parts = urlsplit(normalized)
    # Pluska decorates virtually every internal link with itm_* placement data.
    # It is analytics metadata, not part of the resource identity.
    query = [(key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True)
             if not key.lower().startswith("itm_")]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), ""))


def article_id(url):
    if kind(url) != "article":
        return None
    return urlsplit(url).path.rstrip("/")


def kind(url):
    parts = urlsplit(url)
    path = parts.path.rstrip("/") or "/"
    segments = [segment.lower() for segment in path.split("/") if segment]
    query_keys = {key.lower() for key, _ in parse_qsl(parts.query)}
    if query_keys & EXCLUDED_QUERY_PARAMETERS:
        return None
    if path == "/robots.txt":
        return "robots"
    if path.endswith((".xml", ".xml.gz")) and (
            "sitemap" in path.lower() or path == "/google_news.xml"):
        return "sitemap"
    if path == "/" or (segments and segments[0] == "r"):
        return "listing"
    if not segments or segments[0] in EXCLUDED_ROOTS:
        return None
    if segments[:2] == ["premium", "predplatne"]:
        return None
    # Current and historical articles use /rubric/slug, with premium stories
    # using /premium/rubric/slug. Rubric listings are explicitly under /r/.
    return "article" if len(segments) >= 2 else None
