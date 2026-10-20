"""Пиньинь к китайскому тексту тренировки — для настройки «Пиньинь» в шапке.

Транскрипция нужна вариантам ответа, китайской формулировке (`questionZh`) и китайским
вставкам в русском вопросе («Как выглядит десерт 双皮奶?»). Скрипт пишет
`data/pinyin.json`: текст → слоги со знаками тона. Файл коммитится, чтобы транскрипцию можно
было просмотреть в диффе; сборка встраивает его в страницу, а для текста без записи
транскрипция просто не показывается.

Нужен pypinyin (`pip install pypinyin==0.55.0`, в CI ставится сам). Многозначные иероглифы
он читает по словарю слов и иногда ошибается (大佛 — dà fú вместо dà fó): исправления —
в `data/pinyin-phrases.json` (слово → слоги через пробел), они применяются ко всему тексту.
Запись из одного иероглифа действует, только когда текст и есть этот иероглиф (вариант «藏» —
сокращённое название Тибета), чтобы не менять чтение знака во всех остальных словах.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BANK = ROOT / 'data/bank.json'
PHRASES = ROOT / 'data/pinyin-phrases.json'
TARGET = ROOT / 'data/pinyin.json'

HAN = r'㐀-䶿一-鿿豈-﫿'
# китайская вставка в русском вопросе: иероглифы, имена с «·» внутри. То же выражение —
# HAN_RUN в src/quiz.mjs: страница ищет транскрипцию по тем же кускам текста
HAN_RUN = re.compile(f'[{HAN}]+(?:[·・][{HAN}]+)*')
PUNCTUATION = str.maketrans({
    '，': ',', '、': ',', '。': '.', '；': ';', '：': ':', '！': '!', '？': '?',
    '（': '(', '）': ')', '《': '«', '》': '»', '・': '·',
})
MARK = '\x00'


def texts(bank: list[dict]) -> set[str]:
    """Китайский текст, который ученик видит в раунде."""
    found: set[str] = set()
    for record in bank:
        found.update(option['zh'] for option in record['options'])
        if record.get('questionZh'):
            found.add(record['questionZh'])
        found.update(HAN_RUN.findall(record['questionRu']))
    return {text for text in found if re.search(f'[{HAN}]', text)}


def transcriber(phrases: dict[str, str]):
    from pypinyin import Style, lazy_pinyin, load_phrases_dict

    load_phrases_dict({word: [[syllable] for syllable in reading.split()]
                       for word, reading in phrases.items() if len(word) > 1})

    def transcribe(text: str) -> str:
        if text in phrases:
            return phrases[text]
        # не-китайский кусок (цифры, латиница, знаки) помечается и идёт как есть
        items = lazy_pinyin(text, style=Style.TONE, errors=lambda chunk: [MARK + chunk])
        words = [item[1:].translate(PUNCTUATION).strip() if item.startswith(MARK) else item
                 for item in items]
        line = ' '.join(word for word in words if word)
        # знаки прилегают к слогу: закрывающие — к предыдущему, открывающие — к следующему
        line = re.sub(r'\s+([,.;:!?)»”…·])', r'\1', line)
        line = re.sub(r'([(«“·])\s+', r'\1', line)
        # знаки подряд приходят одним куском («”、“»): после запятой нужен пробел
        return re.sub(r'([,;:!?])(?=[^\s\d,.;:!?)»”…])', r'\1 ', line)

    return transcribe


def main() -> None:
    try:
        import pypinyin  # noqa: F401
    except ImportError:
        sys.exit('Нужен pypinyin: pip install pypinyin==0.55.0 (или в виртуальном окружении)')
    bank = json.loads(BANK.read_text('utf-8'))
    phrases = json.loads(PHRASES.read_text('utf-8'))
    transcribe = transcriber(phrases)
    table = {text: transcribe(text) for text in sorted(texts(bank))}
    TARGET.write_text(json.dumps(table, ensure_ascii=False, indent=0) + '\n', 'utf-8')
    print(f'Пиньинь: {len(table)} строк → {TARGET.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
