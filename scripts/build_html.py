"""Проверка инвариантов и сборка одного самодостаточного HTML."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from minify import minify_css, minify_js
from normalize import completeness_errors, fragment_pairs, language_errors
from taxonomy import TOPICS

TARGET = ROOT / 'dist/lingvostranovedenie-trainer.html'


def validate(bank: list[dict]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for record in bank:
        where = record['id']
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
    html = html.replace('/*QUIZ_CSS*/', minify_css((ROOT / 'src/quiz.css').read_text('utf-8')))
    engine = minify_js((ROOT / 'src/quiz.mjs').read_text('utf-8').replace('export ', ''))
    html = html.replace('/*QUIZ_ENGINE*/', engine)
    html = html.replace('/*QUESTION_BANK*/', json.dumps(bank, ensure_ascii=False, separators=(',', ':')))
    html = html.replace('/*QUIZ_UI*/', minify_js((ROOT / 'src/quiz.ui.js').read_text('utf-8')))
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(html, encoding='utf-8')
    verified = sum(1 for record in bank if record['answer']['state'] == 'verified')
    print(f'собрано: {TARGET} ({TARGET.stat().st_size // 1024} КБ), проверено {verified} из {len(bank)}')


if __name__ == '__main__':
    main()
