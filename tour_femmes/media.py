from __future__ import annotations

import hashlib
from threading import Lock
from pathlib import Path
from time import monotonic, sleep
from urllib.parse import urlparse

import requests
from flask import Blueprint, Response, abort, current_app, send_file

from tour_femmes.pcs_urls import canonicalize_pcs_url, is_configured_pcs_url

media_bp = Blueprint("media", __name__, url_prefix="/media")

IMAGE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
IMAGE_DOWNLOAD_LOCK = Lock()
LAST_IMAGE_REQUEST_AT = 0.0
IMAGE_COOLDOWN_UNTIL = 0.0
TRANSPARENT_PIXEL = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\xff"
    b"\xff?\x00\x05\xfe\x02\xfeA\xe2!\xbc\x00\x00\x00\x00IEND\xaeB`\x82"
)


@media_bp.route("/pcs-image")
def pcs_image():
    source_url = _validated_pcs_url()
    cache_path = _cache_path(source_url)
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    if not cache_path.exists():
        response = _download_image(source_url)
        if response is None:
            return _fallback_image()
        content_type = response.headers.get("Content-Type", "").split(";")[0].lower()
        if content_type not in IMAGE_EXTENSIONS:
            return _fallback_image()
        cache_path.write_bytes(response.content)

    return send_file(cache_path, max_age=86400)


def _download_image(source_url: str) -> requests.Response | None:
    global IMAGE_COOLDOWN_UNTIL, LAST_IMAGE_REQUEST_AT

    with IMAGE_DOWNLOAD_LOCK:
        now = monotonic()
        if now < IMAGE_COOLDOWN_UNTIL:
            return None

        delay = float(current_app.config.get("PCS_IMAGE_REQUEST_DELAY_SECONDS", 3.0))
        elapsed = now - LAST_IMAGE_REQUEST_AT
        if elapsed < delay:
            sleep(delay - elapsed)

        try:
            response = requests.get(
                source_url,
                timeout=20,
                headers={
                    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9,nl;q=0.8",
                    "Referer": current_app.config["PCS_BASE_URL"],
                    "User-Agent": current_app.config["PCS_USER_AGENT"],
                },
            )
            LAST_IMAGE_REQUEST_AT = monotonic()
            if response.status_code == 429:
                IMAGE_COOLDOWN_UNTIL = LAST_IMAGE_REQUEST_AT + float(current_app.config.get("PCS_429_BACKOFF_SECONDS", 30.0))
                return None
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            current_app.logger.warning("PCS image download failed: %s (%s)", source_url, exc)
            return None


def _fallback_image() -> Response:
    return Response(TRANSPARENT_PIXEL, mimetype="image/png", headers={"Cache-Control": "public, max-age=300"})


def _validated_pcs_url() -> str:
    from flask import request

    source_url = request.args.get("url", "").strip()
    source_url = canonicalize_pcs_url(source_url, current_app.config["PCS_BASE_URL"])
    parsed = urlparse(source_url)
    if parsed.scheme not in {"http", "https"} or not is_configured_pcs_url(
        source_url,
        current_app.config["PCS_BASE_URL"],
    ):
        abort(400)
    if not parsed.path.lower().startswith("/images/"):
        abort(400)
    return source_url


def _cache_path(source_url: str) -> Path:
    digest = hashlib.sha256(source_url.encode("utf-8")).hexdigest()
    parsed_ext = Path(urlparse(source_url).path).suffix.lower()
    extension = parsed_ext if parsed_ext in {".jpg", ".jpeg", ".png", ".webp", ".gif"} else ".img"
    return Path(current_app.instance_path) / "pcs-image-cache" / f"{digest}{extension}"
