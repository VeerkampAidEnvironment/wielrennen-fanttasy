from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.parse import urlparse

from flask import current_app

IMAGE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
CONTENT_TYPES_BY_EXTENSION = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


def pcs_image_cache_path(source_url: str) -> Path:
    digest = hashlib.sha256(source_url.encode("utf-8")).hexdigest()
    parsed_ext = Path(urlparse(source_url).path).suffix.lower()
    extension = parsed_ext if parsed_ext in CONTENT_TYPES_BY_EXTENSION else ".img"
    return Path(current_app.instance_path) / "pcs-image-cache" / f"{digest}{extension}"


def load_cached_pcs_image(source_url: str) -> tuple[bytes, str] | None:
    cache_path = pcs_image_cache_path(source_url)
    content_type = CONTENT_TYPES_BY_EXTENSION.get(cache_path.suffix.lower())
    if not content_type or not cache_path.is_file():
        return None
    content = cache_path.read_bytes()
    return (content, content_type) if content else None


def store_cached_pcs_image(source_url: str, content: bytes) -> Path:
    cache_path = pcs_image_cache_path(source_url)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(content)
    return cache_path
