from app.adapters.url_extract import extract_public_url


def test_extract_success(monkeypatch):
    html = "<article><h1>标题</h1><p>" + "正文内容" * 80 + "</p></article>"
    monkeypatch.setattr(
        "app.adapters.url_extract.fetch_html",
        lambda url: (200, html),
    )
    result = extract_public_url("https://example.com/a")
    assert result.ok is True
    assert result.title
    assert len(result.text) >= 200


def test_extract_login_wall(monkeypatch):
    monkeypatch.setattr(
        "app.adapters.url_extract.fetch_html",
        lambda url: (401, "login"),
    )
    result = extract_public_url("https://example.com/private")
    assert result.ok is False
    assert result.error_code == "URL_LOGIN_WALL"


def test_extract_too_short(monkeypatch):
    monkeypatch.setattr(
        "app.adapters.url_extract.fetch_html",
        lambda url: (200, "<p>太短了</p>"),
    )
    result = extract_public_url("https://example.com/short")
    assert result.ok is False
    assert result.error_code == "URL_TOO_SHORT"
