"""Проверка инвариантов и сборка одного самодостаточного HTML."""

from __future__ import annotations

import base64
import json
import re
import sys
import tempfile
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from minify import minify_css, minify_js
from normalize import completeness_errors, fragment_pairs, language_errors
from taxonomy import TOPICS
from authored import validate_authored
import chengyu
import pinyin

TARGET = ROOT / 'dist/lingvostranovedenie-trainer.html'


def plural_ru(count: int, forms: tuple[str, str, str]) -> str:
    """Форма слова для числа: (1 вопрос, 2 вопроса, 5 вопросов)."""
    if count % 10 == 1 and count % 100 != 11:
        return forms[0]
    if 2 <= count % 10 <= 4 and not 12 <= count % 100 <= 14:
        return forms[1]
    return forms[2]


def bank_description(bank: list[dict]) -> str:
    """Описание для поисковиков и превью ссылок — считается по банку при сборке,
    чтобы число вопросов не устаревало."""
    count = len(bank)
    every_verified = all(record['answer']['state'] == 'verified' for record in bank)
    sources = ('у каждого ответа — пояснение и ссылка на источник' if every_verified
               else 'у проверенных ответов — пояснение и ссылка на источник')
    return (f'{count} {plural_ru(count, ("вопрос", "вопроса", "вопросов"))} '
            f'по лингвострановедению Китая для подготовки к ВсОШ: вопрос по-русски, '
            f'варианты по-китайски, {sources}.')


def serialize_bank(bank: list[dict]) -> str:
    """Serialize JSON without allowing a data field to close the surrounding script tag."""
    return json.dumps(bank, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')


def validate(bank: list[dict]) -> list[str]:
    errors: list[str] = []
    olympiad_bank = [record for record in bank if record.get('origin') is None]
    authored_bank = [record for record in bank if record.get('origin') == 'addition']
    errors += validate_authored(authored_bank, olympiad_bank)
    seen: set[str] = set()
    for record in bank:
        where = record['id']
        if record.get('origin') not in {None, 'addition'}:
            errors.append(f'{where}: неизвестное происхождение вопроса')
        if where in seen:
            errors.append(f'{where}: повторяющийся id')
        seen.add(where)
        options = [option['zh'] for option in record['options']]
        errors += [f'{where}: {message}' for message in language_errors(record['questionRu'], options)]
        errors += [f'{where}: {message}'
                   for message in completeness_errors(record['questionRu'], record.get('questionZh'), options)]
        if record['topic'] not in TOPICS:
            errors.append(f'{where}: тема вне списка семи категорий: {record["topic"]!r}')
        ids = {option['id'] for option in record['options']}
        if record['answer']['optionId'] and record['answer']['optionId'] not in ids:
            errors.append(f'{where}: ответ указывает на несуществующий вариант')
        if record['answer']['state'] == 'verified':
            if not record['explanation']['ru'].strip():
                errors.append(f'{where}: проверенный ответ без пояснения')
            if not record['evidence']:
                errors.append(f'{where}: проверенный ответ без ссылки на источник')
    errors += [f'{left}: формулировка выглядит обрезком {right}' for left, right in
               fragment_pairs([(r['id'], r['questionRu']) for r in bank])]
    return errors


FONT_URL = re.compile(r'url\(([\w.-]+\.woff2)\)')


def embedded_fonts() -> str:
    """@font-face из src/fonts/fonts.css, где файл шрифта заменён data:-адресом."""
    fonts = ROOT / 'src/fonts'

    def inline(match: re.Match) -> str:
        data = base64.b64encode((fonts / match.group(1)).read_bytes()).decode('ascii')
        return f'url(data:font/woff2;base64,{data})'

    return FONT_URL.sub(inline, (fonts / 'fonts.css').read_text('utf-8'))


def stylesheet() -> str:
    """Шрифты, токены и компоненты дизайн-системы, затем стили самого тренажёра."""
    parts = [embedded_fonts()]
    parts += [(ROOT / path).read_text('utf-8')
              for path in ('src/ink/ink-tokens.css', 'src/ink/bundle.css', 'src/quiz.css', 'src/chengyu.css')]
    return '\n'.join(parts)


def pinyin_table(bank: list[dict]) -> dict[str, str]:
    """Транскрипции для настройки «Пиньинь» — только текст, который есть в банке.
    Таблицу пишет scripts/pinyin.py; текст без записи просто идёт без транскрипции."""
    table = json.loads((ROOT / 'data/pinyin.json').read_text('utf-8'))
    needed = pinyin.texts(bank)
    missing = needed - table.keys()
    if missing:
        print(f'пиньинь: нет транскрипции у {len(missing)} строк — запустите python3 scripts/pinyin.py')
    return {text: table[text] for text in sorted(needed - missing)}


def main() -> None:
    bank = json.loads((ROOT / 'data/bank.json').read_text('utf-8'))
    errors = validate(bank)
    olympiad_chengyu, draft_chengyu = chengyu.load('olympiad.json'), chengyu.load('drafts.json')
    errors += [f'чэнъюй: {message}' for message in chengyu.validate(olympiad_chengyu, draft_chengyu)]
    if errors:
        print(f'сборка остановлена, нарушений: {len(errors)}')
        for message in errors[:40]:
            print(' -', message)
        raise SystemExit(1)

    html = (ROOT / 'src/template.html').read_text('utf-8')
    html = html.replace('/*BANK_DESCRIPTION*/', escape(bank_description(bank)))
    html = html.replace('/*QUIZ_CSS*/', minify_css(stylesheet()))
    engine = minify_js((ROOT / 'src/quiz.mjs').read_text('utf-8').replace('export ', ''))
    html = html.replace('/*QUIZ_ENGINE*/', engine)
    html = html.replace('/*QUESTION_BANK*/', serialize_bank(bank))
    html = html.replace('/*PINYIN*/', serialize_bank(pinyin_table(bank)))
    html = html.replace('/*QUIZ_UI*/', minify_js((ROOT / 'src/quiz.ui.js').read_text('utf-8')))
    # раздел «Чэнъюй»: свой банк (олимпиадные + принятые составленные), движок и интерфейс
    chengyu_bank = chengyu.published(olympiad_chengyu, draft_chengyu)
    html = html.replace('/*CHENGYU_BANK*/', serialize_bank(chengyu_bank))
    cy_engine = minify_js((ROOT / 'src/chengyu.mjs').read_text('utf-8').replace('export ', ''))
    html = html.replace('/*CHENGYU_ENGINE*/', cy_engine)
    html = html.replace('/*CHENGYU_UI*/', minify_js((ROOT / 'src/chengyu.ui.js').read_text('utf-8')))
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    # через временный файл и замену: тесты читают dist/ параллельно со сборкой
    # в build.test.mjs и не должны увидеть файл, записанный наполовину
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=TARGET.parent,
                                     prefix=TARGET.name, suffix='.partial', delete=False) as partial:
        partial.write(html)
    try:
        Path(partial.name).replace(TARGET)
    finally:
        Path(partial.name).unlink(missing_ok=True)
    verified = sum(1 for record in bank if record['answer']['state'] == 'verified')
    print(f'собрано: {TARGET} ({TARGET.stat().st_size // 1024} КБ), проверено {verified} из {len(bank)}')


if __name__ == '__main__':
    main()
