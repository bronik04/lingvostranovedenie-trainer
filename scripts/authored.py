"""Проверка и загрузка дополнений к олимпиадной базе."""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse

from normalize import completeness_errors, language_errors, normalize_text
from taxonomy import TOPICS

SENTENCE = re.compile(r'[^.!?]+[.!?]')


def sentence_count(text: str) -> int:
    return len(SENTENCE.findall(text))


def evidence_errors(evidence: object) -> list[str]:
    if not isinstance(evidence, list) or not evidence:
        return ['нет официального источника']

    errors: list[str] = []
    for index, item in enumerate(evidence, start=1):
        if not isinstance(item, dict):
            errors.append(f'источник {index} имеет неверный формат')
            continue
        parsed = urlparse(item.get('url', ''))
        if parsed.scheme not in {'http', 'https'} or not parsed.netloc:
            errors.append(f'источник {index} имеет небезопасную ссылку')
        if not isinstance(item.get('title'), str) or not item['title'].strip():
            errors.append(f'у источника {index} нет названия')
        if not isinstance(item.get('checkedAt'), str) or not item['checkedAt'].strip():
            errors.append(f'у источника {index} нет даты проверки')
        if item.get('authority') != 'official':
            errors.append(f'источник {index} не помечен официальным')
    return errors


def validate_authored(records: list[dict], olympiad_bank: list[dict]) -> list[str]:
    errors: list[str] = []
    known_ids = {record['id'] for record in olympiad_bank}
    known_questions = {normalize_text(record['questionRu']) for record in olympiad_bank}
    seen_ids: set[str] = set()
    seen_questions: set[str] = set()

    for index, record in enumerate(records, start=1):
        where = record.get('id', f'запись {index}') if isinstance(record, dict) else f'запись {index}'
        if not isinstance(record, dict):
            errors.append(f'{where}: запись должна быть объектом')
            continue

        if not isinstance(record.get('id'), str) or not record['id'].strip():
            errors.append(f'{where}: нет id')
        elif record['id'] in known_ids or record['id'] in seen_ids:
            errors.append(f'{where}: повторяющийся id')
        seen_ids.add(record.get('id', ''))

        if record.get('origin') != 'addition':
            errors.append(f'{where}: origin должен быть addition')
        if record.get('topic') not in TOPICS:
            errors.append(f'{where}: тема вне списка семи категорий')

        question = record.get('questionRu')
        if not isinstance(question, str):
            errors.append(f'{where}: вопрос должен быть строкой')
            question = ''
        options = record.get('options')
        if not isinstance(options, list) or len(options) != 4:
            errors.append(f'{where}: нужно ровно четыре варианта')
            option_ids: set[str] = set()
            option_texts: list[str] = []
        else:
            option_ids = {option.get('id') for option in options if isinstance(option, dict)}
            option_texts = [option.get('zh', '') if isinstance(option, dict) else '' for option in options]
            if len(option_ids) != 4 or any(not isinstance(option_id, str) or not option_id for option_id in option_ids):
                errors.append(f'{where}: варианты должны иметь уникальные id')
            errors.extend(f'{where}: {message}' for message in language_errors(question, option_texts))
            errors.extend(f'{where}: {message}' for message in completeness_errors(
                question, record.get('questionZh'), option_texts))

        answer = record.get('answer')
        if not isinstance(answer, dict) or answer.get('state') != 'verified':
            errors.append(f'{where}: ответ должен иметь статус verified')
        elif answer.get('optionId') not in option_ids:
            errors.append(f'{where}: ответ указывает на несуществующий вариант')

        explanation = record.get('explanation', {})
        explanation_text = explanation.get('ru', '') if isinstance(explanation, dict) else ''
        if not isinstance(explanation_text, str) or not explanation_text.strip():
            errors.append(f'{where}: нет пояснения')
        elif not 3 <= sentence_count(explanation_text) <= 5:
            errors.append(f'{where}: пояснение должно состоять из 3–5 предложений')
        errors.extend(f'{where}: {message}' for message in evidence_errors(record.get('evidence')))

        normalized_question = normalize_text(question)
        if normalized_question in known_questions or normalized_question in seen_questions:
            errors.append(f'{where}: формулировка уже есть в базе')
        known_questions.add(normalized_question)
        seen_questions.add(normalized_question)

        derived_from = record.get('derivedFrom')
        if derived_from is not None:
            if derived_from not in known_ids:
                errors.append(f'{where}: derivedFrom указывает на неизвестный олимпиадный вопрос')
            elif normalized_question == normalize_text(next(
                    item['questionRu'] for item in olympiad_bank if item['id'] == derived_from)):
                errors.append(f'{where}: обратный вопрос повторяет исходную формулировку')

    return errors


def load_authored(path: Path, olympiad_bank: list[dict]) -> list[dict]:
    records = json.loads(path.read_text('utf-8'))
    if not isinstance(records, list):
        raise ValueError('дополнения должны быть списком')
    errors = validate_authored(records, olympiad_bank)
    if errors:
        raise ValueError('некорректные дополнения:\n - ' + '\n - '.join(errors))
    return [{**record, 'occurrences': record.get('occurrences', []),
             'parseWarnings': record.get('parseWarnings', []),
             'topicSource': record.get('topicSource', 'authored')}
            for record in records]
