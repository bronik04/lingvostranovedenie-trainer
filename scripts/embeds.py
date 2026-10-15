"""Встраивание олимпиадного вопроса в досье.

Вопрос досье с полем `embeds` не создаёт новую запись: олимпиадная запись остаётся собой (id,
формулировка, появления, исходные варианты и их id — на них держится прогресс учеников), но
получает общий набор неверных вариантов из той же колонки таблицы и подписи ко всем неверным
вариантам — из ячеек таблицы. Слой идёт после склеек и удалений (`embeds` — итоговый id) и до
`glosses.json`. Спецификация — docs/superpowers/specs/2026-10-15-dossiers-myths-space-design.md.
"""

from __future__ import annotations

from dossiers import question_options


def _column_glosses(question: dict, dossier: dict) -> dict[str, str]:
    """Подпись каждой ячейки спрашиваемой колонки таблицы — по тексту ячейки."""
    fact = question['fact']
    glosses: dict[str, str] = {}
    for row in dossier['tables'][fact['table']]['rows']:
        cell = row.get(fact['ask'])
        if isinstance(cell, dict) and cell.get('gloss'):
            glosses.setdefault(cell['zh'].strip(), cell['gloss'].strip())
    return glosses


def apply_embeds(bank: list[dict], loaded: list[tuple[dict, list[dict]]],
                 glosses: dict[str, dict]) -> list[dict]:
    by_id = {record['id']: record for record in bank}
    merged_into = {old: record['id'] for record in bank for old in record.get('mergedIds', [])}
    errors: list[str] = []
    embedded_by: dict[str, str] = {}
    updates: dict[str, dict] = {}
    for dossier, questions in loaded:
        for question in questions:
            if 'embeds' not in question or question['status'] != 'accepted':
                continue
            where = f'{dossier["id"]}/{question["id"]}'
            target = question['embeds']
            record = by_id.get(target)
            if record is None:
                hint = f' — влита в {merged_into[target]}' if target in merged_into else ''
                errors.append(f'{where}: в банке нет записи {target}{hint}')
                continue
            if target in embedded_by:
                errors.append(f'{where}: запись {target} уже встроена вопросом {embedded_by[target]}')
                continue
            embedded_by[target] = where
            if 'dossier' in record:
                errors.append(f'{where}: {target} — вопрос досье, его не встраивают')
                continue
            if target in glosses:
                errors.append(f'{where}: у {target} есть подписи в glosses.json — перенесите их в ячейки таблицы')
                continue
            table_options, _ = question_options(question, dossier)
            answer = next(option for option in record['options'] if option['id'] == record['answer']['optionId'])
            if answer['zh'].strip() != table_options[0]['zh']:
                errors.append(f'{where}: ответ {target} ({answer["zh"]}) не совпадает с ячейкой '
                              f'({table_options[0]["zh"]})')
                continue
            cell_glosses = _column_glosses(question, dossier)
            options: list[dict] = []
            for option in record['options']:
                option = {key: value for key, value in option.items() if key != 'gloss'}
                if option['id'] != answer['id']:
                    gloss = cell_glosses.get(option['zh'].strip())
                    if gloss is None:
                        errors.append(f'{where}: для варианта {option["zh"].strip()} нет ячейки с подписью в таблице')
                    else:
                        option['gloss'] = gloss
                options.append(option)
            texts = {option['zh'].strip() for option in options}
            for added in table_options[1:]:
                if added['zh'] not in texts:
                    options.append(added)
                    texts.add(added['zh'])
            explanation = record.get('explanation', {}).get('ru', '')
            named = [option['zh'].strip() for option in options
                     if option['id'] != answer['id'] and option['zh'].strip() in explanation]
            if named:
                errors.append(f'{where}: пояснение {target} называет неверные варианты {named} — '
                              'на экране их может не оказаться; правка в editorial.json')
            updates[target] = {**record, 'options': options, 'dossier': dossier['id']}
    if errors:
        raise ValueError('некорректные встраивания:\n - ' + '\n - '.join(errors))
    return [updates.get(record['id'], record) for record in bank]
