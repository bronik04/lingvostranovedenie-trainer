"""Разбор варианта олимпиады, выгруженного из Цифриума (PDF предпросмотра с ответами).

У такой выгрузки нет ни номеров заданий, ни букв вариантов, а год не напечатан: этап и классы
стоят в шапке, год приходит из JOBS. Правильный вариант выделен зелёным цветом шрифта, поэтому
текст читается через `pdftohtml -xml`: там у каждого куска текста есть шрифт с цветом.
"""

from __future__ import annotations

import re
import subprocess
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path

from normalize import strip_artifacts

from parsers.pdf_papers import HEADER_STAGE, STAGES

GRADES = re.compile(r'(?P<low>\d+)\s*[-‒–]\s*(?P<high>\d+)\s+класс')
SECTION_START = re.compile(r'^ЛИНГВОСТРАНОВЕДЕНИЕ')
SECTION_END = re.compile(r'^(АУДИРОВАНИЕ|ЧТЕНИЕ|ЛЕКСИКО|ПИСЬМО|ГОВОРЕНИЕ)')
INSTRUCTION = re.compile(r'^Выберите верный вариант ответа')
TASK_END = re.compile(r'^За решение задачи')
TASK_ID = re.compile(r'#\d+\s*$')
# правильный вариант предпросмотр набирает зелёным: в этом разделе #85d16a, в ЛГ-тесте #7ec82e.
# Поэтому ключ — любой цвет, где зелёный канал заметно сильнее красного и синего
KEY_GREEN_MARGIN = 40
# колонтитулы браузера (дата печати, адрес страницы, номер листа) набраны мелко
MIN_FONT_SIZE = 15
# вариант ответа набран с отступом, формулировка — от левого края карточки
OPTION_LEFT = 150
# куски одной строки расходятся по высоте на 2–6 точек, строки — на 30 и больше
LINE_GAP = 10
# пробел между кусками ставится по зазору: одна версия poppler кладёт его в кусок («1905 » + «年»),
# другая может разрезать строку без него, а соседние иероглифы идут без зазора
SPACE_GAP = 4
# шрифт выгрузки отдаёт часть иероглифов знаками-ключами: ⼤ вместо 大, ⻢ вместо 马.
# Ключи Канси NFKC сводит к обычным иероглифам, дополнительные ключи — только эта таблица
RADICALS = {'⻆': '角', '⻄': '西', '⻢': '马'}
KANGXI = re.compile('[⼀-⿟]')
SUPPLEMENT = re.compile('[⺀-⻿]')


def _clean(text: str) -> str:
    text = KANGXI.sub(lambda match: unicodedata.normalize('NFKC', match.group()), text)
    return SUPPLEMENT.sub(lambda match: RADICALS.get(match.group(), match.group()), text)


def _is_key(color: str) -> bool:
    match = re.fullmatch(r'#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})', color)
    if not match:
        return False
    red, green, blue = (int(channel, 16) for channel in match.groups())
    return green - max(red, blue) >= KEY_GREEN_MARGIN


def _pieces(path: Path) -> list[tuple[int, int, int, int, str, bool]]:
    """Куски текста: (лист, верх, левый край, ширина, текст, отмечен ли зелёным)."""
    result = subprocess.run(['pdftohtml', '-q', '-xml', '-i', '-stdout', str(path)],
                            capture_output=True, text=True, check=True)
    root = ET.fromstring(result.stdout)
    fonts: dict[str, tuple[int, str]] = {}
    pieces = []
    for page in root.iter('page'):
        number = int(page.get('number'))
        for element in page:
            if element.tag == 'fontspec':
                fonts[element.get('id')] = (int(element.get('size')), element.get('color', '').lower())
            elif element.tag == 'text':
                size, color = fonts[element.get('font')]
                text = ''.join(element.itertext())
                if size >= MIN_FONT_SIZE and text.strip():
                    pieces.append((number, int(element.get('top')), int(element.get('left')),
                                   int(element.get('width')), _clean(text), _is_key(color)))
    return sorted(pieces)


def _joined(row: list[tuple[int, int, int, int, str, bool]]) -> str:
    text, right = '', None
    for _, _, left, width, piece, _ in row:
        if right is not None and left - right > SPACE_GAP and not text.endswith(' ') and not piece.startswith(' '):
            text += ' '
        text += piece
        right = left + width
    return re.sub(r'\s+', ' ', text).strip()


def _lines(pieces: list[tuple[int, int, int, int, str, bool]]) -> list[tuple[int, str, bool]]:
    """Строки бланка: (левый край, текст, отмечена ли зелёным)."""
    rows: list[list[tuple[int, int, int, int, str, bool]]] = []
    for piece in pieces:
        last = rows[-1] if rows else None
        if last and last[0][0] == piece[0] and piece[1] - last[0][1] <= LINE_GAP:
            last.append(piece)
        else:
            rows.append([piece])
    lines = []
    for row in rows:
        row.sort(key=lambda piece: piece[2])
        lines.append((row[0][2], _joined(row), any(piece[5] for piece in row)))
    return lines


def parse(path: Path, year: str) -> list[dict]:
    return records(_lines(_pieces(path)), path.name, year)


def records(lines: list[tuple[int, str, bool]], source_file: str, year: str) -> list[dict]:
    """Задания раздела из строк бланка: (левый край, текст, отмечена ли зелёным)."""
    stage, code, grades = '', 'unk', ''
    for _, text, _ in lines:
        stage_match = HEADER_STAGE.match(text)
        if stage_match and not stage:
            stage = stage_match.group('stage').lower()
            code = STAGES[stage_match.group('stage')]
        grades_match = GRADES.search(text)
        if grades_match and not grades:
            grades = f"{grades_match.group('low')}-{grades_match.group('high')}"

    tasks: list[dict] = []
    inside = False
    question: list[str] = []
    options: list[tuple[str, bool]] = []
    for left, text, marked in lines:
        if SECTION_START.match(text):
            inside, question, options = True, [], []
            continue
        if SECTION_END.match(text):
            inside = False
        if not inside or INSTRUCTION.match(text) or TASK_ID.fullmatch(text):
            continue
        if TASK_END.match(text):
            keys = [index for index, (_, green) in enumerate(options) if green]
            warnings = [] if len(keys) == 1 else [f'отмечено вариантов: {len(keys)}']
            if len(options) != 4:
                warnings.append(f'вариантов: {len(options)}')
            leftover = SUPPLEMENT.findall(' '.join([*question, *(option for option, _ in options)]))
            if leftover:
                warnings.append(f'знаки-ключи без замены: {"".join(sorted(set(leftover)))}')
            tasks.append({
                'sourceFile': source_file,
                'year': year,
                'stage': stage,
                'stageCode': code,
                'grades': grades,
                'number': len(tasks) + 1,
                'sourceOrdinal': None,
                'questionRu': ' '.join(question),
                'questionZh': None,
                'options': [strip_artifacts(option) for option, _ in options],
                'officialKeyIndex': keys[0] if len(keys) == 1 else None,
                'topic': None,
                'parseWarnings': warnings,
            })
            inside = False
            continue
        if left > OPTION_LEFT:
            options.append((text, marked))
        else:
            question.append(text)
    return tasks
