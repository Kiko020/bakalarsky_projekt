import re
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

from ...common.urls import TRACKING_PARAMETERS


ARTICLE = re.compile(r"^/blog/(\d+)/[^/]+/?$", re.I)
AUTHOR = re.compile(r"^/autor/[^/]+/?$", re.I)
BLOG_LISTING = re.compile(r"^/blog/(?:page/\d+)?/?$", re.I)
BLOG_DIRECTORY = re.compile(r"^/zoznam-blogerov(?:/page/\d+)?/?$", re.I)


def normalize(url, base="https://dennikn.sk/"):
    try:
        parts = urlsplit(urljoin(base, url))
        port = parts.port
    except (TypeError, ValueError):
        return None
    host = (parts.hostname or "").lower()
    if parts.scheme not in {"http", "https"} or host not in {"dennikn.sk", "www.dennikn.sk"}:
        return None
    if parts.username or parts.password or port not in (None, 80, 443):
        return None
    query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not key.lower().startswith("utm_") and key.lower() not in TRACKING_PARAMETERS
    ]
    return urlunsplit(("https", "dennikn.sk", parts.path or "/", urlencode(sorted(query)), ""))


def article_id(url):
    try:
        parts = urlsplit(url)
    except (TypeError, ValueError):
        return None
    match = ARTICLE.match(parts.path)
    return match.group(1) if parts.hostname and parts.hostname.lower() in {
        "dennikn.sk", "www.dennikn.sk"
    } and match else None


def kind(url):
    try:
        parts = urlsplit(url)
    except (TypeError, ValueError):
        return None
    if (parts.hostname or "").lower() not in {"dennikn.sk", "www.dennikn.sk"}:
        return None
    path = parts.path or "/"
    if ARTICLE.match(path):
        return "article"
    if BLOG_LISTING.match(path) or BLOG_DIRECTORY.match(path):
        return "listing"
    if AUTHOR.match(path):
        return "author"
    return None
