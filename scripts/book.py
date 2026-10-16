"""Книга для чтения: проверка и сборка.

    .venv/bin/python3 scripts/book.py check            — формат, длина, уровень, источники всех уроков
    .venv/bin/python3 scripts/book.py build [--drafts] — PDF и EPUB в book/out/

Нужен jieba (requirements.txt): python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
"""
import argparse
import os
import sys
from pathlib import Path

from book_lesson import BOOK, LessonError, body_text, count_han, load_blocks, load_lessons, validate_lesson
from book_level import annotate, load_vocab
from book_render import TITLE, book_html, write_epub, write_pdf


def _annotated(src: Path, hsk_dir: Path):
    """Блоки и уроки: (урок, ошибки формата, разметка пиньиня с ошибками уровня)."""
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


def build(src: Path = BOOK / 'src', out_dir: Path = BOOK / 'out', drafts: bool = False, pdf: bool = True) -> list[str]:
    """Собирает PDF и EPUB; без drafts — только принятые уроки. Возвращает id уроков в книге."""
    blocks, items = _annotated(src, BOOK / 'hsk')
    chosen = [a for lesson, _, a in items if drafts or lesson.status == 'accepted']
    if not chosen:
        return []
    out_dir.mkdir(parents=True, exist_ok=True)
    html_path = out_dir / f'{TITLE}.html'
    img_base = Path(os.path.relpath(BOOK, out_dir)).as_posix() + '/'
    html_path.write_text(book_html(chosen, blocks, BOOK, drafts, img_base), encoding='utf-8')
    write_epub(chosen, blocks, out_dir / f'{TITLE}.epub', BOOK, drafts)
    if pdf:
        write_pdf(html_path, out_dir / f'{TITLE}.pdf')
    return [a.lesson.id for a in chosen]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='Книга для чтения: проверка и сборка')
    sub = parser.add_subparsers(dest='command', required=True)
    p_check = sub.add_parser('check')
    p_check.add_argument('--src', type=Path, default=BOOK / 'src')
    p_build = sub.add_parser('build')
    p_build.add_argument('--src', type=Path, default=BOOK / 'src')
    p_build.add_argument('--drafts', action='store_true', help='включить черновики с пометкой')
    args = parser.parse_args(argv)
    lines, errors = check(args.src)
    if args.command == 'check' or errors:
        print('\n'.join(lines))
        return 1 if errors else 0
    ids = build(args.src, drafts=args.drafts)
    if not ids:
        print('Нет принятых уроков (status: accepted); для черновиков — build --drafts')
        return 1
    print(f'Уроков в книге: {len(ids)} → book/out/{TITLE}.pdf, book/out/{TITLE}.epub')
    return 0


if __name__ == '__main__':
    sys.exit(main())
