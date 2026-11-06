from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit


TRACKING_PARAMETERS = {"fbclid", "gclid", "dclid", "msclkid"}


def normalize_url(url, *, base, hosts, canonical_host):
    """Normalize a URL while enforcing a site's allowed hosts."""
    try:
        parts = urlsplit(urljoin(base, url))
        port = parts.port
    except (TypeError, ValueError):
        return None
    if parts.scheme not in {"http", "https"} or parts.hostname not in hosts:
        return None
    if parts.username or parts.password or port not in (None, 80, 443):
        return None
    query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not key.lower().startswith("utm_") and key.lower() not in TRACKING_PARAMETERS
    ]
    return urlunsplit(("https", canonical_host, parts.path or "/", urlencode(sorted(query)), ""))
