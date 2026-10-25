"""Региональные варианты: решения по каждому заданию, отчёт для автора и сверка с бланками.

    python3 scripts/regions.py                      # проверить решения и переписать отчёт
    python3 scripts/regions.py --sources <папка>    # ещё и сверить расшифровку с PDF в папке вариантов

`data/review/regions.json` — решение по каждому заданию `data/regions/variants.json` (ключ — id задания,
например «2025-26-mun-spb-3»):

- `add` — идёт в банк;
- `in-bank` — тот же вопрос с тем же ответом уже есть, `bankId` — запись банка;
- `repeat` — то же задание другого региона в другой редакции, `sameAs` — id задания, которое идёт в банк;
- `narrow` — узкая местная деталь, `doubtful` — сомнительное (спорный ключ, ошибочная посылка, вопрос,
  зависящий от года, испорченные варианты), `ru-options` — варианты по-русски, `format` — меньше трёх
  вариантов или задание по картинке; у всех четырёх обязательна `reason`.

Отложенное автор возвращает правкой статуса на `add` (решение автора 2026-10-25: узкие — в отдельный
список, «если что, потом приму»). Отложенное скрипт выписывает ещё и страницей
`data/review/regions-excluded.html`: она открывается в браузере без сервера.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from normalize import CYRILLIC
from parsers.regions import task_id
from strict_json import loads_unique

VARIANTS = ROOT / 'data/regions/variants.json'
DECISIONS = ROOT / 'data/review/regions.json'
REPORT = ROOT / 'data/review/regions.md'
PAGE = ROOT / 'data/review/regions-excluded.html'
PAGE_TEMPLATE = ROOT / 'scripts/templates/regions-excluded.html'
# отложенное, к которому автор хочет вернуться (решение автора 2026-10-25); «уже в банке» и повторы — нет
PAGE_STATUSES = ('narrow', 'doubtful', 'ru-options', 'format')
STATUSES = {'add', 'in-bank', 'repeat', 'narrow', 'doubtful', 'ru-options', 'format'}
WITH_REASON = {'narrow', 'doubtful', 'ru-options', 'format'}
# шрифт выгрузок Цифриума отдаёт часть иероглифов дополнительными ключами, их NFKC не сводит
RADICALS = {'⺟': '母', '⻁': '虎', '⻄': '西', '⻅': '见', '⻆': '角', '⻋': '车', '⻓': '长', '⻔': '门',
            '⻘': '青', '⻙': '韦', '⻛': '风', '⻜': '飞', '⻢': '马', '⻣': '骨', '⻩': '黄', '⻬': '齐',
            '⻰': '龙', '⻳': '龟'}
TITLES = {
    'narrow': 'Узкие — отложены до решения автора',
    'doubtful': 'Сомнительные — не публикуются',
    'ru-options': 'Варианты по-русски',
    'format': 'Не подходят по формату',
    'repeat': 'Повторы другого регионального задания',
    'in-bank': 'Уже есть в банке',
}


def load() -> tuple[list[dict], dict[str, dict]]:
    return (json.loads(VARIANTS.read_text('utf-8')), loads_unique(DECISIONS.read_text('utf-8'), 'решениях по региональным заданиям'))


def tasks_by_id(variants: list[dict]) -> dict[str, tuple[dict, dict]]:
    return {task_id(variant, task): (variant, task) for variant in variants for task in variant['tasks']}


def validate(variants: list[dict], decisions: object, bank: list[dict] | None = None) -> list[str]:
    """Ошибки решений; с собранным банком — ещё и ссылок `in-bank` и вливания в старые записи."""
    if not isinstance(decisions, dict):
        return ['решения должны быть словарём id задания → решение']
    errors: list[str] = []
    tasks = tasks_by_id(variants)
    if len(tasks) != sum(len(variant['tasks']) for variant in variants):
        errors.append('в расшифровке повторяются номера заданий одного варианта')
    for missing in sorted(set(tasks) - set(decisions)):
        errors.append(f'{missing}: нет решения')
    for extra in sorted(set(decisions) - set(tasks)):
        errors.append(f'{extra}: решение есть, а задания в расшифровке нет')
    bank_ids = None
    if bank is not None:
        bank_ids = {record['id'] for record in bank} | {i for record in bank for i in record.get('mergedIds', [])}
        # задание `add` с тем же набором вариантов, что у старой записи, сборка молча вливает в неё,
        # а id записи берётся по самому раннему появлению: старый id мог бы смениться (прогресс учеников)
        for record in bank:
            regional = [bool(o.get('regionCode')) for o in record.get('occurrences', [])]
            if any(regional) and not all(regional):
                errors.append(f"{record['id']}: региональное задание влилось в запись банка — "
                              'это пересечение, решение должно быть in-bank')
    for key, item in decisions.items():
        if key not in tasks:
            continue
        if not isinstance(item, dict):
            errors.append(f'{key}: решение должно быть объектом')
            continue
        status = item.get('status')
        if status not in STATUSES:
            errors.append(f'{key}: неизвестный статус {status!r}')
            continue
        if status in WITH_REASON and not str(item.get('reason', '')).strip():
            errors.append(f'{key}: не указана причина')
        if status == 'repeat':
            target = decisions.get(item.get('sameAs')) if isinstance(item.get('sameAs'), str) else None
            if not isinstance(target, dict) or target.get('status') != 'add':
                errors.append(f'{key}: повтор задания {item.get("sameAs")!r}, которое не идёт в банк')
        if status == 'in-bank' and bank_ids is not None and item.get('bankId') not in bank_ids:
            errors.append(f'{key}: в банке нет записи {item.get("bankId")!r}')
        if status == 'add':
            _, task = tasks[key]
            options = task['options']
            if len(options) < 3:
                errors.append(f'{key}: меньше трёх вариантов')
            if any(CYRILLIC.search(option) for option in options):
                errors.append(f'{key}: варианты должны быть по-китайски')
            index = task['officialKeyIndex']
            if index is not None and not 0 <= index < len(options):
                errors.append(f'{key}: ключ указывает на вариант вне списка')
    return errors


def write_report(variants: list[dict], decisions: dict[str, dict]) -> None:
    tasks = tasks_by_id(variants)
    counts = Counter(item['status'] for item in decisions.values())
    lines = ['# Региональные варианты — решения по заданиям', '',
             'Отчёт пишет `python3 scripts/regions.py` и переписывает его целиком; решения — '
             '`data/review/regions.json`.', '',
             f'Вариантов: {len(variants)}, заданий: {len(tasks)}; в банк идут {counts["add"]}.', '']
    for status, title in TITLES.items():
        keys = sorted(key for key, item in decisions.items() if item['status'] == status)
        lines += [f'## {title} ({len(keys)})', '']
        for key in keys:
            variant, task = tasks[key]
            question = task['questionRu'] or task['questionZh']
            answer = (task['options'][task['officialKeyIndex']]
                      if task['officialKeyIndex'] is not None else 'ключа нет')
            item = decisions[key]
            note = item.get('reason') or item.get('bankId') or item.get('sameAs') or ''
            lines.append(f"- `{key}` ({variant['region']}) — {question} | {' / '.join(task['options'])} | "
                         f'ключ: {answer}. {note}')
        lines.append('')
    REPORT.write_text('\n'.join(lines), encoding='utf-8')


def write_page(variants: list[dict], decisions: dict[str, dict]) -> None:
    """Страница отложенных заданий: открывается в браузере без сервера, данные вписаны в неё."""
    rows = []
    # номер задания — числом: «…-2» раньше «…-10»
    order = lambda pair: [int(part) if part.isdigit() else part for part in re.split(r'(\d+)', pair[0])]
    for key, (variant, task) in sorted(tasks_by_id(variants).items(), key=order):
        item = decisions[key]
        if item['status'] not in PAGE_STATUSES:
            continue
        rows.append({'id': key, 's': item['status'], 'r': variant['region'], 'y': variant['year'].replace('-', '/'),
                     'st': variant['stage'], 'n': task['number'], 'q': task['questionRu'] or task['questionZh'],
                     'zh': task['questionZh'] if task['questionRu'] else None, 'o': task['options'],
                     'k': task['officialKeyIndex'], 'why': item.get('reason', '')})
    counts = Counter(row['s'] for row in rows)
    summary = (f"всего {len(rows)}: узких {counts['narrow']}, сомнительных {counts['doubtful']}, "
               f"с вариантами по-русски {counts['ru-options']}, не того формата {counts['format']}.")
    # ни одного «<» внутри <script>: ни «</script>», ни «<!--» не собьют разбор страницы
    data = json.dumps(rows, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')
    page = PAGE_TEMPLATE.read_text('utf-8').replace('__SUMMARY__', summary).replace('__DATA__', data)
    PAGE.write_text(page, encoding='utf-8')


def _squash(text: str) -> str:
    """Текст бланка для сравнения: без пробелов и подчёркиваний, с ключами иероглифов, сведёнными к иероглифам.

    Подчёркивания убираются с обеих сторон: пропуск, набранный в бланке пробелами, в расшифровке
    записан «______».
    """
    text = unicodedata.normalize('NFKC', text)
    text = ''.join(RADICALS.get(char, char) for char in text)
    return re.sub(r'[\s_]+', '', text)


def _real_path(folder: Path, relative: str) -> Path:
    # в реестре путь записан в NFC, а macOS хранит имена файлов в NFD
    current = folder
    for part in relative.split('/'):
        match = [child for child in current.iterdir() if unicodedata.normalize('NFC', child.name) == part]
        if not match:
            raise FileNotFoundError(relative)
        current = match[0]
    return current


def check_sources(variants: list[dict], folder: Path) -> list[str]:
    """Расшифровка против бланков: контрольные суммы файлов и текст каждого задания.

    Задания с `transcribed` переписаны с картинки страницы (текстовый слой PDF испорчен или цифры
    набраны шрифтом без текста), их сверял человек — здесь проверяется только файл.
    """
    errors: list[str] = []
    for variant in variants:
        texts = []
        for origin in variant['origin']:
            try:
                path = _real_path(folder, origin['file'])
            except FileNotFoundError:
                errors.append(f"{variant['id']}: нет файла {origin['file']}")
                continue
            if hashlib.sha256(path.read_bytes()).hexdigest() != origin['sha256']:
                errors.append(f"{variant['id']}: файл {origin['file']} изменился")
            for mode in ([], ['-layout']):
                texts.append(_squash(subprocess.run(['pdftotext', *mode, str(path), '-'],
                                                    capture_output=True, text=True).stdout))
            # в выгрузках Цифриума pdftotext уносит китайский хвост строки («吃在____，玩在苏州”.»)
            # в другое место страницы, а куски в разметке pdftohtml идут по порядку строки
            xml = subprocess.run(['pdftohtml', '-q', '-xml', '-i', '-stdout', str(path)],
                                 capture_output=True, text=True).stdout
            texts.append(_squash(re.sub(r'<[^>]+>', '', xml)))
        text = ''.join(texts)
        for task in variant['tasks']:
            if task.get('transcribed'):
                continue
            pieces = [task['questionZh'] or '', task['questionRu'] or '', *task['options']]
            for piece in pieces:
                # концевой знак, которого нет в бланке, расшифровка добавляет: без него сборка
                # не примет вопрос («Закончи фразу «上有天堂，__________»» → «….»)
                if piece and _squash(piece).rstrip('.?:…') not in text:
                    errors.append(f"{task_id(variant, task)}: в бланке нет «{piece[:40]}»")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--sources', type=Path, help='папка вариантов (03-ВСОШ)')
    args = parser.parse_args()
    variants, decisions = load()
    bank = json.loads((ROOT / 'data/bank.json').read_text('utf-8'))
    errors = validate(variants, decisions, bank)
    if args.sources:
        errors += check_sources(variants, args.sources)
    if errors:
        raise SystemExit('региональные варианты:\n - ' + '\n - '.join(errors))
    write_report(variants, decisions)
    write_page(variants, decisions)
    print(f'региональные варианты: {len(variants)} вариантов, решений {len(decisions)}')


if __name__ == '__main__':
    main()
