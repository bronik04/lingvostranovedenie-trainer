"""Рубрикация банка по семи категориям."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

TOPICS = [
    'География и административное устройство',
    'Россия и межкультурный блок',
    'Литература, язык, искусство и философия',
    'История и государство',
    'Общество: население, этносы и религии',
    'Экономика, образование, наука и спорт',
    'Культура, традиции и праздники',
]


def _score(text: str, keywords: list[str]) -> int:
    lowered = text.lower()
    return sum(1 for keyword in keywords if keyword.lower() in lowered)


def assign_topics(bank: list[dict], rules: dict) -> tuple[list[dict], list[dict]]:
    disputed: list[dict] = []
    for record in bank:
        if record.get('topic') and record.get('topicSource') in {'categories-310', 'authored', 'editorial'}:
            continue
        haystack = ' '.join([record['questionRu'], record.get('questionZh') or '']
                            + [option['zh'] for option in record['options']])
        scores = {topic: _score(haystack, keywords) for topic, keywords in rules['topics'].items()}
        best = max(scores, key=lambda topic: (scores[topic], -TOPICS.index(topic)))
        record['topic'] = best if scores[best] else rules['default']
        record['topicSource'] = 'assigned'
        disputed.append({'id': record['id'], 'topic': record['topic'],
                         'questionRu': record['questionRu'], 'confident': bool(scores[best])})
    return bank, disputed


def main() -> None:
    bank = json.loads((ROOT / 'data/bank.json').read_text('utf-8'))
    rules = json.loads((ROOT / 'data/taxonomy.json').read_text('utf-8'))
    bank, disputed = assign_topics(bank, rules)
    (ROOT / 'data/bank.json').write_text(
        json.dumps(bank, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')

    lines = ['# Рубрикация — метки, проставленные автоматически', '',
             f'Всего проставлено: {len(disputed)}', '',
             '| id | тема | уверенно | вопрос |', '|---|---|---|---|']
    lines += [f"| `{item['id']}` | {item['topic']} | {'да' if item['confident'] else 'нет'} | {item['questionRu'][:80]} |"
              for item in disputed]
    (ROOT / 'data/review/taxonomy.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'проставлено тем: {len(disputed)}; отчёт: data/review/taxonomy.md')


if __name__ == '__main__':
    main()
