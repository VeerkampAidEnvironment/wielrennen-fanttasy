from tour_femmes import _pcs_image_url, create_app
from tour_femmes.pcs_urls import canonicalize_pcs_url, is_configured_pcs_url
from requests import Response

from tour_femmes.services.pcs import PcsClient, normalize_event_reference, pcs_forbidden_hint


class TestConfig:
    SECRET_KEY = "test"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True
    ADMIN_PASSWORD = "admin"
    PCS_BASE_URL = "https://www.procyclingstats.com"
    APP_TIMEZONE = "Europe/Amsterdam"


def test_pcs_urls_are_canonicalized_to_configured_www_host():
    assert (
        canonicalize_pcs_url(
            "https://procyclingstats.com/race/tour-de-france-femmes/2026?x=1",
            "https://www.procyclingstats.com",
        )
        == "https://www.procyclingstats.com/race/tour-de-france-femmes/2026?x=1"
    )
    assert is_configured_pcs_url(
        "https://procyclingstats.com/race/tour-de-france-femmes/2026",
        "https://www.procyclingstats.com",
    )


def test_pcs_client_uses_canonical_www_host():
    client = PcsClient(base_url="https://www.procyclingstats.com")

    assert (
        client.canonical_url("https://procyclingstats.com/rider/demi-vollering")
        == "https://www.procyclingstats.com/rider/demi-vollering"
    )


def test_pcs_client_sends_browser_like_headers():
    client = PcsClient(base_url="https://www.procyclingstats.com")

    document_headers = client.headers_for_url("https://www.procyclingstats.com/race/example/2026")
    image_headers = client.headers_for_url("https://www.procyclingstats.com/images/example.jpg", image=True)

    assert document_headers["Referer"] == "https://www.procyclingstats.com/"
    assert document_headers["Upgrade-Insecure-Requests"] == "1"
    assert document_headers["Sec-Fetch-Dest"] == "document"
    assert "text/html" in document_headers["Accept"]
    assert image_headers["Sec-Fetch-Dest"] == "image"
    assert image_headers["Accept"].startswith("image/")


def test_pcs_forbidden_hint_distinguishes_pythonanywhere_proxy():
    response = Response()
    response.status_code = 403
    response._content = b"Access to arbitrary websites is not available from free accounts"
    response.headers["Server"] = "PythonAnywhere"

    assert "PythonAnywhere-proxy/allowlist" in pcs_forbidden_hint(response)


def test_normalize_event_reference_uses_configured_base_for_pcs_urls():
    app = create_app(__name__ + ".TestConfig")
    with app.app_context():
        assert normalize_event_reference("https://procyclingstats.com/race/example/2026") == (
            "example",
            2026,
            "https://www.procyclingstats.com/race/example/2026",
        )


def test_pcs_image_helper_can_skip_server_side_proxy_for_pythonanywhere():
    app = create_app(__name__ + ".TestConfig")
    app.config["PCS_PROXY_IMAGES"] = False
    with app.test_request_context("/"):
        assert (
            _pcs_image_url("https://procyclingstats.com/images/riders/example.jpg")
            == "https://www.procyclingstats.com/images/riders/example.jpg"
        )


def test_pcs_image_helper_proxies_by_default():
    app = create_app(__name__ + ".TestConfig")
    with app.test_request_context("/"):
        image_url = _pcs_image_url("https://procyclingstats.com/images/riders/example.jpg")

    assert image_url.startswith("/media/pcs-image?url=")
