"""Проверка инвариантов и сборка одного самодостаточного HTML."""

from __future__ import annotations

import json
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


def main() -> None:
    bank = json.loads((ROOT / 'data/bank.json').read_text('utf-8'))
    errors = validate(bank)
    if errors:
        print(f'сборка остановлена, нарушений: {len(errors)}')
        for message in errors[:40]:
            print(' -', message)
        raise SystemExit(1)

    html = (ROOT / 'src/template.html').read_text('utf-8')
    html = html.replace('/*BANK_DESCRIPTION*/', escape(bank_description(bank)))
    html = html.replace('/*QUIZ_CSS*/', minify_css((ROOT / 'src/quiz.css').read_text('utf-8')))
    engine = minify_js((ROOT / 'src/quiz.mjs').read_text('utf-8').replace('export ', ''))
    html = html.replace('/*QUIZ_ENGINE*/', engine)
    html = html.replace('/*QUESTION_BANK*/', serialize_bank(bank))
    html = html.replace('/*QUIZ_UI*/', minify_js((ROOT / 'src/quiz.ui.js').read_text('utf-8')))
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
