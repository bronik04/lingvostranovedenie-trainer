"""Книга для чтения: проверка и сборка.

    .venv/bin/python3 scripts/book.py check            — формат, длина, уровень, источники всех уроков
    .venv/bin/python3 scripts/book.py build [--drafts] — PDF и EPUB в book/out/

Нужен jieba (requirements.txt): python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
"""
import argparse
import sys
from pathlib import Path

from book_lesson import BOOK, LessonError, body_text, count_han, load_blocks, load_lessons, validate_lesson
from book_level import annotate, load_vocab


def _annotated(src: Path, hsk_dir: Path):
    """Уроки с разметкой пиньиня и ошибками; ошибки разбора файла — отдельным списком."""
    blocks = load_blocks()
    vocab = load_vocab(hsk_dir)
    lessons = load_lessons(src)
    return blocks, [(l, validate_lesson(l, blocks), annotate(l, vocab)) for l in lessons]


def check(src: Path = BOOK / 'src', hsk_dir: Path = BOOK / 'hsk') -> tuple[list[str], int]:
    lines: list[str] = []
    try:
        blocks, items = _annotated(src, hsk_dir)
    except LessonError as e:
        return [str(e)], 1
    errors = 0
    seen: dict[str, Path] = {}
    for lesson, problems, a in items:
        block = next((b for b in blocks if b['slug'] == lesson.block), None)
        bounds = f' ({block["min"]}–{block["max"]})' if block else ''
        lines.append(f'{lesson.block}/{lesson.path.stem} · {lesson.status} · '
                     f'{count_han(body_text(lesson))}{bounds} · HSK5: {len(a.hsk5)} · HSK6: {len(a.hsk6)}')
        problems = list(problems) + a.errors
        if lesson.id in seen:
            problems.append(f'повтор id «{lesson.id}» — уже в {seen[lesson.id].name}')
        seen.setdefault(lesson.id, lesson.path)
        lines += [f'    {p}' for p in problems]
        errors += len(problems)
    lines.append(f'Уроков: {len(items)}, ошибок: {errors}')
    return lines, errors


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='Книга для чтения: проверка и сборка')
    sub = parser.add_subparsers(dest='command', required=True)
    p_check = sub.add_parser('check')
    p_check.add_argument('--src', type=Path, default=BOOK / 'src')
    args = parser.parse_args(argv)
    if args.command == 'check':
        lines, errors = check(args.src)
        print('\n'.join(lines))
        return 1 if errors else 0
    return 2


if __name__ == '__main__':
    sys.exit(main())
