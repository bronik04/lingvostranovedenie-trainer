"""Слияние сырых записей в канонический банк."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from normalize import (completeness_errors, fragment_pairs, language_errors, normalize_text,
                       option_key, tidy)
from authored import load_authored, validate_authored
from editorial import apply_editorial, load_editorial
from explanations import apply_revisions, load_revisions
from glosses import apply_glosses, load_glosses

STAGE_ORDER = {'pri': 0, 'shk': 1, 'mun': 2, 'reg': 3, 'zak': 4}


def record_id(occurrence: dict) -> str:
    """Идентификатор по самому раннему появлению вопроса.

    Номер задания известен не всегда: в банке 423 нумерация сквозная по темам
    документа, а не по олимпиадному бланку. Там, где номера нет, вместо него идёт
    короткий отпечаток текста вопроса — он так же устойчив и не зависит от темы.
    """
    if occurrence.get('number') is not None:
        return f"{occurrence['year']}-{occurrence['stageCode']}-{occurrence['number']}"
    fingerprint = hashlib.sha1(occurrence.get('fingerprint', '').encode('utf-8')).hexdigest()[:6]
    return f"{occurrence['year']}-{occurrence['stageCode']}-q{fingerprint}"


def _authority(source_file: str) -> int:
    if source_file.endswith('.pdf'):
        return 3
    for prefix, weight in (('Банк вопросов', 2), ('Вопросы по категориям', 1)):
        if source_file.startswith(prefix):
            return weight
    return 0


def _is_whole(text: str) -> bool:
    return not completeness_errors(text, None, [])


def _best_wording(candidates: list[tuple[int, str]]) -> str:
    """Полная редакция важнее авторитетной.

    Обрезка встречается в любом источнике, включая первоисточник: в банке 423 у вопроса
    про Цзянсу отрезано «Китая.», а из бланка 2024-25 при извлечении текста выпала
    середина вопроса про развитые регионы. Поэтому порядок такой: сначала целость,
    затем длина и только потом авторитет источника.
    """
    return max(candidates, key=lambda pair: (_is_whole(pair[1]), len(pair[1]), pair[0]))[1]


def _forms(member: dict, translations: dict[str, str]) -> set[tuple[str, str]]:
    """Нормализованные формы вопроса: китайская, русская и перевод китайской.

    Один и тот же вопрос в разных источниках записан то по-китайски, то по-русски,
    поэтому сравнивать надо все доступные формы, а не одну.
    """
    forms: set[tuple[str, str]] = set()
    chinese = normalize_text(member['questionZh'] or '')
    russian = normalize_text(member['questionRu'] or '')
    if chinese:
        forms.add(('zh', chinese))
        translated = translations.get(chinese)
        if translated:
            forms.add(('ru', normalize_text(translated)))
    if russian:
        forms.add(('ru', russian))
    return forms


def _is_subsequence(short: str, long: str) -> bool:
    iterator = iter(long)
    return all(symbol in iterator for symbol in short)


def _same_wording(first: str, second: str) -> bool:
    """Одна и та же формулировка, возможно урезанная одним из источников.

    Урезать может не только хвост: в бланке 2024-25 из вопроса «Какие регионы Китая
    наиболее развиты в социально-экономическом отношении?» выпала середина, и остались
    «Какие регионы» плюс «экономическом отношении?». Поэтому короткий текст считается
    тем же вопросом, если он целиком укладывается в длинный по порядку символов и при
    этом занимает не меньше половины его длины.
    """
    if first == second or first.startswith(second) or second.startswith(first):
        return True
    if first.endswith(second) or second.endswith(first):
        return True
    short, long = sorted((first, second), key=len)
    return len(short) >= len(long) / 2 and _is_subsequence(short, long)


def _same_question(left: set[tuple[str, str]], right: set[tuple[str, str]]) -> bool:
    """Тот же вопрос, если совпала любая форма — с поправкой на обрезку."""
    for language, first in left:
        for other_language, second in right:
            if language != other_language or not first or not second:
                continue
            if _same_wording(first, second):
                return True
    return False


def _split_by_question(members: list[dict], translations: dict[str, str]) -> list[list[dict]]:
    """Разбить записи с одним набором вариантов по разным вопросам.

    Один набор вариантов обслуживает несколько разных заданий: четыре классических
    романа предлагают и в вопросе про Сунь Укуна, и в вопросе про У Суна, и ответы там
    разные. Без этого разбиения такие задания слиплись бы в одно с конфликтом ключей.
    """
    buckets: list[tuple[set[tuple[str, str]], list[dict]]] = []
    for member in members:
        forms = _forms(member, translations)
        for bucket_forms, bucket in buckets:
            if _same_question(forms, bucket_forms):
                bucket.append(member)
                bucket_forms |= forms
                break
        else:
            buckets.append((set(forms), [member]))
    return [bucket for _, bucket in buckets]


def _group(raw: list[dict], translations: dict[str, str]) -> dict[tuple, list[dict]]:
    """Дедупликация в два прохода.

    Первый — по набору непустых вариантов и тексту вопроса. Второй присоединяет запись
    с испорченным списком вариантов к полной: у вопроса про восемь кухонь в банке 423
    нет варианта D, а в сводном сборнике он есть, и иначе вопрос разъехался бы надвое.

    Второй проход срабатывает только тогда, когда набор вариантов одной записи целиком
    входит в набор другой. Совпадения одного лишь текста недостаточно: вопрос «какое
    произведение не относится к четырём классическим романам» давали в разные годы с
    разными наборами вариантов и разными ответами — это разные задания.
    """
    by_options: dict[tuple[str, ...], list[dict]] = {}
    for record in raw:
        key = option_key([option for option in record['options'] if option.strip()])
        by_options.setdefault(key, []).append(record)

    groups: dict[tuple, list[dict]] = {}
    forms: dict[tuple, set[tuple[str, str]]] = {}
    for options, members in sorted(by_options.items()):
        for bucket in _split_by_question(members, translations):
            bucket_forms: set[tuple[str, str]] = set()
            for member in bucket:
                bucket_forms |= _forms(member, translations)
            label = min((text for language, text in bucket_forms if language == 'zh'), default='')
            label = label or min((text for _, text in bucket_forms), default='')
            groups[(options, label)] = bucket
            forms[(options, label)] = bucket_forms

    keys = sorted(groups, key=lambda key: (-len(key[0]), key))
    parent = {key: key for key in keys}
    for small in keys:
        for big in keys:
            if len(big[0]) <= len(small[0]) or not set(small[0]) <= set(big[0]):
                continue
            if _same_question(forms[small], forms[big]):
                parent[small] = big
                break

    merged: dict[tuple, list[dict]] = {}
    for key in keys:
        anchor = key
        while parent[anchor] != anchor:
            anchor = parent[anchor]
        merged.setdefault(anchor, []).extend(groups[key])
    return merged


def _options_rank(record: dict, keys: set[str]) -> tuple[int, int, int]:
    """Набор вариантов выбирается так, чтобы в нём был официальный ключ.

    Источники расходятся по вариантам одного вопроса: например, у вопроса про четыре
    классических романа в одной редакции среди вариантов есть «骆驼祥子», в другой нет.
    Если взять набор без ключа, ответ окажется недостижим. Поэтому сначала смотрим,
    вмещает ли набор все известные ключи, затем полноту, затем авторитет источника.
    """
    texts = {normalize_text(option) for option in record['options']}
    hosts_keys = 1 if keys <= texts else 0
    filled = sum(1 for option in record['options'] if option.strip())
    return hosts_keys, filled, _authority(record['sourceFile'])


def merge(raw: list[dict], translations: dict[str, str],
          verification: dict[str, dict] | None = None) -> tuple[list[dict], dict]:
    """Собрать банк. `verification` — результаты волн проверки, они переживают пересборку."""
    verification = verification or {}
    groups = _group(raw, translations)

    bank: list[dict] = []
    report: dict[str, list] = {'conflicts': [], 'untranslated': [], 'dropped': [], 'merged': []}

    for key, members in sorted(groups.items()):
        # порядок чтения файлов не должен влиять на результат: всё, что дальше выбирает
        # «лучшего» кандидата, обязано получать участников в устойчивом порядке
        members = sorted(members, key=lambda m: (
            m['sourceFile'], m['year'], STAGE_ORDER.get(m['stageCode'], 9),
            m['number'] if m['number'] is not None else -1,
            m['sourceOrdinal'] if m['sourceOrdinal'] is not None else -1))
        # появление — это выход вопроса на конкретном этапе конкретного года, а не строка
        # в файле: один и тот же вопрос лежит сразу в нескольких источниках, и без
        # схлопывания «2023-24, муниципальный» повторилось бы четыре раза подряд
        appearances: dict[tuple[str, str, int | None], dict] = {}
        for member in members:
            spot = (member['year'], member['stageCode'], member['number'])
            entry = appearances.setdefault(spot, {
                'year': member['year'], 'stage': member['stage'], 'stageCode': member['stageCode'],
                'grades': member['grades'], 'number': member['number'],
                'officialKey': None, 'sourceFiles': [],
            })
            entry['sourceFiles'].append(member['sourceFile'])
            entry['grades'] = entry['grades'] or member['grades']
            if entry['officialKey'] is None and member['officialKeyIndex'] is not None:
                entry['officialKey'] = normalize_text(member['options'][member['officialKeyIndex']])

        # запись из банка 423 не знает номера задания; если для того же года и этапа
        # номер известен из бланка или сборника, это одно и то же появление
        for spot in [spot for spot in appearances if spot[2] is None]:
            numbered = [other for other in appearances
                        if other[0] == spot[0] and other[1] == spot[1] and other[2] is not None]
            if len(numbered) != 1:
                continue
            nameless = appearances.pop(spot)
            target = appearances[numbered[0]]
            target['sourceFiles'] += nameless['sourceFiles']
            target['grades'] = target['grades'] or nameless['grades']
            target['officialKey'] = target['officialKey'] or nameless['officialKey']

        for entry in appearances.values():
            entry['sourceFiles'] = sorted(set(entry['sourceFiles']))
        occurrences = sorted(appearances.values(),
                             key=lambda o: (o['year'], STAGE_ORDER.get(o['stageCode'], 9),
                                            o['number'] if o['number'] is not None else 10_000))

        russian = [(_authority(m['sourceFile']), m['questionRu']) for m in members if m['questionRu']]
        chinese = [(_authority(m['sourceFile']), m['questionZh']) for m in members if m['questionZh']]
        question_zh = tidy(_best_wording(chinese)) if chinese else None

        if russian:
            question_ru = tidy(_best_wording(russian))
        elif question_zh and normalize_text(question_zh) in translations:
            question_ru = translations[normalize_text(question_zh)]
        else:
            report['untranslated'].append({'questionZh': question_zh, 'options': members[0]['options']})
            continue

        bank_id = record_id(dict(occurrences[0], fingerprint=key[1] or normalize_text(question_ru)))
        keys = {entry['officialKey'] for entry in occurrences if entry['officialKey']}

        options_source = max(members, key=lambda m: _options_rank(m, keys))
        options = [{'id': f'o{index + 1}', 'zh': text} for index, text in enumerate(options_source['options'])]
        by_text = {normalize_text(option['zh']): option['id'] for option in options}

        # ключ хранится как идентификатор варианта: в разных источниках варианты одного
        # вопроса стоят в разном порядке, поэтому буква или номер позиции ненадёжны
        for entry in occurrences:
            entry['officialKey'] = by_text.get(entry['officialKey']) if entry['officialKey'] else None

        unknown = [key for key in keys if key not in by_text]
        if unknown:
            answer = {'optionId': None, 'state': 'needs-review'}
            report['dropped'].append({'id': bank_id,
                                      'errors': [f'ключ указывает на вариант вне списка: {unknown}'],
                                      'questionRu': question_ru})
        elif len(keys) > 1:
            answer = {'optionId': None, 'state': 'conflict'}
            report['conflicts'].append({'id': bank_id, 'variants': sorted(keys)})
        elif keys:
            answer = {'optionId': by_text[keys.pop()], 'state': 'unverified'}
        else:
            answer = {'optionId': None, 'state': 'needs-review'}

        topics = sorted({m['topic'] for m in members if m['topic']})
        errors = language_errors(question_ru, [option['zh'] for option in options])
        errors += completeness_errors(question_ru, question_zh, [option['zh'] for option in options])
        if errors:
            report['dropped'].append({'id': bank_id, 'errors': errors, 'questionRu': question_ru})
            continue

        if len(members) > 1:
            report['merged'].append({'id': bank_id, 'count': len(members)})

        bank.append({
            'id': bank_id,
            'topic': topics[0] if topics else None,
            'topicSource': 'categories-310' if topics else 'assigned',
            'questionRu': question_ru,
            'questionZh': question_zh,
            'options': options,
            'occurrences': occurrences,
            'answer': answer,
            'explanation': {'ru': ''},
            'evidence': [],
            'wave': 0,
            'parseWarnings': sorted({w for m in members for w in m['parseWarnings']}),
        })

    # идентификаторы обязаны быть уникальными: один и тот же номер задания могут
    # носить разные вопросы одного бланка, если номер известен не для всех источников
    seen: dict[str, int] = {}
    for record in bank:
        base = record['id']
        if base in seen:
            seen[base] += 1
            record['id'] = f"{base}-{'abcdefghij'[seen[base] - 1]}"
        else:
            seen[base] = 0

    # проверка волн применяется только теперь, когда id уже окончательные: если сделать
    # это раньше, запись, попавшая в коллизию и получившая суффикс -a/-b, не найдёт себя
    # в verification (он ключуется по итоговому id) и молча останется непроверенной
    for record in bank:
        verified = verification.get(record['id'])
        if not verified:
            continue
        official = {entry['officialKey'] for entry in record['occurrences'] if entry['officialKey']}
        if official and verified['optionId'] not in official and not verified.get('overrideOfficialKey'):
            record['answer'] = {'optionId': None, 'state': 'conflict'}
        else:
            record['answer'] = {'optionId': verified['optionId'], 'state': 'verified'}
        record['explanation'] = {'ru': verified['explanation']}
        record['evidence'] = verified['evidence']
        record['wave'] = verified['wave']

    bank.sort(key=lambda record: record['id'])
    report['fragments'] = fragment_pairs([(r['id'], r['questionRu']) for r in bank])
    return bank, report


def _write_report(report: dict, bank: list[dict]) -> None:
    lines = ['# Отчёт о слиянии', '',
             f'Записей в банке: {len(bank)}',
             f'Склеено дублей: {len(report["merged"])}',
             f'Конфликтов ключей: {len(report["conflicts"])}',
             f'Без русского текста: {len(report["untranslated"])}',
             f'Отброшено по инвариантам: {len(report["dropped"])}',
             f'Подозрения на обрезку: {len(report["fragments"])}', '']
    for title, key in (('Конфликты ключей', 'conflicts'), ('Без перевода', 'untranslated'),
                       ('Отброшенные записи', 'dropped')):
        lines += [f'## {title}', '']
        lines += [f'- `{json.dumps(item, ensure_ascii=False)}`' for item in report[key]] or ['- пусто']
        lines.append('')
    if report['fragments']:
        lines += ['## Пары «вопрос — обрезок вопроса»', '']
        lines += [f'- `{left}` ↔ `{right}`' for left, right in report['fragments']]
    (ROOT / 'data/review/merge.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main() -> None:
    raw: list[dict] = []
    for path in sorted((ROOT / 'data/raw').glob('*.json')):
        if path.name == 'index.json':
            continue
        raw.extend(json.loads(path.read_text('utf-8')))
    translations = json.loads((ROOT / 'data/translations.json').read_text('utf-8'))
    verification_file = ROOT / 'data/verification.json'
    verification = json.loads(verification_file.read_text('utf-8')) if verification_file.exists() else {}
    bank, report = merge(raw, translations, verification)
    revisions = load_revisions(ROOT / 'data/review/explanation-wave-1.json', bank)
    bank = apply_revisions(bank, revisions)
    bank.extend(load_authored(ROOT / 'data/authored/questions.json', bank))
    # правки — последним слоем, чтобы доходить и до дополнений
    bank = apply_editorial(bank, load_editorial(ROOT / 'data/review/editorial.json'))
    # дополнения после правок проверяются здесь же, чтобы не записать банк,
    # который сборка потом отвергнет
    errors = validate_authored([r for r in bank if r.get('origin') == 'addition'],
                               [r for r in bank if r.get('origin') is None])
    if errors:
        raise ValueError('дополнения после правок некорректны:\n - ' + '\n - '.join(errors))
    # подписи к неверным вариантам — самым последним слоем: они сверяются с
    # текстом варианта уже после всех правок
    bank = apply_glosses(bank, load_glosses(ROOT / 'data/review/glosses.json'))
    bank.sort(key=lambda record: record['id'])
    report['fragments'] = fragment_pairs([(record['id'], record['questionRu']) for record in bank])
    (ROOT / 'data/bank.json').write_text(
        json.dumps(bank, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    (ROOT / 'data/review').mkdir(parents=True, exist_ok=True)
    _write_report(report, bank)
    checked = sum(1 for record in bank if record['answer']['state'] == 'verified')
    print(f'банк: {len(bank)} записей, проверено {checked}; отчёт: data/review/merge.md')


if __name__ == '__main__':
    main()
