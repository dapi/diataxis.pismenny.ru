#!/usr/bin/env python3
"""Fill Russian gettext messages while preserving reStructuredText markup."""

from __future__ import annotations

import argparse
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import polib


ROOT = Path(__file__).resolve().parents[1]
CATALOG_DIR = ROOT / "translation" / "ru" / "LC_MESSAGES"
PLACEHOLDER = "ZXQPH{index}PHQXZ"

INLINE_RE = re.compile(
    r"(?P<brand>Diátaxis)"
    r"|:(?P<role>[A-Za-z0-9_-]+):`(?P<role_body>[^`]+)`"
    r"|``(?P<literal>[^`]*)``"
    r"|`(?P<link_label>[^`<]+?)\s*<(?P<link_target>https?://[^>]+)>`_"
    r"|(?P<strong>\*\*.+?\*\*)"
    r"|(?P<emphasis>(?<!\*)\*[^*]+\*(?!\*))"
    r"|(?P<url>https?://[^\s)>]+)"
    r"|(?P<substitution>\|[A-Za-z0-9_-]+\|)"
)

EXACT_TERMS = {
    "Tutorial": "Учебное руководство",
    "Tutorials": "Учебные руководства",
    "How-to guide": "Практическое руководство",
    "How-to guides": "Практические руководства",
    "Reference": "Справочник",
    "Explanation": "Объяснения",
    "Home": "Главная",
    "Next": "Далее",
    "Previous": "Назад",
    "Search": "Поиск",
    '<a href="%(path)s">Copyright</a> &#169; %(copyright)s': '<a href="%(path)s">Авторские права</a> &#169; %(copyright)s',
    "Copyright &#169; %(copyright)s": "Авторские права &#169; %(copyright)s",
    "Last updated on %(last_updated)s": "Последнее обновление: %(last_updated)s",
    "It's not the responsibility of a recipe to *teach* you how to make something. A professional chef who has made exactly the same thing multiple times before may still follow a recipe - even if they *created* the recipe themselves - to ensure that they do it correctly.": "Рецепт не обязан *учить* вас готовить. Профессиональный повар, который уже много раз готовил то же самое, всё равно может следовать рецепту — даже если он сам *создал* этот рецепт, — чтобы получить правильный результат.",
    "These are all good questions. Let’s start with the last one. *If the distinction is really so important, why isn’t it more obvious?*": "Это хорошие вопросы. Начнём с последнего. *Если различие действительно так важно, почему оно не очевиднее?*",
}


def translate_text(translator, value: str) -> str:
    translated = translator.translate(value)
    if not isinstance(translated, str) or not translated.strip():
        raise RuntimeError("translation provider returned an empty result")
    return translated


def mask_markup(translator, value: str) -> tuple[str, list[str]]:
    protected: list[str] = []

    def replace(match: re.Match[str]) -> str:
        original = match.group(0)
        if match.group("role"):
            body = match.group("role_body")
            target_match = re.fullmatch(r"(.+?)\s*<([^>]+)>", body)
            if target_match:
                label = target_match.group(1)
                target = target_match.group(2)
                original = f':{match.group("role")}:`{translate_text(translator, label)} <{target}>`'
        elif match.group("link_label"):
            label = translate_text(translator, match.group("link_label"))
            original = f'`{label} <{match.group("link_target")}>`_'
        elif match.group("strong"):
            original = f'**{translate_text(translator, match.group("strong")[2:-2])}**'
        elif match.group("emphasis"):
            original = f'*{translate_text(translator, match.group("emphasis")[1:-1])}*'
        protected.append(original)
        return PLACEHOLDER.format(index=len(protected) - 1)

    return INLINE_RE.sub(replace, value), protected


def restore_markup(value: str, protected: list[str]) -> str:
    for index, original in enumerate(protected):
        marker = PLACEHOLDER.format(index=index)
        if value.count(marker) != 1:
            raise ValueError(f"translation lost protected marker {marker}")
        value = value.replace(marker, original)
    return value


def translate_message(translator, message: str) -> str:
    if message in EXACT_TERMS:
        return EXACT_TERMS[message]
    masked, protected = mask_markup(translator, message)
    only_marker = re.fullmatch(r"ZXQPH\d+PHQXZ", masked)
    translated = masked if only_marker else translate_text(translator, masked)
    return restore_markup(translated, protected)


def markup_signature(value: str) -> tuple:
    return (
        tuple(re.findall(r":[A-Za-z0-9_-]+:", value)),
        tuple(re.findall(r"(?<=<)[A-Za-z0-9_./:#?=&-]+(?=>)", value)),
        tuple(re.findall(r"https?://[^\s)>]+", value)),
        value.count("**"),
        value.count("*"),
        value.count("``"),
        value.count("`"),
        tuple(re.findall(r"%\([^)]+\)[A-Za-z]", value)),
        tuple(re.findall(r"\|[A-Za-z0-9_-]+\|", value)),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--provider", choices=("google", "argos"), default="google")
    parser.add_argument("--workers", type=int, default=0)
    parser.add_argument("--file", action="append", default=[])
    parser.add_argument("--repair-markup", action="store_true")
    args = parser.parse_args()

    state = threading.local()

    def get_translator():
        if hasattr(state, "translator"):
            return state.translator
        if args.provider == "argos":
            import argostranslate.translate

            state.translator = argostranslate.translate.get_translation_from_codes("en", "ru")
            if state.translator is None:
                raise RuntimeError("Argos en→ru model is not installed")
        else:
            from deep_translator import GoogleTranslator

            state.translator = GoogleTranslator(source="en", target="ru")
        return state.translator

    catalogs: dict[Path, polib.POFile] = {}
    jobs: list[tuple[Path, polib.POEntry]] = []
    failures: list[str] = []
    for path in sorted(CATALOG_DIR.glob("*.po")):
        if args.file and path.name not in args.file:
            continue
        catalog = polib.pofile(path)
        catalogs[path] = catalog
        for entry in catalog:
            if args.repair_markup and entry.msgstr and markup_signature(entry.msgid) == markup_signature(entry.msgstr):
                continue
            if entry.obsolete or (entry.msgstr and not args.force) or not entry.msgid:
                continue
            if args.limit and len(jobs) >= args.limit:
                break
            jobs.append((path, entry))
        if args.limit and len(jobs) >= args.limit:
            break

    def run_job(index: int, entry: polib.POEntry) -> tuple[int, str]:
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                return index, translate_message(get_translator(), entry.msgid)
            except Exception as error:
                last_error = error
                time.sleep(attempt + 1)
        raise RuntimeError(str(last_error))

    workers = args.workers or (6 if args.provider == "google" else 1)
    changed_paths: set[Path] = set()
    with ThreadPoolExecutor(max_workers=workers) as executor:
        pending = {
            executor.submit(run_job, index, entry): (path, entry)
            for index, (path, entry) in enumerate(jobs)
        }
        for future in as_completed(pending):
            path, entry = pending[future]
            try:
                _, entry.msgstr = future.result()
            except Exception as error:
                failures.append(f"{path.name}: {entry.msgid[:80]!r}: {error}")
                continue
            entry.flags = [flag for flag in entry.flags if flag != "fuzzy"]
            changed_paths.add(path)

    for path in sorted(changed_paths):
        catalog = catalogs[path]
        if catalog:
            catalog.metadata["Last-Translator"] = "Danil Pismenny <danil@pismenny.ru>"
            catalog.metadata["Language-Team"] = "Russian"
            catalog.save(path)

    print(f"translated messages: {len(jobs) - len(failures)}")
    if failures:
        print("messages left untranslated:")
        for failure in failures:
            print(f"- {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
