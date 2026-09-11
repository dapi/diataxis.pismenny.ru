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
russian_pages = [page for page in root_pages if (SITE / "en") not in page.parents]

assert_contains(
    SITE / "index.html",
    [
        'lang="ru"',
        "Системный подход к созданию технической документации",
        "Учебные руководства",
        'src="_images/diataxis.ru.png"',
        "https://diataxis.fr/",
        "https://creativecommons.org/licenses/by-sa/4.0/",
        "https://pismenny.ru/",
        "Неофициальный русский перевод",
    ],
)
assert_contains(
    SITE / "start-here" / "index.html",
    [
        "Учебные руководства",
        "Практические руководства",
        "Справочник",
        "Объяснения",
    ],
)
assert_contains(
    SITE / "reference-explanation" / "index.html",
    [
        "Различие между справочником и объяснением",
        "Если материал скучен и не запоминается",
    ],
)
assert_contains(
    SITE / "en" / "index.html",
    [
        'lang="en"',
        "A systematic approach to technical documentation authoring",
        'src="_images/diataxis.png"',
    ],
)
assert (SITE / "_images" / "diataxis.ru.png").is_file()

localized_overviews = {
    "tutorials": "overview-tutorials.ru.png",
    "how-to-guides": "overview-how-to.ru.png",
    "explanation": "overview-explanation.ru.png",
    "reference": "overview-reference.ru.png",
}
for page_name, image_name in localized_overviews.items():
    assert_contains(SITE / page_name / "index.html", [f'src="../_images/{image_name}"'])
    assert (SITE / "_images" / image_name).is_file()
    assert_contains(
        SITE / "en" / page_name / "index.html",
        [f'src="../_images/{image_name.removesuffix(".ru.png")}.png"'],
    )

for page in root_pages:
    text = page.read_text(encoding="utf-8")
    assert "ZXQPH" not in text, f"unrestored placeholder in {page}"
    if 'http-equiv="refresh"' in text:
        continue
    assert "https://github.com/dapi/diataxis.pismenny.ru" in text, f"repository link missing in {page}"

forbidden_machine_translation_fragments = [
    "Диатаксис",
    "Правила большого пальца",
    "атомный корм",
    "Как управлять <strong>",
    "пользователь <em>делать</em>",
    "пользователь <em>знать</em>",
    "переводятся на <em>не</em>",
    "you need to leave",
    "ЦИТАЦИЯ.cff",
]
for page in russian_pages:
    text = page.read_text(encoding="utf-8")
    for fragment in forbidden_machine_translation_fragments:
        assert fragment not in text, f"machine-translation fragment {fragment!r} in {page}"

print(f"checked {len(root_pages)} generated pages")
