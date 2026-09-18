"""Нормализация текста и инварианты банка вопросов."""

from __future__ import annotations

import re
import unicodedata

CYRILLIC = re.compile(r'[А-Яа-яЁё]')
CJK = re.compile(r'[一-鿿]')
OPTION_LABEL = re.compile(r'^\s*[A-DА-Г]\s*[.、．)）]\s*')
TERMINALS = ('?', '？', '.', '。', '!', '！', '…', ':', '：')
# вопрос-заполнялка законно начинается с многоточия или кавычки:
# «… — важнейшая продовольственная культура Китая», «„Четверокнижие“ включает …»
OPENERS = ('…', '«', '"', '„', '“', '(', '（', '‹')
# самый короткий законный вопрос в источниках — «Как называется гимн КНР?» (24 символа)
MIN_QUESTION_LENGTH = 15

# к вариантам ответа в источниках прилипает текст колонтитулов и соседних разделов:
# «普希金美术馆 Максимальное количество баллов за задание…», «瓷都ПИСЬМО写作(…)»
ARTIFACTS = re.compile(
    r'\s*(?:'
    r'(?:Пригласительный|Школьный|Муниципальный|Региональный|Заключительный)\s+(?:\S+\s+)?этап'
    r'|Максимальн\w+|Максимум'
    r'|\*?\s*Данное\s+задание'
    r'|Примечание'
    r'|Всероссийская\s+олимпиада'
    r'|ПИСЬМО|АУДИРОВАНИЕ|ЧТЕНИЕ|ЛЕКСИКА|ГРАММАТИКА|ГОВОРЕНИЕ|ПИСЬМЕННАЯ'
    r'|写作|听力|阅读|口语'
    r')[\s\S]*$'
)


# перенос по слогам оставляет в тексте дефис с пробелом: «социально- экономическом»
HYPHEN_BREAK = re.compile(r'(?<=[а-яёa-z])-\s+(?=[а-яёa-z])')


def tidy(value: str) -> str:
    """Убрать следы переноса строк из формулировки."""
    return HYPHEN_BREAK.sub('-', value).strip()


def strip_artifacts(value: str) -> str:
    """Убрать из варианта ответа приклеившийся текст колонтитула или соседнего раздела."""
    return ARTIFACTS.sub('', value).strip(' ;·')


def normalize_text(value: str) -> str:
    """Свести строку к виду, пригодному для сравнения: без меток, пробелов и концевых знаков."""
    text = unicodedata.normalize('NFKC', value)
    text = OPTION_LABEL.sub('', text)
    text = re.sub(r'\s+', '', text)
    return text.strip('。？?！!.,，、；;： :…')


def option_key(options: list[str]) -> tuple[str, ...]:
    """Ключ дедупликации: набор вариантов без учёта порядка и буквенных меток."""
    return tuple(sorted(normalize_text(option) for option in options))


def language_errors(question_ru: str, options: list[str]) -> list[str]:
    """Вопрос по-русски, варианты по-китайски.

    Китайские вкрапления внутри русского вопроса законны и встречаются в самих
    бланках: «Какой из городов называют 泉城?», «не относится к 4 классическим романам
    (四大名著)», «обучение в неполной средней школе (初中)». Убрать их — значит испортить
    вопрос, поэтому проверяется не отсутствие иероглифов, а наличие русского текста:
    целиком китайская формулировка в поле вопроса — ошибка.
    """
    errors: list[str] = []
    if not CYRILLIC.search(question_ru):
        errors.append('вопрос показывается не по-русски')
    for option in options:
        if CYRILLIC.search(option):
            errors.append(f'кириллица в варианте ответа: {option!r}')
    return errors


def completeness_errors(question_ru: str, question_zh: str | None, options: list[str]) -> list[str]:
    errors: list[str] = []
    if question_ru != question_ru.strip():
        errors.append('вопрос начинается или заканчивается пробелом')
    text = question_ru.strip()
    if len(text) < MIN_QUESTION_LENGTH:
        errors.append(f'вопрос короче {MIN_QUESTION_LENGTH} символов: {text!r}')
    if text and not (text[0].isupper() or text[0].isdigit() or text.startswith(OPENERS)):
        errors.append(f'вопрос начинается не с заглавной буквы: {text[:30]!r}')
    if not text.endswith(TERMINALS):
        errors.append(f'вопрос обрывается без знака препинания: {text[-30:]!r}')
    if question_zh is not None and len(normalize_text(question_zh)) < 4:
        errors.append(f'китайская формулировка слишком коротка: {question_zh!r}')
    for option in options:
        if len(option.strip()) < 1:
            errors.append('пустой вариант ответа')
    return errors


def fragment_pairs(records: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Пары записей, где один текст — начало или конец другого: признак обрезки."""
    keys = [(record_id, normalize_text(text)) for record_id, text in records]
    pairs: list[tuple[str, str]] = []
    for index, (left_id, left) in enumerate(keys):
        for right_id, right in keys[index + 1:]:
            if not left or not right or left == right:
                continue
            if left.startswith(right) or left.endswith(right) or right.startswith(left) or right.endswith(left):
                pairs.append((left_id, right_id))
    return pairs
