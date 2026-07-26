from __future__ import annotations

from urllib.parse import urlparse, urlunparse

PCS_HOST_ALIASES = {"procyclingstats.com", "www.procyclingstats.com"}


def canonicalize_pcs_url(source_url: str, base_url: str) -> str:
    parsed = urlparse(source_url)
    if parsed.scheme not in {"http", "https"} or parsed.netloc.lower() not in PCS_HOST_ALIASES:
        return source_url

    base = urlparse(base_url.rstrip("/"))
    return urlunparse(
        (
            base.scheme or "https",
            base.netloc,
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment,
        )
    )


def is_configured_pcs_url(source_url: str, base_url: str) -> bool:
    parsed = urlparse(canonicalize_pcs_url(source_url, base_url))
    base = urlparse(base_url.rstrip("/"))
    return parsed.scheme in {"http", "https"} and parsed.netloc.lower() == base.netloc.lower()
