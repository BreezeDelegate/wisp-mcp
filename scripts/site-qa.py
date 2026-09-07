from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
PAGES = [DOCS / "index.html", DOCS / "en/index.html"]
ASSETS = [
    "assets/site.css",
    "assets/site.js",
    "assets/flag-fr.webp",
    "assets/flag-gb.webp",
    "assets/wisp-client-panel.webp",
]


class Audit(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.hrefs: list[str] = []
        self.imgs: list[tuple[str | None, bool]] = []
        self.lang: str | None = None
        self.viewport = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = dict(attrs)
        if tag == "html":
            self.lang = data.get("lang")
        if tag == "meta" and data.get("name") == "viewport":
            self.viewport = True
        if tag == "a" and data.get("href"):
            self.hrefs.append(data["href"] or "")
        if tag == "img":
            self.imgs.append((data.get("src"), "alt" in data))
        if data.get("id"):
            self.ids.add(data["id"] or "")


for page in PAGES:
    text = page.read_text(encoding="utf-8")
    audit = Audit()
    audit.feed(text)
    assert audit.lang in {"fr", "en"} and audit.viewport
    assert "https://wisp.hinoake.com" in text
    assert "breezedelegate.github.io/wisp-mcp" not in text
    assert "GPT-5.6 Sol" in text and "WISP_API_TOKEN" not in text
    for src, has_alt in audit.imgs:
        assert has_alt, (page, src)
        if src and src.startswith("/"):
            assert (DOCS / src.lstrip("/")).exists(), (page, src)
    for href in audit.hrefs:
        if href.startswith("#") and len(href) > 1:
            assert href[1:] in audit.ids, (page, href)

for asset in ASSETS:
    assert (DOCS / asset).is_file(), asset

nginx = (ROOT / "deploy/site/nginx/default.conf").read_text(encoding="utf-8")
assert "default-src 'self'" in nginx
assert "script-src 'self'" in nginx
assert "connect-src 'none'" in nginx

print("SITE_STATIC_QA_OK pages=2 assets=5 csp=quoted")
