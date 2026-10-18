"""Сверка цитаты с сохранённой копией страницы.

    python3 quote.py <файл .txt из кэша> "<цитата>"

Цитата должна стоять в тексте страницы дословно. Сравнение — после нормализации: NFKC (полноширинные
знаки → обычные), без пробелов и переводов строк (pdftotext и разметка рвут строки посреди фразы),
кавычки «»“”„「」『』 → ", тире –—― → -. Если дословно нет — печатает самый похожий фрагмент
страницы: по нему видно, где цитата расходится.
"""
import difflib
import sys
import unicodedata
from pathlib import Path

QUOTES = str.maketrans({c: '"' for c in '«»“”„「」『』‘’\''} | {c: '-' for c in '–—―‐'})


def normalize(text: str) -> tuple[str, list[int]]:
    """Нормализованный текст и позиция каждого его знака в исходном."""
    chars, where = [], []
    for index, char in enumerate(text):
        for part in unicodedata.normalize('NFKC', char).translate(QUOTES):
            if not part.isspace():
                chars.append(part.lower())
                where.append(index)
    return ''.join(chars), where


def find(page: str, quote: str) -> tuple[bool, str]:
    """(нашлась ли дословно, фрагмент страницы — найденный или самый похожий)."""
    hay, where = normalize(page)
    needle, _ = normalize(quote)
    if not needle:
        return False, ''
    at = hay.find(needle)
    if at >= 0:
        return True, page[where[at]:where[at + len(needle) - 1] + 1]
    size, best, best_at = len(needle), 0.0, 0
    step = max(1, size // 4)
    for start in range(0, max(1, len(hay) - size + 1), step):
        ratio = difflib.SequenceMatcher(None, needle, hay[start:start + size], autojunk=False).quick_ratio()
        if ratio > best:
            best, best_at = ratio, start
    end = min(len(where) - 1, best_at + size - 1)
    return False, page[where[best_at]:where[end] + 1] if where else ''


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    page = Path(sys.argv[1]).read_text('utf-8')
    ok, fragment = find(page, sys.argv[2])
    if ok:
        print('есть дословно')
    else:
        print('НЕТ дословно. Самый похожий фрагмент страницы:\n' + fragment)
        sys.exit(1)


if __name__ == '__main__':
    main()
