"""Отбор очередной партии на проверку и приём её результатов."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRIORITY = {'needs-review': 0, 'conflict': 1, 'unverified': 2}


def select_wave(bank: list[dict], size: int) -> list[dict]:
    """Очередная партия: сначала вопросы без ответа и с расхождением ключей."""
    pending = [record for record in bank if record['answer']['state'] in PRIORITY]
    pending.sort(key=lambda record: (PRIORITY[record['answer']['state']], record['topic'] or '', record['id']))
    return pending[:size]


def apply_results(bank: list[dict], results: list[dict], wave: int) -> tuple[list[dict], list[dict]]:
    """Принять результаты проверки. Ответ без источника или пояснения не принимается."""
    today = dt.date.today().isoformat()
    by_id = {record['id']: record for record in bank}
    mismatches: list[dict] = []

    for result in results:
        record = by_id[result['id']]
        if not result.get('evidence'):
            raise ValueError(f'{result["id"]}: результат без ссылки на источник')
        if not result.get('explanation', '').strip():
            raise ValueError(f'{result["id"]}: результат без пояснения')
        if result['optionId'] not in {option['id'] for option in record['options']}:
            raise ValueError(f'{result["id"]}: ответ указывает на несуществующий вариант {result["optionId"]!r}')

        official = {occurrence['officialKey'] for occurrence in record['occurrences']
                    if occurrence.get('officialKey')}

        record['explanation'] = {'ru': result['explanation'].strip()}
        record['evidence'] = [{'title': item['title'], 'url': item['url'], 'checkedAt': today}
                              for item in result['evidence']]
        record['wave'] = wave

        if official and result['optionId'] not in official:
            # расхождение с официальным ключом не решается молча: вопрос уходит на сверку
            record['answer'] = {'optionId': None, 'state': 'conflict'}
            mismatches.append({
                'id': record['id'],
                'questionRu': record['questionRu'],
                'official': sorted(_text(record, key) for key in official),
                'found': _text(record, result['optionId']),
                'note': result.get('note', ''),
            })
        else:
            record['answer'] = {'optionId': result['optionId'], 'state': 'verified'}

    return bank, mismatches


def _text(record: dict, option_id: str) -> str:
    for option in record['options']:
        if option['id'] == option_id:
            return option['zh']
    return option_id


def write_report(wave: int, done: list[dict], mismatches: list[dict]) -> None:
    lines = [f'# Волна проверки {wave}', '',
             f'Проверено вопросов: {len(done)}',
             f'Расхождений с официальным ключом: {len(mismatches)}', '',
             '## Расхождения', '']
    lines += [f"- `{item['id']}` — {item['questionRu']}\n"
              f"  официальный ключ: {', '.join(item['official'])}; источники дают: {item['found']}."
              f"{' ' + item['note'] if item['note'] else ''}"
              for item in mismatches] or ['- нет']
    (ROOT / f'data/review/wave-{wave}.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--wave', type=int, required=True)
    parser.add_argument('--size', type=int, default=50)
    parser.add_argument('--results', type=Path, help='JSON с результатами проверки')
    args = parser.parse_args()

    bank = json.loads((ROOT / 'data/bank.json').read_text('utf-8'))
    if args.results is None:
        batch = select_wave(bank, args.size)
        print(json.dumps([{'id': r['id'], 'topic': r['topic'], 'questionRu': r['questionRu'],
                           'questionZh': r['questionZh'], 'options': r['options'],
                           'answer': r['answer'], 'occurrences': r['occurrences']}
                          for r in batch], ensure_ascii=False, indent=2))
        return

    results = json.loads(args.results.read_text('utf-8'))
    bank, mismatches = apply_results(bank, results, args.wave)
    (ROOT / 'data/bank.json').write_text(
        json.dumps(bank, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    write_report(args.wave, results, mismatches)
    print(f'волна {args.wave}: принято {len(results)}, расхождений {len(mismatches)}')


if __name__ == '__main__':
    main()
