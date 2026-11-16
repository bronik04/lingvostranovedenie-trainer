"""Материалы для чтения после ответа; не меняют банк и источники проверки ключа."""

from urllib.parse import urlsplit


def article_link(value):
    if not isinstance(value, dict) or not isinstance(value.get('title'), str) or not value['title'].strip():
        return None
    try:
        url = value.get('url', '')
        parsed = urlsplit(url)
        if (parsed.scheme not in {'https', 'http'} or not parsed.hostname
                or parsed.username or parsed.password
                or parsed.path in {'', '/'}
                or parsed.path.lower().endswith(('.pdf', '.doc', '.docx'))):
            return None
    except (ValueError, TypeError, AttributeError):
        return None
    return {'title': value['title'].strip(), 'url': url}


def validate_catalog(catalog):
    if not isinstance(catalog, dict):
        return ['материалы для чтения: ожидается объект']
    errors = []
    for section, entries in catalog.items():
        if section not in {'rows', 'questions'} or not isinstance(entries, dict):
            errors.append(f'материалы для чтения: неизвестный раздел или неверный формат {section}')
            continue
        for key, value in entries.items():
            if not isinstance(key, str) or not key.strip() or not article_link(value):
                errors.append(f'материалы для чтения: некорректная статья {section}/{key}')
    return errors


def evidence_priority(source):
    host = urlsplit(source['url']).hostname or ''
    if host == 'ru.wikipedia.org':
        return 0
    if host.endswith('.ru') or '/ru/' in urlsplit(source['url']).path:
        return 1
    return 2


def reading_links(bank, catalog):
    """Одна-две статьи по теме. Явный выбор → строка досье → имеющийся источник.

    Каталог содержит проверенные прямые ссылки, а не поисковые запросы. Новые вопросы
    без записи получают подходящий источник; страница и сборка не обращаются к сети.
    """
    result = {}
    for record in bank:
        explicit = catalog.get('questions', {}).get(record['id'])
        refs = record.get('factRow', [])
        if isinstance(refs, str):
            refs = [refs]
        candidates = [explicit] if explicit else [catalog.get('rows', {}).get(ref) for ref in refs]
        links = [link for candidate in candidates if (link := article_link(candidate))]
        if not links:
            evidence = [link for source in record.get('evidence', []) if (link := article_link(source))]
            links = sorted(evidence, key=evidence_priority)[:1]
        unique = {link['url']: link for link in links}
        if unique:
            result[record['id']] = list(unique.values())[:2]
    return result
