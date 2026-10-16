"""Импорт списков слов HSK 2.0 из колод Anki автора в book/hsk/hsk20.tsv.

Колоды накопительные (в HSK4F — все слова уровней 1–4), поэтому уровень слова —
наименьший уровень колоды, в которой оно встретилось. Запуск:
    python3 scripts/book_hsk.py "<папка с колодами Anki>"
"""
import re
import sys
from pathlib import Path

BOOK = Path(__file__).resolve().parents[1] / 'book'
DECKS = [(1, 'HSK1.txt'), (2, 'HSK2.txt'), (3, 'HSK3F.txt'),
         (4, 'HSK4F.txt'), (5, 'HSK5F.txt'), (6, 'HSK6F.txt')]


def import_anki(anki_dir: Path) -> list[tuple[str, str, int]]:
    found: dict[str, tuple[str, int]] = {}
    for level, name in DECKS:
        path = anki_dir / name
        if not path.exists():
            continue
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            parts = line.split('\t')
            if len(parts) < 2 or not parts[0].strip():
                continue
            for variant in re.split(r'[|｜/／]', parts[0]):
                word = re.sub(r'[（(].*?[)）]', '', variant).strip()
                if word and (word not in found or found[word][1] > level):
                    found[word] = (parts[1].strip(), level)
    return sorted(((w, p, lv) for w, (p, lv) in found.items()), key=lambda r: (r[2], r[0]))


def write_tsv(rows, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(f'{w}\t{p}\t{lv}\n' for w, p, lv in rows), encoding='utf-8')


if __name__ == '__main__':
    rows = import_anki(Path(sys.argv[1]))
    write_tsv(rows, BOOK / 'hsk' / 'hsk20.tsv')
    print(f'{len(rows)} слов → book/hsk/hsk20.tsv')
