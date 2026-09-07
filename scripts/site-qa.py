from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
PAGES = [DOCS / "index.html", DOCS / "en/index.html"]
REQUIRED_ASSETS = [
    "assets/site.css",
    "assets/site.js",
    "assets/flag-fr.webp",
    "assets/flag-gb.webp",
]
BANNED_LEGACY_MARKERS = [
    'class="hero',
    "section-head",
    "trustline",
    "choice-band",
    "panel-proof",
    "faq-list",
    "setup-layout",
    "product-label",
]


class Audit(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.hrefs: list[str] = []
        self.imgs: list[tuple[str | None, bool]] = []
        self.lang: str | None = None
        self.viewport = False
        self.onboarding_steps = 0
        self.main_count = 0
        self.section_count = 0
        self.onboarding_roots = 0

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
        if tag == "main":
            self.main_count += 1
        if tag == "section":
            self.section_count += 1
        if "data-onboarding-step" in data:
            self.onboarding_steps += 1
        if "data-onboarding" in data:
            self.onboarding_roots += 1
        if data.get("id"):
            self.ids.add(data["id"] or "")


for page in PAGES:
    text = page.read_text(encoding="utf-8")
    audit = Audit()
    audit.feed(text)

    assert audit.lang in {"fr", "en"}, (page, audit.lang)
    assert audit.viewport, page
    assert audit.main_count == 1, (page, audit.main_count)
    assert audit.section_count == 0, (page, audit.section_count)
    assert audit.onboarding_roots == 1, (page, audit.onboarding_roots)
    assert audit.onboarding_steps == 8, (page, audit.onboarding_steps)
    assert "https://wisp.hinoake.com" in text
    assert "breezedelegate.github.io/wisp-mcp" not in text
    assert "GPT-5.6 Sol" in text
    assert "WISP_API_TOKEN" not in text
    assert 'data-require-check="install_ok"' in text
    assert 'data-require-check="tunnel_ok"' in text
    assert "Wisp API: OK" in text
    assert 'data-copy-id="skill-memory"' in text
    assert 'data-copy-id="skill-wisp"' in text
    assert 'data-copy-id="skill-release"' in text

    for marker in BANNED_LEGACY_MARKERS:
        assert marker not in text, (page, marker)

    for src, has_alt in audit.imgs:
        assert has_alt, (page, src)
        if src and src.startswith("/"):
            assert (DOCS / src.lstrip("/")).exists(), (page, src)

for asset in REQUIRED_ASSETS:
    assert (DOCS / asset).is_file(), asset

css = (DOCS / "assets/site.css").read_text(encoding="utf-8")
for marker in [".hero", ".section-head", ".trustline", ".choice-band", ".panel-proof", ".faq"]:
    assert marker not in css, marker
assert "@media (max-width:760px)" in css
assert "min-width:320px" in css
assert "44px" in css

js = (DOCS / "assets/site.js").read_text(encoding="utf-8")
assert "localStorage" in js
assert "history.replaceState" in js
assert "fetch(" not in js
assert "XMLHttpRequest" not in js

nginx = (ROOT / "deploy/site/nginx/default.conf").read_text(encoding="utf-8")
assert "default-src 'self'" in nginx
assert "script-src 'self'" in nginx
assert "style-src 'self'" in nginx
assert "connect-src 'none'" in nginx

print("SITE_STATIC_QA_OK onboarding=clean-slate pages=2 steps=8")
