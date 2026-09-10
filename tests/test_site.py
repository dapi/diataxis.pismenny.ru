#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_build" / "site"


def assert_contains(path: Path, fragments: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    for fragment in fragments:
        assert fragment in text, f"{fragment!r} is absent from {path}"


root_pages = sorted(SITE.rglob("index.html"))
assert len(root_pages) >= 30, f"expected Russian and English pages, got {len(root_pages)}"

assert_contains(
    SITE / "index.html",
    [
        'lang="ru"',
        "Системный подход к созданию технической документации",
        "Учебные руководства",
        "https://diataxis.fr/",
        "https://creativecommons.org/licenses/by-sa/4.0/",
        "https://pismenny.ru/",
    ],
)
assert_contains(
    SITE / "en" / "index.html",
    ['lang="en"', "A systematic approach to technical documentation authoring"],
)

for page in root_pages:
    text = page.read_text(encoding="utf-8")
    assert "ZXQPH" not in text, f"unrestored placeholder in {page}"
    if 'http-equiv="refresh"' in text:
        continue
    assert "https://github.com/dapi/diataxis.pismenny.ru" in text, f"repository link missing in {page}"

print(f"checked {len(root_pages)} generated pages")
