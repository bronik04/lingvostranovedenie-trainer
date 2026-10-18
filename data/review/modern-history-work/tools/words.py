"""Счёт слов цитаты для бюджета «не больше 25 слов на публикацию» (правило «Достопримечательностей»):
китайский текст — словами jieba (pylib/ рядом), остальное — словами через пробел; куски одной
публикации (одного url) складываются.

    python3 words.py "<цитата>"
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'pylib'))
try:
    import jieba
    jieba.setLogLevel(60)
except ImportError:  # запасной счёт: примерно 1,6 иероглифа на слово
    jieba = None

HAN = re.compile(r'[㐀-鿿]+')
LIMIT = 25


def count(text: str) -> int:
    n = 0
    for part in re.split(r'([㐀-鿿]+)', text):
        if not part:
            continue
        if HAN.fullmatch(part):
            n += len([w for w in jieba.cut(part) if w.strip()]) if jieba else -(-len(part) * 10 // 16)
        else:
            n += len(re.findall(r'[\w\d]+', part))
    return n


if __name__ == '__main__':
    print(count(' '.join(sys.argv[1:])))
