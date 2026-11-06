import re
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

from ...common.urls import TRACKING_PARAMETERS


ARTICLE = re.compile(r"^/(\d{4})/(\d{1,2})/(\d{1,2})/[^/]+/?$", re.I)
PAGE = re.compile(r"^/page/\d+/?$", re.I)
DIRECTORY = re.compile(r"^/abecedny-zoznam-blogov(?:/page/\d+)?/?$", re.I)
SITEMAP = re.compile(r"^/sitemap(?:/[^/]+\.xml|\.xml)/?$", re.I)
EXCLUDED_ROOTS = {
    "author", "category", "comments", "feed", "search", "tag", "wp-admin",
    "wp-content", "wp-includes", "wp-json", "wp-login.php", "wp-pravda-login.php",
    "wp-signup.php", "xmlrpc.php",
}


def _is_blog_host(host):
    return host == "blog.pravda.sk" or (
        host.endswith(".blog.pravda.sk")
        and host.count(".") == 3
        and bool(host.removesuffix(".blog.pravda.sk"))
    )


def normalize(url, base="https://blog.pravda.sk/"):
    try:
        parts = urlsplit(urljoin(base, url))
        port = parts.port
    except (TypeError, ValueError):
        return None
    host = (parts.hostname or "").lower()
    if parts.scheme not in {"http", "https"} or not _is_blog_host(host):
        return None
    if parts.username or parts.password or port not in (None, 80, 443):
        return None
    query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not key.lower().startswith("utm_") and key.lower() not in TRACKING_PARAMETERS
    ]
    return urlunsplit(("https", host, parts.path or "/", urlencode(sorted(query)), ""))


def article_id(url):
    try:
        parts = urlsplit(url)
    except (TypeError, ValueError):
        return None
    if not _is_blog_host((parts.hostname or "").lower()) or not ARTICLE.match(parts.path):
        return None
    return f"{parts.hostname.lower()}{parts.path.rstrip('/')}"


def kind(url):
    try:
        parts = urlsplit(url)
    except (TypeError, ValueError):
        return None
    host = (parts.hostname or "").lower()
    if not _is_blog_host(host):
        return None
    path = parts.path or "/"
    segments = [segment.lower() for segment in path.split("/") if segment]
    if segments and segments[0] in EXCLUDED_ROOTS:
        return None
    if host == "blog.pravda.sk":
        if path == "/robots.txt":
            return "robots"
        if SITEMAP.match(path):
            return "sitemap"
        if path == "/" or DIRECTORY.match(path):
            return "listing"
        return None
    if ARTICLE.match(path):
        return "article"
    if path == "/" or PAGE.match(path):
        return "listing"
    return None
