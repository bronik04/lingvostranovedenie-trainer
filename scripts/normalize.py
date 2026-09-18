"""Нормализация текста и инварианты банка вопросов."""

from __future__ import annotations

import re
import unicodedata

CYRILLIC = re.compile(r'[А-Яа-яЁё]')
CJK = re.compile(r'[一-鿿]')
OPTION_LABEL = re.compile(r'^\s*[A-DА-Г]\s*[.、．)）]\s*')
TERMINALS = ('?', '？', '.', '。', '!', '！', '…', ':', '：')
MIN_QUESTION_LENGTH = 25


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
    errors: list[str] = []
    if not CYRILLIC.search(question_ru):
        errors.append('вопрос показывается не по-русски')
    if CJK.search(question_ru):
        errors.append('иероглифы в русском тексте вопроса')
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
    if text and not (text[0].isupper() or text[0].isdigit()):
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
