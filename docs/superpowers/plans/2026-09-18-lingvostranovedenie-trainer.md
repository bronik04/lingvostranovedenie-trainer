# Тренажёр по лингвострановедению — план реализации

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Собрать из трёх DOCX, пяти PDF и файла переводов один канонический банк вопросов ВсОШ по лингвострановедению и выпускать из него самодостаточный HTML-тренажёр, где вопрос по-русски, варианты по-китайски, а у каждого ответа есть пояснение и источник.

**Architecture:** Питоновский конвейер из четырёх ступеней: парсеры приводят каждый источник к единой сырой записи в `data/raw/`, слияние дедуплицирует их по набору вариантов и собирает `data/bank.json`, рубрикация проставляет тему, сборщик встраивает банк в один HTML. Инварианты (язык, полнота формулировок, схема) живут в одном модуле и вызываются и тестами, и сборкой: нарушение останавливает сборку.

**Tech Stack:** Python 3 только со стандартной библиотекой (`zipfile`, `xml.etree`, `json`, `re`, `hashlib`) плюс системный `pdftotext`; ванильные HTML/CSS/JS; тесты — `python3 -m unittest` для конвейера и `node --test` для логики квиза и сборки.

## Global Constraints

- `python-docx` в системе нет и ставить его не нужно: DOCX читается через `zipfile` + `xml.etree`.
- Вопрос показывается по-русски, варианты — по-китайски. `questionRu` содержит кириллицу и не содержит иероглифов; `options[].zh` не содержит кириллицы. Латиница в вариантах допустима только там, где она есть в оригинале: `阿Q正传`, `HSK`, `YCT`, `TOEFL`.
- Полнота формулировок: `questionRu` не короче 25 символов, не начинается со строчной буквы или пробела, оканчивается на `?`, `？`, `.`, `。`, `!`, `！`, `…`, `:` или `：`, и ни один вопрос не является началом или концом другого.
- Нарушение языкового инварианта или полноты — ошибка сборки, а не предупреждение.
- Темы — ровно семь из `data/taxonomy.json`. Темы «Разное» в итоговом банке нет.
- `id` записи: `<год>-<код этапа>-<номер>` самого раннего появления, коды этапов `pri`, `shk`, `mun`, `reg`, `zak`.
- Правильность хранится в `answer.optionId`; буквы A–D нигде не хранятся и рисуются по видимому порядку.
- Ответы не выдумываются: нет источника — `needs-review`, расхождение — `conflict`.
- Слияние детерминировано: повторный прогон на тех же `sources/` даёт побайтово тот же `data/bank.json`.
- Артефакт — один файл `dist/lingvostranovedenie-trainer.html` без единой внешней ссылки.
- Коммит после каждой задачи.

**Спека:** `docs/superpowers/specs/2026-09-18-lingvostranovedenie-trainer-design.md`

## Карта файлов

| Файл | Ответственность |
|---|---|
| `scripts/normalize.py` | нормализация текста, ключи дедупликации, проверки языка и полноты |
| `scripts/docx_text.py` | DOCX → список абзацев |
| `scripts/parsers/bank423.py` | разбор банка 423 |
| `scripts/parsers/categories310.py` | разбор базы «310», источник тем и полных формулировок |
| `scripts/parsers/vsosh.py` | разбор сводного сборника и таблицы ключей |
| `scripts/parsers/pdf_papers.py` | разбор оригинальных бланков PDF |
| `scripts/import_sources.py` | CLI: все парсеры → `data/raw/*.json` |
| `scripts/merge_bank.py` | дедупликация, склейка появлений, выбор полной редакции, конфликты, `id` |
| `scripts/taxonomy.py` | рубрикация по семи категориям и отчёт |
| `scripts/build_html.py` | проверка инвариантов и сборка одного HTML |
| `scripts/wave.py` | выбор очередной волны проверки и приём её результатов |
| `src/quiz.mjs` | логика раунда: отбор, перемешивание, метки, оценка |
| `src/template.html`, `src/quiz.css` | разметка трёх экранов и стили |
| `src/quiz.ui.js` | обвязка экранов: фильтры, ход раунда, разбор, база, прогресс в localStorage |

Сырая запись, которую отдаёт любой парсер, — единый контракт всего конвейера:

```python
{
    'sourceFile': 'Банк вопросов — лингвострановедение (423, с ответами).docx',
    'year': '2015-16',
    'stage': 'школьный',
    'stageCode': 'shk',
    'grades': '9-11',
    'number': 1,
    'questionRu': None,                 # или строка
    'questionZh': '现在中国的人口总数是多少？',
    'options': ['接近20亿', '接近1亿', '接近15亿', '超过18亿'],   # в порядке A–D документа
    'officialKeyIndex': 2,              # 0..3 или None
    'topic': None,                      # заполняет только categories310
    'parseWarnings': [],
}
```

---

### Task 1: Скелет репозитория и первоисточники

**Files:**
- Create: `README.md`, `CLAUDE.md`, `package.json`, `sources/manifest.json`
- Create: `sources/` (копии восьми файлов с Яндекс.Диска)
- Test: `test/test_sources.py`

**Interfaces:**
- Produces: `sources/manifest.json` — список `{name, sha256, bytes}` по каждому первоисточнику.

- [ ] **Step 1: Скопировать первоисточники**

```bash
cd ~/Documents/Projects/lingvostranovedenie-trainer
SRC="$HOME/Yandex.Disk.localized/Китайский язык/03-Экзамены/03-ВСОШ/02-Материалы/01-Лингвострановедение"
mkdir -p sources data/raw data/review dist
cp "$SRC"/*.docx "$SRC"/*.pdf sources/
ls sources | wc -l   # ожидается 8
```

- [ ] **Step 2: Написать падающий тест на манифест**

```python
# test/test_sources.py
import hashlib, json, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = 8


class ManifestTest(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((ROOT / 'sources/manifest.json').read_text('utf-8'))

    def test_manifest_lists_every_source(self):
        on_disk = {p.name for p in (ROOT / 'sources').iterdir() if p.suffix in {'.docx', '.pdf'}}
        self.assertEqual(len(on_disk), EXPECTED)
        self.assertEqual({entry['name'] for entry in self.manifest}, on_disk)

    def test_checksums_match_disk(self):
        for entry in self.manifest:
            data = (ROOT / 'sources' / entry['name']).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), entry['sha256'], entry['name'])
            self.assertEqual(len(data), entry['bytes'], entry['name'])


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 3: Прогнать тест и убедиться, что он падает**

Run: `python3 -m unittest test.test_sources -v`
Expected: FAIL — `FileNotFoundError: sources/manifest.json`

- [ ] **Step 4: Сгенерировать манифест**

```python
# scripts/make_manifest.py
import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    entries = []
    for path in sorted((ROOT / 'sources').iterdir()):
        if path.suffix not in {'.docx', '.pdf'}:
            continue
        data = path.read_bytes()
        entries.append({
            'name': path.name,
            'sha256': hashlib.sha256(data).hexdigest(),
            'bytes': len(data),
        })
    target = ROOT / 'sources/manifest.json'
    target.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'{len(entries)} источников записано в {target}')


if __name__ == '__main__':
    main()
```

Run: `python3 scripts/make_manifest.py`

- [ ] **Step 5: Прогнать тест и убедиться, что он проходит**

Run: `python3 -m unittest test.test_sources -v`
Expected: PASS, два теста

- [ ] **Step 6: Написать README.md и CLAUDE.md**

`README.md` — что это, откуда данные, как собрать:

```markdown
# Тренажёр по лингвострановедению (ВсОШ, китайский язык)

Банк вопросов раздела «Лингвострановедение» Всероссийской олимпиады школьников
за 2015/16 — 2025/26 и тренажёр к нему: вопрос по-русски, варианты по-китайски,
у каждого ответа пояснение и ссылка на источник.

## Сборка

    python3 scripts/import_sources.py     # sources/ -> data/raw/
    python3 scripts/merge_bank.py         # data/raw/ -> data/bank.json + отчёты
    python3 scripts/build_html.py         # data/bank.json -> dist/

## Тесты

    python3 -m unittest discover -s test -v
    node --test test/

## Данные

`sources/` — неизменяемые первоисточники, их контрольные суммы в `sources/manifest.json`.
`data/bank.json` — канонический банк, единственный источник правды для сборки.
`data/review/` — отчёты слияния, рубрикации и волн проверки ответов.
```

`CLAUDE.md` — правила работы в репозитории:

```markdown
# Правила работы

- Вопрос всегда по-русски, варианты всегда по-китайски. Проверяется `scripts/normalize.py`,
  нарушение останавливает сборку.
- Формулировки не сокращать. Если источники расходятся по длине, берётся полная редакция.
- Ответы не выдумывать: нет подтверждающего источника — `needs-review`, расхождение с
  официальным ключом — `conflict` и запись в отчёт волны.
- `sources/` не редактировать: это неизменяемые первоисточники.
- `data/bank.json` правится только скриптами, руками — никогда.
- Тесты: `python3 -m unittest discover -s test` и `node --test test/`.
```

- [ ] **Step 7: Добавить package.json**

```json
{
  "name": "lingvostranovedenie-trainer",
  "private": true,
  "type": "module",
  "scripts": {
    "test": "node --test test/",
    "build": "python3 scripts/import_sources.py && python3 scripts/merge_bank.py && python3 scripts/build_html.py"
  }
}
```

- [ ] **Step 8: Коммит**

```bash
git add sources package.json README.md CLAUDE.md scripts/make_manifest.py test/test_sources.py
git commit -m "Первоисточники, манифест и скелет репозитория"
```

---

### Task 2: Инварианты языка и полноты

**Files:**
- Create: `scripts/normalize.py`
- Test: `test/test_normalize.py`

**Interfaces:**
- Produces:
  - `normalize_text(value: str) -> str`
  - `option_key(options: list[str]) -> tuple[str, ...]`
  - `language_errors(question_ru: str, options: list[str]) -> list[str]`
  - `completeness_errors(question_ru: str, question_zh: str | None, options: list[str]) -> list[str]`
  - `fragment_pairs(records: list[tuple[str, str]]) -> list[tuple[str, str]]`

- [ ] **Step 1: Написать падающий тест**

Тест построен на настоящих обрезках из старого банка — это регрессионный набор.

```python
# test/test_normalize.py
import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from normalize import (completeness_errors, fragment_pairs, language_errors,
                       normalize_text, option_key)

WHOLE = 'Административный центр провинции Цзянсу, одна из четырех древних столиц Китая.'


class NormalizeTest(unittest.TestCase):
    def test_normalize_strips_labels_spaces_and_tail_punctuation(self):
        self.assertEqual(normalize_text('A) 接近 20 亿'), '接近20亿')
        self.assertEqual(normalize_text('B. 上海'), '上海')
        self.assertEqual(normalize_text('中国最大的港口城市是哪一个？'), '中国最大的港口城市是哪一个')

    def test_option_key_ignores_order_and_labels(self):
        self.assertEqual(option_key(['A) 广州', 'B) 上海']), option_key(['上海', '广州']))


class LanguageTest(unittest.TestCase):
    def test_accepts_russian_question_with_chinese_options(self):
        self.assertEqual(language_errors(WHOLE, ['西安', '北京', '洛阳', '南京']), [])

    def test_accepts_numeric_and_latin_options_from_originals(self):
        self.assertEqual(language_errors(WHOLE, ['5%', '22%', 'HSK', '阿Q正传']), [])

    def test_rejects_chinese_question(self):
        self.assertTrue(language_errors('中国最大的港口城市是哪一个？', ['上海']))

    def test_rejects_cyrillic_option(self):
        self.assertTrue(language_errors(WHOLE, ['Шанхай', '北京']))


class CompletenessTest(unittest.TestCase):
    def test_accepts_whole_question(self):
        self.assertEqual(completeness_errors(WHOLE, '江苏省的行政中心是哪里？', ['西安', '南京']), [])

    def test_rejects_question_cut_at_the_head(self):
        self.assertTrue(completeness_errors('дминистративный центр провинции Цзянсу.', None, ['西安']))

    def test_rejects_question_cut_at_the_tail(self):
        self.assertTrue(completeness_errors(
            'Река Хуанхэ отделяет эту провинцию от провинции Шэньси. В этой провинции',
            None, ['山西', '河北']))

    def test_rejects_leading_space(self):
        self.assertTrue(completeness_errors(' какой провинции расположены три из пяти СЭЗ?', None, ['广东']))

    def test_rejects_too_short_question(self):
        self.assertTrue(completeness_errors('Столица Китая?', None, ['北京']))

    def test_rejects_empty_option(self):
        self.assertTrue(completeness_errors(WHOLE, None, ['西安', '  ']))


class FragmentTest(unittest.TestCase):
    def test_reports_question_that_is_a_prefix_of_another(self):
        pairs = fragment_pairs([
            ('2023-24-shk-138', 'Административный центр провинции Цзянсу, одна из четырех древних столиц'),
            ('2023-24-mun-138', WHOLE),
            ('2015-16-shk-1', 'Какова общая численность населения Китая в настоящее время?'),
        ])
        self.assertEqual(pairs, [('2023-24-shk-138', '2023-24-mun-138')])


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Прогнать тест и убедиться, что он падает**

Run: `python3 -m unittest test.test_normalize -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'normalize'`

- [ ] **Step 3: Написать модуль**

```python
# scripts/normalize.py
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
```

- [ ] **Step 4: Прогнать тест и убедиться, что он проходит**

Run: `python3 -m unittest test.test_normalize -v`
Expected: PASS, 13 тестов

- [ ] **Step 5: Коммит**

```bash
git add scripts/normalize.py test/test_normalize.py
git commit -m "Инварианты языка и полноты формулировок"
```

---

### Task 3: Чтение DOCX и разбор банка 423

**Files:**
- Create: `scripts/docx_text.py`, `scripts/parsers/__init__.py`, `scripts/parsers/bank423.py`
- Test: `test/test_bank423.py`

**Interfaces:**
- Consumes: `normalize_text` из Task 2.
- Produces:
  - `docx_text.paragraphs(path: Path) -> list[str]`
  - `bank423.parse(path: Path) -> list[dict]` — сырые записи по контракту из карты файлов.

Формат источника подтверждён на файле: заголовок темы отдельным абзацем, затем `138. <вопрос>`, затем `A) … B) … C) … D) …` одной строкой, затем `Ответ: C · 2023-24, мун., 9-11` либо `Ответ: в опубликованных ключах отсутствует · 2023-24, школ., 9-11`. Вопросы ранних лет записаны по-китайски: 192 из 423. Сокращения этапов в источнике: `пригл.`, `школ.`, `мун.`, `рег.`, `закл.`

- [ ] **Step 1: Написать падающий тест**

```python
# test/test_bank423.py
import sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from docx_text import paragraphs
from parsers.bank423 import parse

SOURCE = ROOT / 'sources/Банк вопросов — лингвострановедение (423, с ответами).docx'


class DocxTextTest(unittest.TestCase):
    def test_reads_paragraphs_without_python_docx(self):
        lines = paragraphs(SOURCE)
        self.assertGreater(len(lines), 1000)
        self.assertEqual(lines[0], 'БАНК ЗАДАНИЙ: ЛИНГВОСТРАНОВЕДЕНИЕ')
        self.assertTrue(all(line == line.strip() for line in lines))


class Bank423Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = parse(SOURCE)

    def test_parses_every_question(self):
        self.assertEqual(len(self.records), 423)

    def test_first_record_is_complete(self):
        first = self.records[0]
        self.assertEqual(first['number'], 1)
        self.assertEqual(first['year'], '2015-16')
        self.assertEqual(first['stage'], 'школьный')
        self.assertEqual(first['stageCode'], 'shk')
        self.assertEqual(first['grades'], '9-11')
        self.assertEqual(first['questionZh'], '现在中国的人口总数是多少？')
        self.assertIsNone(first['questionRu'])
        self.assertEqual(first['options'], ['接近 20 亿', '接近 1 亿', '接近 15 亿', '超过 18 亿'])
        self.assertEqual(first['officialKeyIndex'], 2)

    def test_keeps_the_first_letter_of_russian_questions(self):
        """Старый импортёр съедал первый символ: 'дминистративный центр…'."""
        russian = [r['questionRu'] for r in self.records if r['questionRu']]
        self.assertTrue(any(q.startswith('Административный центр провинции Цзянсу') for q in russian))
        self.assertFalse(any(q[0].islower() for q in russian))

    def test_missing_key_becomes_none(self):
        without_key = [r for r in self.records if r['officialKeyIndex'] is None]
        self.assertEqual(len(without_key), 118)

    def test_two_known_broken_option_lines_are_reported_not_silently_padded(self):
        """В источнике две испорченные строки вариантов — парсер обязан о них сказать."""
        broken = [r for r in self.records if not all(option.strip() for option in r['options'])]
        self.assertEqual(len(broken), 2)
        for record in broken:
            self.assertEqual(len(record['options']), 4, record['number'])
            self.assertTrue(record['parseWarnings'], record['number'])

    def test_repeated_letter_does_not_overwrite_the_first_option(self):
        """Строка 'A) 兵马俑 B) 十三陵 C) 大唐芙蓉园 A) 大唐芙蓉园': первый вариант остаётся 兵马俑."""
        record = next(r for r in self.records if '兵马俑' in ' '.join(r['options']))
        self.assertEqual(record['options'][0], '兵马俑')
        self.assertIn('буква варианта повторяется: A', record['parseWarnings'])

    def test_every_other_record_has_four_filled_options(self):
        healthy = [r for r in self.records if not r['parseWarnings']]
        self.assertEqual(len(healthy), 421)
        for record in healthy:
            self.assertEqual(len(record['options']), 4, record['number'])
            self.assertTrue(all(option.strip() for option in record['options']), record['number'])


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Прогнать тест и убедиться, что он падает**

Run: `python3 -m unittest test.test_bank423 -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'docx_text'`

- [ ] **Step 3: Написать чтение DOCX**

```python
# scripts/docx_text.py
"""Чтение абзацев DOCX без внешних зависимостей."""

from __future__ import annotations

import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree

NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'


def paragraphs(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as archive:
        xml = archive.read('word/document.xml').decode('utf-8')
    root = ElementTree.fromstring(xml)
    lines: list[str] = []
    for node in root.iter(f'{{{NS}}}p'):
        text = ''.join(run.text or '' for run in node.iter(f'{{{NS}}}t'))
        text = re.sub(r'\s+', ' ', text).strip()
        if text:
            lines.append(text)
    return lines
```

- [ ] **Step 4: Написать парсер банка 423**

Первый символ вопроса теряться не может: текст берётся группой регулярного выражения после номера, а не срезом строки.

```python
# scripts/parsers/bank423.py
"""Разбор файла «Банк вопросов — лингвострановедение (423, с ответами).docx»."""

from __future__ import annotations

import re
from pathlib import Path

from docx_text import paragraphs

QUESTION = re.compile(r'^(?P<number>\d+)\.\s+(?P<text>\S.*)$')
OPTIONS = re.compile(r'([A-D])\)\s*(.*?)(?=\s+[A-D]\)|$)')
ANSWER = re.compile(r'^Ответ:\s*(?P<key>[A-D]|в опубликованных ключах отсутствует)\s*·\s*(?P<source>.+)$')
SOURCE = re.compile(r'^(?P<year>\d{4}-\d{2}),\s*(?P<stage>[^,]+),\s*(?P<grades>.+)$')
CYRILLIC = re.compile(r'[А-Яа-яЁё]')

STAGES = {
    'пригл.': ('пригласительный', 'pri'),
    'школ.': ('школьный', 'shk'),
    'мун.': ('муниципальный', 'mun'),
    'рег.': ('региональный', 'reg'),
    'закл.': ('заключительный', 'zak'),
}


def _options(line: str) -> tuple[list[str], list[str]]:
    """Варианты в порядке A–D и предупреждения о дефектах строки.

    В источнике есть две испорченные строки: у вопроса про достопримечательность
    четвёртый вариант помечен буквой A вместо D, у вопроса про кухни варианта D нет
    вовсе. Буква, встреченная второй раз, не затирает первую — иначе «兵马俑» пропадёт.
    """
    found: dict[str, str] = {}
    duplicates: list[str] = []
    for letter, text in OPTIONS.findall(line):
        if letter in found:
            duplicates.append(letter)
            continue
        found[letter] = text.strip()
    options = [found.get(letter, '') for letter in 'ABCD']
    warnings: list[str] = []
    if duplicates:
        warnings.append(f'буква варианта повторяется: {", ".join(duplicates)}')
    missing = [letter for letter in 'ABCD' if not found.get(letter)]
    if missing:
        warnings.append(f'нет вариантов: {", ".join(missing)}')
    return options, warnings


def parse(path: Path) -> list[dict]:
    lines = paragraphs(path)
    records: list[dict] = []
    pending: dict | None = None
    for line in lines:
        question = QUESTION.match(line)
        if question and not line.startswith('Ответ:'):
            text = question.group('text').strip()
            pending = {
                'sourceFile': path.name,
                'number': int(question.group('number')),
                'questionRu': text if CYRILLIC.search(text) else None,
                'questionZh': None if CYRILLIC.search(text) else text,
                'options': [],
                'officialKeyIndex': None,
                'topic': None,
                'parseWarnings': [],
            }
            continue
        if pending is not None and not pending['options'] and OPTIONS.search(line):
            pending['options'], warnings = _options(line)
            pending['parseWarnings'].extend(warnings)
            continue
        answer = ANSWER.match(line)
        if pending is not None and answer:
            key = answer.group('key')
            pending['officialKeyIndex'] = None if key.startswith('в опубликованных') else 'ABCD'.index(key)
            source = SOURCE.match(answer.group('source').strip())
            if source:
                stage, code = STAGES.get(source.group('stage').strip(), (source.group('stage').strip(), 'unk'))
                pending.update({
                    'year': source.group('year'),
                    'stage': stage,
                    'stageCode': code,
                    'grades': source.group('grades').strip(),
                })
            else:
                pending.update({'year': '', 'stage': '', 'stageCode': 'unk', 'grades': ''})
                pending['parseWarnings'].append(f'не разобран источник: {answer.group("source")!r}')
            records.append(pending)
            pending = None
    return records
```

- [ ] **Step 5: Прогнать тесты и убедиться, что они проходят**

Run: `python3 -m unittest test.test_bank423 -v`
Expected: PASS, 6 тестов

- [ ] **Step 6: Коммит**

```bash
git add scripts/docx_text.py scripts/parsers test/test_bank423.py
git commit -m "Чтение DOCX и разбор банка 423 без потери первого символа"
```

---

### Task 4: Перенос готовых переводов

**Files:**
- Create: `scripts/migrate_translations.py`, `data/translations.json`
- Test: `test/test_translations.py`

**Interfaces:**
- Consumes: `normalize_text` из Task 2, `bank423.parse` из Task 3.
- Produces: `data/translations.json` — словарь `{нормализованный китайский вопрос: русский текст}`.

В старом проекте 201 перевод лежит в `work/manual_translations.json` под ключами прежней схемы (`geography-001-001`). Схема `id` меняется, поэтому переводы перекладываются на ключ, который не зависит от нумерации, — нормализованный китайский текст вопроса. Китайских вопросов в банке 192, так что переводов должно хватить на все.

- [ ] **Step 1: Написать падающий тест**

```python
# test/test_translations.py
import json, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from normalize import CYRILLIC, normalize_text
from parsers.bank423 import parse

SOURCE = ROOT / 'sources/Банк вопросов — лингвострановедение (423, с ответами).docx'


class TranslationsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.translations = json.loads((ROOT / 'data/translations.json').read_text('utf-8'))
        cls.records = parse(SOURCE)

    def test_keyed_by_normalised_chinese(self):
        key = normalize_text('现在中国的人口总数是多少？')
        self.assertEqual(self.translations[key], 'Какова общая численность населения Китая в настоящее время?')

    def test_covers_every_chinese_only_question(self):
        missing = [r['questionZh'] for r in self.records
                   if r['questionRu'] is None and normalize_text(r['questionZh']) not in self.translations]
        self.assertEqual(missing, [], f'без перевода осталось {len(missing)} вопросов')

    def test_every_translation_is_russian(self):
        for chinese, russian in self.translations.items():
            self.assertTrue(CYRILLIC.search(russian), chinese)


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Прогнать тест и убедиться, что он падает**

Run: `python3 -m unittest test.test_translations -v`
Expected: FAIL — `FileNotFoundError: data/translations.json`

- [ ] **Step 3: Написать перекладку**

```python
# scripts/migrate_translations.py
"""Перенос переводов старого проекта на ключ, не зависящий от нумерации."""

from __future__ import annotations

import json
from pathlib import Path

from normalize import normalize_text

ROOT = Path(__file__).resolve().parents[1]
OLD = Path.home() / 'Documents/Codex/2026-09-17/html/work'


def main() -> None:
    old_bank = json.loads((OLD / 'question_bank.json').read_text('utf-8'))
    old_translations = json.loads((OLD / 'manual_translations.json').read_text('utf-8'))
    by_id = {record['id']: record for record in old_bank}

    translations: dict[str, str] = {}
    skipped: list[str] = []
    for record_id, russian in old_translations.items():
        record = by_id.get(record_id)
        if record is None or not record.get('questionZh'):
            skipped.append(record_id)
            continue
        translations[normalize_text(record['questionZh'])] = russian.strip()

    target = ROOT / 'data/translations.json'
    target.write_text(
        json.dumps(dict(sorted(translations.items())), ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8',
    )
    print(f'перенесено переводов: {len(translations)}, пропущено: {len(skipped)}')
    if skipped:
        print('пропущенные ключи:', ', '.join(skipped[:10]))


if __name__ == '__main__':
    main()
```

Run: `python3 scripts/migrate_translations.py`

- [ ] **Step 4: Прогнать тест**

Run: `python3 -m unittest test.test_translations -v`
Expected: PASS. Если `test_covers_every_chinese_only_question` падает, тест печатает китайские тексты без перевода — перевести их вручную, дописать в `data/translations.json` и прогнать снова. Перечень таких вопросов идёт отдельным списком в отчёт о слиянии (Task 9).

- [ ] **Step 5: Коммит**

```bash
git add scripts/migrate_translations.py data/translations.json test/test_translations.py
git commit -m "Перенос переводов на ключ по китайскому тексту"
```

---

### Task 5: Разбор базы «310» — темы и полные формулировки

**Files:**
- Create: `scripts/parsers/categories310.py`
- Test: `test/test_categories310.py`

**Interfaces:**
- Produces: `categories310.parse(path: Path) -> list[dict]` — сырые записи с заполненным `topic` и полным `questionRu`.

Формат: заголовок `34. 2025–2026, Региональный этап, №7`, затем русский вопрос, затем четыре строки `A. …`. Год записан длинно (`2025–2026`) и приводится к короткому виду (`2025-26`). Эта база — источник полных формулировок: именно здесь лежит `…одна из четырех древних столиц Китая.`, обрезанное в банке 423.

- [ ] **Step 1: Написать падающий тест**

```python
# test/test_categories310.py
import sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from parsers.categories310 import parse

SOURCE = ROOT / 'sources/Вопросы по категориям (310 шт).docx'
TOPICS = {
    'География и административное устройство',
    'Россия и межкультурный блок',
    'Литература, язык, искусство и философия',
    'История и государство',
    'Общество: население, этносы и религии',
    'Экономика, образование, наука и спорт',
    'Культура, традиции и праздники',
}


class Categories310Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = parse(SOURCE)

    def test_parses_every_question(self):
        self.assertEqual(len(self.records), 310)

    def test_every_record_carries_one_of_seven_topics(self):
        self.assertEqual({r['topic'] for r in self.records}, TOPICS)

    def test_year_is_normalised_to_short_form(self):
        self.assertTrue(all(len(r['year']) == 7 and r['year'][4] == '-' for r in self.records))

    def test_holds_the_whole_wording_cut_in_bank423(self):
        wanted = 'Административный центр провинции Цзянсу, одна из четырех древних столиц Китая.'
        self.assertIn(wanted, [r['questionRu'] for r in self.records])

    def test_questions_are_russian_and_options_chinese(self):
        for record in self.records:
            self.assertIsNotNone(record['questionRu'], record['number'])
            self.assertEqual(len(record['options']), 4, record['number'])

    def test_stage_codes_are_known(self):
        self.assertTrue({r['stageCode'] for r in self.records} <= {'pri', 'shk', 'mun', 'reg', 'zak'})


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Прогнать тест и убедиться, что он падает**

Run: `python3 -m unittest test.test_categories310 -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'parsers.categories310'`

- [ ] **Step 3: Написать парсер**

```python
# scripts/parsers/categories310.py
"""Разбор файла «Вопросы по категориям (310 шт).docx»."""

from __future__ import annotations

import re
from pathlib import Path

from docx_text import paragraphs

HEADER = re.compile(
    r'^(?P<ordinal>\d+)\.\s+(?P<year>\d{4}[–-]\d{4}),\s*(?P<stage>[^,]+?)\s*этап,\s*№\s*(?P<number>\d+)$'
)
OPTION = re.compile(r'^(?P<letter>[A-D])[.、．)]\s*(?P<text>\S.*)$')
SECTION = re.compile(r'^\d+\.\s+(?P<topic>[^—]+?)\s+—\s+\d+\s+вопрос')

STAGES = {
    'Пригласительный': ('пригласительный', 'pri'),
    'Школьный': ('школьный', 'shk'),
    'Муниципальный': ('муниципальный', 'mun'),
    'Региональный': ('региональный', 'reg'),
    'Заключительный': ('заключительный', 'zak'),
}


def _short_year(value: str) -> str:
    start, end = re.split(r'[–-]', value)
    return f'{start}-{end[2:]}'


def parse(path: Path) -> list[dict]:
    lines = paragraphs(path)
    records: list[dict] = []
    topic: str | None = None
    index = 0
    while index < len(lines):
        line = lines[index]
        section = SECTION.match(line)
        if section:
            topic = section.group('topic').strip()
            index += 1
            continue
        header = HEADER.match(line)
        if not header:
            index += 1
            continue
        question = lines[index + 1] if index + 1 < len(lines) else ''
        options: list[str] = []
        cursor = index + 2
        while cursor < len(lines) and len(options) < 4:
            option = OPTION.match(lines[cursor])
            if not option:
                break
            options.append(option.group('text').strip())
            cursor += 1
        if len(options) == 4:
            stage, code = STAGES.get(header.group('stage').strip(), (header.group('stage').strip(), 'unk'))
            records.append({
                'sourceFile': path.name,
                'year': _short_year(header.group('year')),
                'stage': stage,
                'stageCode': code,
                'grades': '',
                'number': int(header.group('number')),
                'questionRu': question.strip(),
                'questionZh': None,
                'options': options,
                'officialKeyIndex': None,
                'topic': topic,
                'parseWarnings': [],
            })
        index = cursor
    return records
```

- [ ] **Step 4: Прогнать тесты**

Run: `python3 -m unittest test.test_categories310 -v`
Expected: PASS, 6 тестов

- [ ] **Step 5: Коммит**

```bash
git add scripts/parsers/categories310.py test/test_categories310.py
git commit -m "Разбор базы «310»: темы и полные формулировки"
```

---

### Task 6: Разбор сводного сборника и таблицы ключей

**Files:**
- Create: `scripts/parsers/vsosh.py`
- Test: `test/test_vsosh.py`

**Interfaces:**
- Produces:
  - `vsosh.parse(path: Path) -> list[dict]`
  - `vsosh.parse_keys(lines: list[str]) -> dict[tuple[str, str, int], int]` — `(год, код этапа, номер) → индекс ответа`

Формат: заголовок года `2015–2016 уч. г.`, заголовок этапа `Школьный этап`, затем `56. 现在中国的人口总数是多少？` и четыре строки `A. …`. В конце документа таблица ключей построчно: `Региональный этап: 1—B, 2—C, 3—D, …` под заголовком своего года. Этот сборник — единственный источник ключей помимо банка 423, поэтому таблица разбирается отдельной функцией.

- [ ] **Step 1: Написать падающий тест**

```python
# test/test_vsosh.py
import sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from docx_text import paragraphs
from parsers.vsosh import parse, parse_keys

SOURCE = ROOT / 'sources/Лингвострановедение ВсОШ.docx'


class VsoshKeysTest(unittest.TestCase):
    def test_reads_key_table_rows(self):
        keys = parse_keys([
            '2024–2025 уч. г.',
            'Региональный этап: 1—B, 2—C, 3—A, 4—A, 5—D',
            '2025–2026 уч. г.',
            'Школьный этап: 28—B, 29—C',
        ])
        self.assertEqual(keys[('2024-25', 'reg', 1)], 1)
        self.assertEqual(keys[('2024-25', 'reg', 4)], 0)
        self.assertEqual(keys[('2025-26', 'shk', 29)], 2)

    def test_ignores_the_note_about_missing_keys(self):
        keys = parse_keys(['Примечание: ответы отсутствуют или неполные для этапов: 15-16 — Заключительный'])
        self.assertEqual(keys, {})


class VsoshParseTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = parse(SOURCE)

    def test_parses_about_three_hundred_questions(self):
        self.assertGreaterEqual(len(self.records), 300)

    def test_first_record_carries_year_stage_and_number(self):
        first = self.records[0]
        self.assertEqual(first['year'], '2015-16')
        self.assertEqual(first['stageCode'], 'shk')
        self.assertEqual(first['number'], 56)
        self.assertEqual(first['questionZh'], '现在中国的人口总数是多少？')

    def test_keys_are_attached_where_the_table_has_them(self):
        with_keys = [r for r in self.records if r['officialKeyIndex'] is not None]
        self.assertGreater(len(with_keys), 100)

    def test_every_record_has_four_options(self):
        for record in self.records:
            self.assertEqual(len(record['options']), 4, (record['year'], record['number']))


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Прогнать тест и убедиться, что он падает**

Run: `python3 -m unittest test.test_vsosh -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'parsers.vsosh'`

- [ ] **Step 3: Написать парсер**

```python
# scripts/parsers/vsosh.py
"""Разбор сводного сборника «Лингвострановедение ВсОШ.docx» и таблицы ключей."""

from __future__ import annotations

import re
from pathlib import Path

from docx_text import paragraphs

YEAR = re.compile(r'^(?P<start>\d{4})[–-](?P<end>\d{4})\s+уч\.\s*г\.$')
STAGE_LINE = re.compile(r'^(?P<stage>Пригласительный|Школьный|Муниципальный|Региональный|Заключительный)\s+этап$')
KEY_LINE = re.compile(r'^(?P<stage>Пригласительный|Школьный|Муниципальный|Региональный|Заключительный)\s+этап:\s*(?P<body>.+)$')
KEY_PAIR = re.compile(r'(\d+)\s*[—–-]\s*([A-D])')
QUESTION = re.compile(r'^(?P<number>\d+)[.、]\s+(?P<text>\S.*)$')
OPTION = re.compile(r'^(?P<letter>[A-D])[.、．)]\s*(?P<text>\S.*)$')
CYRILLIC = re.compile(r'[А-Яа-яЁё]')

STAGES = {
    'Пригласительный': ('пригласительный', 'pri'),
    'Школьный': ('школьный', 'shk'),
    'Муниципальный': ('муниципальный', 'mun'),
    'Региональный': ('региональный', 'reg'),
    'Заключительный': ('заключительный', 'zak'),
}


def _short_year(start: str, end: str) -> str:
    return f'{start}-{end[2:]}'


def parse_keys(lines: list[str]) -> dict[tuple[str, str, int], int]:
    keys: dict[tuple[str, str, int], int] = {}
    year = ''
    for line in lines:
        year_match = YEAR.match(line)
        if year_match:
            year = _short_year(year_match.group('start'), year_match.group('end'))
            continue
        key_match = KEY_LINE.match(line)
        if not key_match or not year:
            continue
        _, code = STAGES[key_match.group('stage')]
        for number, letter in KEY_PAIR.findall(key_match.group('body')):
            keys[(year, code, int(number))] = 'ABCD'.index(letter)
    return keys


def parse(path: Path) -> list[dict]:
    lines = paragraphs(path)
    keys = parse_keys(lines)
    records: list[dict] = []
    year = ''
    stage, code = '', 'unk'
    index = 0
    while index < len(lines):
        line = lines[index]
        year_match = YEAR.match(line)
        if year_match:
            year = _short_year(year_match.group('start'), year_match.group('end'))
            index += 1
            continue
        stage_match = STAGE_LINE.match(line)
        if stage_match:
            stage, code = STAGES[stage_match.group('stage')]
            index += 1
            continue
        question = QUESTION.match(line)
        if not question or KEY_LINE.match(line):
            index += 1
            continue
        options: list[str] = []
        cursor = index + 1
        while cursor < len(lines) and len(options) < 4:
            option = OPTION.match(lines[cursor])
            if not option:
                break
            options.append(option.group('text').strip())
            cursor += 1
        if len(options) == 4 and year:
            number = int(question.group('number'))
            text = question.group('text').strip()
            records.append({
                'sourceFile': path.name,
                'year': year,
                'stage': stage,
                'stageCode': code,
                'grades': '',
                'number': number,
                'questionRu': text if CYRILLIC.search(text) else None,
                'questionZh': None if CYRILLIC.search(text) else text,
                'options': options,
                'officialKeyIndex': keys.get((year, code, number)),
                'topic': None,
                'parseWarnings': [],
            })
            index = cursor
        else:
            index += 1
    return records
```

- [ ] **Step 4: Прогнать тесты**

Run: `python3 -m unittest test.test_vsosh -v`
Expected: PASS, 6 тестов

- [ ] **Step 5: Коммит**

```bash
git add scripts/parsers/vsosh.py test/test_vsosh.py
git commit -m "Разбор сводного сборника и таблицы ключей"
```

---

### Task 7: Разбор оригинальных бланков PDF

**Files:**
- Create: `scripts/parsers/pdf_papers.py`
- Test: `test/test_pdf_papers.py`

**Interfaces:**
- Produces: `pdf_papers.parse(path: Path) -> list[dict]` — сырые записи; `officialKeyIndex` всегда `None`.

Ключей в этих файлах нет: проверено по всем пяти, там только бланки заданий. Роль PDF — старший авторитет по формулировкам. Год и этап берутся из шапки первой страницы (`Муниципальный этап. 9–11 классы.`), номера вопросов бывают двух видов: `1.` и `Задание 28.`. Файлы 2023-24 и 2024-25 содержат целый комплект олимпиады, поэтому разбирается только участок после заголовка `ЛИНГВОСТРАНОВЕДЕНИЕ` до следующего заголовка раздела заглавными буквами.

- [ ] **Step 1: Написать падающий тест**

```python
# test/test_pdf_papers.py
import sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from parsers.pdf_papers import parse

MUNICIPAL = ROOT / 'sources/Лингвострановедение 2022-23 — Муниципальный.pdf'
LATEST = ROOT / 'sources/Лингвострановедение 2024-25.pdf'


class PdfPapersTest(unittest.TestCase):
    def test_reads_header_year_and_stage(self):
        records = parse(MUNICIPAL)
        self.assertTrue(records)
        self.assertEqual(records[0]['year'], '2022-23')
        self.assertEqual(records[0]['stageCode'], 'mun')
        self.assertEqual(records[0]['number'], 1)
        self.assertEqual(
            records[0]['questionRu'],
            'В каком климатическом поясе находится большая часть территории Китая?')
        self.assertEqual(records[0]['options'], ['赤道带', '热带', '寒带', '温带'])

    def test_handles_zadanie_numbering(self):
        records = parse(LATEST)
        numbers = {record['number'] for record in records}
        self.assertIn(28, numbers)
        first = next(r for r in records if r['number'] == 28)
        self.assertEqual(first['questionRu'], 'Кто считается основателем российского флота?')

    def test_never_invents_keys(self):
        self.assertTrue(all(r['officialKeyIndex'] is None for r in parse(MUNICIPAL)))

    def test_multiline_question_is_joined_whole(self):
        """В бланке формулировка переносится на несколько строк — она должна склеиться целиком."""
        records = parse(MUNICIPAL)
        third = next(r for r in records if r['number'] == 3)
        self.assertTrue(third['questionRu'].endswith('?'))
        self.assertIn('классическим', third['questionRu'].lower())


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Прогнать тест и убедиться, что он падает**

Run: `python3 -m unittest test.test_pdf_papers -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'parsers.pdf_papers'`

- [ ] **Step 3: Написать парсер**

```python
# scripts/parsers/pdf_papers.py
"""Разбор оригинальных бланков олимпиады в PDF через системный pdftotext."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

HEADER_YEAR = re.compile(r'(?P<start>\d{4})\s*[-‒–]\s*(?P<end>\d{4})')
HEADER_STAGE = re.compile(r'(?P<stage>Пригласительный|Школьный|Муниципальный|Региональный|Заключительный)\s+этап')
SECTION_START = re.compile(r'^ЛИНГВОСТРАНОВЕДЕНИЕ')
SECTION_END = re.compile(r'^(ПИСЬМО|АУДИРОВАНИЕ|ЧТЕНИЕ|ЛЕКСИКА|ГРАММАТИКА|ГОВОРЕНИЕ|ПИСЬМЕННАЯ)')
QUESTION = re.compile(r'^(?:Задание\s+)?(?P<number>\d+)[.．]\s*(?P<text>\S.*)$')
OPTION = re.compile(r'^(?P<letter>[A-D])[.、．)]\s*(?P<text>\S.*)$')

STAGES = {
    'Пригласительный': 'pri', 'Школьный': 'shk', 'Муниципальный': 'mun',
    'Региональный': 'reg', 'Заключительный': 'zak',
}


def _text(path: Path) -> list[str]:
    result = subprocess.run(['pdftotext', str(path), '-'], capture_output=True, text=True, check=True)
    return [line.strip() for line in result.stdout.splitlines()]


def _header(lines: list[str]) -> tuple[str, str, str]:
    head = ' '.join(lines[:12])
    year_match = HEADER_YEAR.search(head)
    stage_match = HEADER_STAGE.search(head)
    year = f"{year_match.group('start')}-{year_match.group('end')[2:]}" if year_match else ''
    stage = stage_match.group('stage') if stage_match else ''
    return year, stage.lower(), STAGES.get(stage, 'unk')


def parse(path: Path) -> list[dict]:
    lines = _text(path)
    year, stage, code = _header(lines)

    inside = False
    records: list[dict] = []
    pending: dict | None = None
    for line in lines:
        if SECTION_START.match(line):
            inside = True
            continue
        if inside and SECTION_END.match(line):
            inside = False
        if not inside or not line:
            continue

        option = OPTION.match(line)
        if pending is not None and option:
            pending['options'].append(option.group('text').strip())
            if len(pending['options']) == 4:
                records.append(pending)
                pending = None
            continue

        question = QUESTION.match(line)
        if question:
            pending = {
                'sourceFile': path.name,
                'year': year,
                'stage': stage,
                'stageCode': code,
                'grades': '',
                'number': int(question.group('number')),
                'questionRu': question.group('text').strip(),
                'questionZh': None,
                'options': [],
                'officialKeyIndex': None,
                'topic': None,
                'parseWarnings': [],
            }
            continue

        if pending is not None and not pending['options']:
            # формулировка перенесена на следующую строку бланка — дописываем целиком
            pending['questionRu'] = f"{pending['questionRu']} {line}".strip()
    return records
```

- [ ] **Step 4: Прогнать тесты**

Run: `python3 -m unittest test.test_pdf_papers -v`
Expected: PASS, 4 теста

- [ ] **Step 5: Коммит**

```bash
git add scripts/parsers/pdf_papers.py test/test_pdf_papers.py
git commit -m "Разбор оригинальных бланков PDF"
```

---

### Task 8: Сбор всех источников в data/raw

**Files:**
- Create: `scripts/import_sources.py`
- Test: `test/test_import_sources.py`

**Interfaces:**
- Consumes: `parse` из четырёх парсеров.
- Produces: `data/raw/<slug>.json` — по файлу на источник, плюс `data/raw/index.json` со сводкой `{slug, sourceFile, records}`.

- [ ] **Step 1: Написать падающий тест**

```python
# test/test_import_sources.py
import json, subprocess, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ImportSourcesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, 'scripts/import_sources.py'], cwd=ROOT, check=True)
        cls.index = json.loads((ROOT / 'data/raw/index.json').read_text('utf-8'))

    def test_every_source_produced_a_file(self):
        self.assertEqual(len(self.index), 8)
        for entry in self.index:
            self.assertTrue((ROOT / 'data/raw' / f"{entry['slug']}.json").exists(), entry['slug'])

    def test_bank423_contributed_all_records(self):
        bank = next(e for e in self.index if e['slug'] == 'bank423')
        self.assertEqual(bank['records'], 423)

    def test_records_follow_the_raw_contract(self):
        records = json.loads((ROOT / 'data/raw/bank423.json').read_text('utf-8'))
        required = {'sourceFile', 'year', 'stage', 'stageCode', 'grades', 'number',
                    'questionRu', 'questionZh', 'options', 'officialKeyIndex', 'topic', 'parseWarnings'}
        for record in records:
            self.assertEqual(set(record), required)

    def test_import_is_deterministic(self):
        before = (ROOT / 'data/raw/bank423.json').read_bytes()
        subprocess.run([sys.executable, 'scripts/import_sources.py'], cwd=ROOT, check=True)
        self.assertEqual(before, (ROOT / 'data/raw/bank423.json').read_bytes())


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Прогнать тест и убедиться, что он падает**

Run: `python3 -m unittest test.test_import_sources -v`
Expected: FAIL — `can't open file 'scripts/import_sources.py'`

- [ ] **Step 3: Написать CLI**

```python
# scripts/import_sources.py
"""Прогон всех парсеров: sources/ -> data/raw/."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from parsers import bank423, categories310, pdf_papers, vsosh

JOBS = [
    ('bank423', 'Банк вопросов — лингвострановедение (423, с ответами).docx', bank423.parse),
    ('categories310', 'Вопросы по категориям (310 шт).docx', categories310.parse),
    ('vsosh', 'Лингвострановедение ВсОШ.docx', vsosh.parse),
    ('paper-2022-23-shk', 'Лингвострановедение 2022-23 — Школьный.pdf', pdf_papers.parse),
    ('paper-2022-23-mun', 'Лингвострановедение 2022-23 — Муниципальный.pdf', pdf_papers.parse),
    ('paper-2022-23-reg', 'Лингвострановедение 2022-23 — Региональный.pdf', pdf_papers.parse),
    ('paper-2022-23-zak', 'Лингвострановедение 2022-23 — Заключительный.pdf', pdf_papers.parse),
    ('paper-2023-24', 'Лингвострановедение 2023-24.pdf', pdf_papers.parse),
    ('paper-2024-25', 'Лингвострановедение 2024-25.pdf', pdf_papers.parse),
]


def main() -> None:
    raw = ROOT / 'data/raw'
    raw.mkdir(parents=True, exist_ok=True)
    index = []
    for slug, filename, parse in JOBS:
        path = ROOT / 'sources' / filename
        if not path.exists():
            print(f'пропуск, файла нет: {filename}')
            continue
        records = parse(path)
        (raw / f'{slug}.json').write_text(
            json.dumps(records, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        index.append({'slug': slug, 'sourceFile': filename, 'records': len(records)})
        print(f'{slug}: {len(records)}')
    (raw / 'index.json').write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
```

- [ ] **Step 4: Прогнать и сверить состав**

Run: `python3 scripts/import_sources.py`
Expected: строки вида `bank423: 423`, `categories310: 310`, `vsosh: 3xx`, и по строке на каждый PDF.

Если в `sources/` нет файла `Лингвострановедение 2022-23 — Школьный.pdf`, скрипт печатает `пропуск, файла нет` — это законный случай, число записей в `index.json` окажется меньше восьми, и тест `test_every_source_produced_a_file` нужно поправить под фактический состав `sources/manifest.json`.

- [ ] **Step 5: Прогнать тесты**

Run: `python3 -m unittest test.test_import_sources -v`
Expected: PASS, 4 теста

- [ ] **Step 6: Коммит**

```bash
git add scripts/import_sources.py data/raw test/test_import_sources.py
git commit -m "Сбор всех источников в data/raw"
```

---

### Task 9: Слияние в канонический банк

**Files:**
- Create: `scripts/merge_bank.py`
- Test: `test/test_merge.py`

**Interfaces:**
- Consumes: `option_key`, `normalize_text`, `completeness_errors`, `language_errors`, `fragment_pairs` из Task 2; `data/raw/*.json`; `data/translations.json`.
- Produces: `data/bank.json`, `data/review/merge.md`; функции `merge(raw: list[dict], translations: dict[str, str]) -> tuple[list[dict], dict]` и `record_id(occurrence: dict) -> str`.

Порядок авторитета: формулировка — PDF, затем банк 423, затем «310», затем сборник; при равенстве авторитета берётся самая длинная редакция. Ключ — банк 423 и таблица сборника; расхождение даёт `conflict`.

- [ ] **Step 1: Написать падающий тест**

```python
# test/test_merge.py
import json, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from merge_bank import merge, record_id


def raw(**overrides):
    record = {
        'sourceFile': 'Банк вопросов — лингвострановедение (423, с ответами).docx',
        'year': '2023-24', 'stage': 'школьный', 'stageCode': 'shk', 'grades': '9-11',
        'number': 138, 'questionRu': 'Административный центр провинции Цзянсу, одна из четырех древних столиц',
        'questionZh': None, 'options': ['西安', '北京', '洛阳', '南京'],
        'officialKeyIndex': None, 'topic': None, 'parseWarnings': [],
    }
    record.update(overrides)
    return record


class RecordIdTest(unittest.TestCase):
    def test_id_is_built_from_year_stage_and_number(self):
        self.assertEqual(record_id({'year': '2015-16', 'stageCode': 'shk', 'number': 56}), '2015-16-shk-56')


class MergeTest(unittest.TestCase):
    def test_merges_duplicates_by_option_set(self):
        bank, _ = merge([raw(), raw(year='2018-19', stageCode='mun', number=29)], {})
        self.assertEqual(len(bank), 1)
        self.assertEqual(len(bank[0]['occurrences']), 2)

    def test_record_with_a_missing_option_joins_the_complete_one(self):
        """В банке 423 у вопроса про восемь кухонь нет варианта D, в сборнике он есть."""
        question = '中国的菜有很多种类…请问“宫保鸡丁”和“鱼香肉丝”属于哪一个菜系？'
        broken = raw(questionRu=None, questionZh=question, options=['粤菜', '川菜', '湘菜', ''])
        whole = raw(sourceFile='Лингвострановедение ВсОШ.docx', questionRu=None, questionZh=question,
                    options=['粤菜', '川菜', '湘菜', '浙菜'], officialKeyIndex=1)
        bank, _ = merge([broken, whole], {question.replace('…', '').replace('“', '').replace('”', ''): 'Вопрос про кухни?'})
        self.assertEqual(len(bank), 1)
        self.assertEqual([option['zh'] for option in bank[0]['options']], ['粤菜', '川菜', '湘菜', '浙菜'])

    def test_record_whose_defect_is_in_the_original_paper_is_dropped_with_a_reason(self):
        """У вопроса про достопримечательность четвёртый вариант испорчен в самом бланке ВсОШ."""
        bank, report = merge([raw(options=['兵马俑', '十三陵', '大唐芙蓉园', ''])], {})
        self.assertEqual(bank, [])
        self.assertEqual(len(report['dropped']), 1)
        self.assertTrue(any('пустой вариант' in error for error in report['dropped'][0]['errors']))

    def test_keeps_the_whole_wording_over_the_truncated_one(self):
        whole = 'Административный центр провинции Цзянсу, одна из четырех древних столиц Китая.'
        bank, _ = merge([
            raw(),
            raw(sourceFile='Вопросы по категориям (310 шт).docx', questionRu=whole, topic='География и административное устройство'),
        ], {})
        self.assertEqual(bank[0]['questionRu'], whole)

    def test_takes_russian_text_from_translations_for_chinese_questions(self):
        bank, _ = merge(
            [raw(questionRu=None, questionZh='现在中国的人口总数是多少？', options=['接近20亿', '接近1亿', '接近15亿', '超过18亿'])],
            {'现在中国的人口总数是多少': 'Какова общая численность населения Китая в настоящее время?'})
        self.assertEqual(bank[0]['questionRu'], 'Какова общая численность населения Китая в настоящее время?')

    def test_official_key_becomes_the_answer_but_stays_unverified(self):
        bank, _ = merge([raw(officialKeyIndex=3)], {})
        self.assertEqual(bank[0]['answer'], {'optionId': 'o4', 'state': 'unverified'})

    def test_conflicting_keys_are_not_resolved_silently(self):
        bank, report = merge([raw(officialKeyIndex=3), raw(year='2018-19', stageCode='mun', officialKeyIndex=0)], {})
        self.assertEqual(bank[0]['answer']['state'], 'conflict')
        self.assertEqual(len(report['conflicts']), 1)

    def test_question_without_key_is_needs_review(self):
        bank, _ = merge([raw()], {})
        self.assertEqual(bank[0]['answer']['state'], 'needs-review')
        self.assertIsNone(bank[0]['answer']['optionId'])

    def test_report_lists_questions_left_without_russian_text(self):
        bank, report = merge([raw(questionRu=None, questionZh='某个没有翻译的问题？')], {})
        self.assertEqual(len(report['untranslated']), 1)
        self.assertEqual(bank, [])

    def test_merge_is_deterministic_regardless_of_input_order(self):
        first = raw()
        second = raw(sourceFile='Вопросы по категориям (310 шт).docx',
                     questionRu='Административный центр провинции Цзянсу, одна из четырех древних столиц Китая.',
                     topic='География и административное устройство')
        forward, _ = merge([first, second], {})
        backward, _ = merge([second, first], {})
        self.assertEqual(json.dumps(forward, ensure_ascii=False, sort_keys=True),
                         json.dumps(backward, ensure_ascii=False, sort_keys=True))


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Прогнать тест и убедиться, что он падает**

Run: `python3 -m unittest test.test_merge -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'merge_bank'`

- [ ] **Step 3: Написать слияние**

```python
# scripts/merge_bank.py
"""Слияние сырых записей в канонический банк."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from normalize import completeness_errors, fragment_pairs, language_errors, normalize_text, option_key

STAGE_ORDER = {'pri': 0, 'shk': 1, 'mun': 2, 'reg': 3, 'zak': 4}


def record_id(occurrence: dict) -> str:
    return f"{occurrence['year']}-{occurrence['stageCode']}-{occurrence['number']}"


def _authority(source_file: str) -> int:
    if source_file.endswith('.pdf'):
        return 3
    for prefix, weight in (('Банк вопросов', 2), ('Вопросы по категориям', 1)):
        if source_file.startswith(prefix):
            return weight
    return 0


def _best_wording(candidates: list[tuple[int, str]]) -> str:
    """Самая авторитетная редакция; при равном авторитете — самая полная."""
    return max(candidates, key=lambda pair: (pair[0], len(pair[1])))[1]


def _group(raw: list[dict]) -> dict[tuple[str, ...], list[dict]]:
    """Дедупликация в два прохода.

    Первый — по набору вариантов. Второй нужен потому, что в источниках есть записи
    с испорченным списком вариантов (у вопроса про восемь кухонь в банке 423 нет
    варианта D, а в сводном сборнике он есть). У таких записей наборы вариантов
    разные, и один проход развёл бы один и тот же вопрос по двум записям.
    """
    by_options: dict[tuple[str, ...], list[dict]] = {}
    for record in raw:
        by_options.setdefault(option_key(record['options']), []).append(record)

    anchors: dict[str, tuple[str, ...]] = {}
    groups: dict[tuple[str, ...], list[dict]] = {}
    for key, members in sorted(by_options.items()):
        texts = {normalize_text(member['questionZh'] or member['questionRu'] or '') for member in members}
        texts.discard('')
        anchor = next((anchors[text] for text in sorted(texts) if text in anchors), key)
        groups.setdefault(anchor, []).extend(members)
        for text in texts:
            anchors.setdefault(text, anchor)
    return groups


def _options_rank(record: dict) -> tuple[int, int]:
    """Полный список вариантов важнее авторитета источника: пустых вариантов быть не должно."""
    filled = sum(1 for option in record['options'] if option.strip())
    return filled, _authority(record['sourceFile'])


def merge(raw: list[dict], translations: dict[str, str]) -> tuple[list[dict], dict]:
    groups = _group(raw)

    bank: list[dict] = []
    report: dict[str, list] = {'conflicts': [], 'untranslated': [], 'dropped': [], 'merged': []}

    for key, members in sorted(groups.items()):
        occurrences = sorted(
            ({'year': m['year'], 'stage': m['stage'], 'stageCode': m['stageCode'],
              'grades': m['grades'], 'number': m['number'],
              'officialKey': m['officialKeyIndex'], 'sourceFile': m['sourceFile']} for m in members),
            key=lambda o: (o['year'], STAGE_ORDER.get(o['stageCode'], 9), o['number']))

        russian = [(_authority(m['sourceFile']), m['questionRu']) for m in members if m['questionRu']]
        chinese = [(_authority(m['sourceFile']), m['questionZh']) for m in members if m['questionZh']]
        question_zh = _best_wording(chinese) if chinese else None

        if russian:
            question_ru = _best_wording(russian)
        elif question_zh and normalize_text(question_zh) in translations:
            question_ru = translations[normalize_text(question_zh)]
        else:
            report['untranslated'].append({'questionZh': question_zh, 'options': members[0]['options']})
            continue

        options_source = max(members, key=_options_rank)
        options = [{'id': f'o{index + 1}', 'zh': text} for index, text in enumerate(options_source['options'])]
        by_text = {normalize_text(option['zh']): option['id'] for option in options}

        keys = {normalize_text(m['options'][m['officialKeyIndex']])
                for m in members if m['officialKeyIndex'] is not None}
        unknown = [key for key in keys if key not in by_text]
        if unknown:
            answer = {'optionId': None, 'state': 'needs-review'}
            report['dropped'].append({'id': record_id(occurrences[0]),
                                      'errors': [f'ключ указывает на вариант вне списка: {unknown}'],
                                      'questionRu': question_ru})
        elif len(keys) > 1:
            answer = {'optionId': None, 'state': 'conflict'}
            report['conflicts'].append({'id': record_id(occurrences[0]), 'variants': sorted(keys)})
        elif keys:
            answer = {'optionId': by_text[keys.pop()], 'state': 'unverified'}
        else:
            answer = {'optionId': None, 'state': 'needs-review'}

        topics = [m['topic'] for m in members if m['topic']]
        errors = language_errors(question_ru, [option['zh'] for option in options])
        errors += completeness_errors(question_ru, question_zh, [option['zh'] for option in options])
        if errors:
            report['dropped'].append({'id': record_id(occurrences[0]), 'errors': errors, 'questionRu': question_ru})
            continue

        if len(members) > 1:
            report['merged'].append({'id': record_id(occurrences[0]), 'count': len(members)})

        bank.append({
            'id': record_id(occurrences[0]),
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
    bank, report = merge(raw, translations)
    (ROOT / 'data/bank.json').write_text(
        json.dumps(bank, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    (ROOT / 'data/review').mkdir(parents=True, exist_ok=True)
    _write_report(report, bank)
    print(f'банк: {len(bank)} записей; отчёт: data/review/merge.md')


if __name__ == '__main__':
    main()
```

- [ ] **Step 4: Прогнать тесты**

Run: `python3 -m unittest test.test_merge -v`
Expected: PASS, 11 тестов

- [ ] **Step 5: Собрать банк и прочитать отчёт**

Run:

```bash
python3 scripts/merge_bank.py
shasum data/bank.json
python3 scripts/merge_bank.py
shasum data/bank.json   # обе суммы обязаны совпасть: слияние детерминировано
sed -n '1,40p' data/review/merge.md
```

Expected: банк в районе 430–450 записей. Разделы «Отброшенные записи» и «Пары „вопрос — обрезок вопроса“» разбираются вручную: для каждой отброшенной записи найти полную редакцию в источниках и дописать её в `data/translations.json` либо поправить парсер, а не ослаблять инвариант.

Одна отброшенная запись законна и останется отброшенной: вопрос «Эта достопримечательность Китая включена в список всемирного наследия ЮНЕСКО…» напечатан в самом бланке ВсОШ 2023-24 с испорченным четвёртым вариантом (`A) 大唐芙蓉园` вместо `D)`, дублирующий третий). Восстановить его не из чего, поэтому он остаётся вне банка с записью в отчёте — это не повод ослаблять проверку. Если захочется вернуть его в тренажёр, недостающий вариант нужно взять из опубликованных материалов оргкомитета и дописать вручную отдельной записью в `data/raw/`.

- [ ] **Step 6: Коммит**

```bash
git add scripts/merge_bank.py data/bank.json data/review/merge.md test/test_merge.py
git commit -m "Слияние источников в канонический банк"
```

---

### Task 10: Рубрикация по семи категориям

**Files:**
- Create: `scripts/taxonomy.py`, `data/taxonomy.json`
- Test: `test/test_taxonomy.py`

**Interfaces:**
- Consumes: `data/bank.json` после Task 9.
- Produces: `assign_topics(bank: list[dict], rules: dict) -> tuple[list[dict], list[dict]]` — банк с проставленными темами и список спорных; отчёт `data/review/taxonomy.md`.

Тема достаётся из базы «310» там, где вопрос совпал (`topicSource: 'categories-310'`). Остальным тема назначается по ключевым словам из `data/taxonomy.json`, и каждая такая метка попадает в отчёт на сверку.

- [ ] **Step 1: Написать падающий тест**

```python
# test/test_taxonomy.py
import json, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from taxonomy import TOPICS, assign_topics


def record(**overrides):
    base = {'id': '2015-16-shk-1', 'topic': None, 'topicSource': 'assigned',
            'questionRu': 'Какой город является крупнейшим портовым городом Китая?',
            'questionZh': None, 'options': [{'id': 'o1', 'zh': '上海'}]}
    base.update(overrides)
    return base


class TaxonomyTest(unittest.TestCase):
    def setUp(self):
        self.rules = json.loads((ROOT / 'data/taxonomy.json').read_text('utf-8'))

    def test_seven_topics_and_no_misc(self):
        self.assertEqual(len(TOPICS), 7)
        self.assertNotIn('Разное', TOPICS)
        self.assertEqual(set(self.rules['topics']), set(TOPICS))

    def test_keeps_topic_that_came_from_categories_310(self):
        bank, disputed = assign_topics(
            [record(topic='Культура, традиции и праздники', topicSource='categories-310')], self.rules)
        self.assertEqual(bank[0]['topic'], 'Культура, традиции и праздники')
        self.assertEqual(disputed, [])

    def test_assigns_topic_by_keywords_and_reports_it(self):
        bank, disputed = assign_topics([record()], self.rules)
        self.assertEqual(bank[0]['topic'], 'География и административное устройство')
        self.assertEqual(bank[0]['topicSource'], 'assigned')
        self.assertEqual(len(disputed), 1)

    def test_russia_questions_go_to_the_intercultural_topic(self):
        bank, _ = assign_topics([record(questionRu='Кто считается основателем российского флота?')], self.rules)
        self.assertEqual(bank[0]['topic'], 'Россия и межкультурный блок')

    def test_every_record_ends_with_a_known_topic(self):
        bank, _ = assign_topics([record(questionRu='Вопрос, не попадающий ни в одно правило вообще?')], self.rules)
        self.assertIn(bank[0]['topic'], TOPICS)


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Прогнать тест и убедиться, что он падает**

Run: `python3 -m unittest test.test_taxonomy -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'taxonomy'`

- [ ] **Step 3: Написать правила рубрикации**

```json
{
  "topics": {
    "География и административное устройство": ["провинц", "город", "река", "гора", "остров", "порт", "climate", "климат", "автономн", "столиц", "СЭЗ", "экономическ зон", "площад", "границ"],
    "Россия и межкультурный блок": ["росси", "русск", "москв", "петербург", "русь", "ссср", "кремл", "советск"],
    "Литература, язык, искусство и философия": ["роман", "поэт", "писател", "иероглиф", "диалект", "живопис", "театр", "философ", "конфуц", "даос", "литератур", "байхуа"],
    "История и государство": ["династ", "император", "революц", "войн", "год произош", "правлен", "党", "госсовет", "внсп", "законодательн", "флаг", "герб", "гимн"],
    "Общество: население, этносы и религии": ["населен", "народност", "национальност", "этнос", "религи", "буддизм", "ислам", "христианств", "демограф"],
    "Экономика, образование, наука и спорт": ["вто", "шос", "экономик", "промышленност", "hsk", "гаокао", "образован", "университет", "изобретен", "медицин", "олимпиад", "спорт", "юан"],
    "Культура, традиции и праздники": ["праздник", "традиц", "обыча", "зодиак", "кухн", "свадьб", "чай", "новый год", "фонар", "дракон", "символ"]
  },
  "default": "Культура, традиции и праздники"
}
```

- [ ] **Step 4: Написать модуль**

```python
# scripts/taxonomy.py
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
        if record.get('topic') and record.get('topicSource') == 'categories-310':
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
```

- [ ] **Step 5: Прогнать тесты и рубрикацию**

Run: `python3 -m unittest test.test_taxonomy -v && python3 scripts/taxonomy.py`
Expected: PASS, 5 тестов; в отчёте порядка 130 строк.

- [ ] **Step 6: Вычитать отчёт**

Просмотреть `data/review/taxonomy.md`, особенно строки с `уверенно = нет`. Спорные метки править в `data/taxonomy.json` (добавляя ключевые слова) и прогонять `python3 scripts/taxonomy.py` заново — правка самого `data/bank.json` руками запрещена.

- [ ] **Step 7: Коммит**

```bash
git add scripts/taxonomy.py data/taxonomy.json data/bank.json data/review/taxonomy.md test/test_taxonomy.py
git commit -m "Рубрикация по семи категориям"
```

---

### Task 11: Логика раунда

**Files:**
- Create: `src/quiz.mjs`
- Test: `test/quiz.test.mjs`

**Interfaces:**
- Produces:
  - `eligible(bank, filters, progress) -> record[]`, где `filters = {topics: string[], years: string[], stages: string[], onlyUnfinished: boolean, onlyVerified: boolean}`
  - `buildRound(bank, filters, progress, size, random) -> record[]`
  - `labelledOptions(record, random) -> {label, optionId, zh}[]`
  - `grade(record, optionId) -> {correct: boolean, answerOptionId: string | null}`

- [ ] **Step 1: Написать падающий тест**

```js
// test/quiz.test.mjs
import assert from 'node:assert/strict';
import test from 'node:test';
import { buildRound, eligible, grade, labelledOptions } from '../src/quiz.mjs';

const record = (id, overrides = {}) => ({
  id,
  topic: 'География и административное устройство',
  questionRu: 'Какой город является крупнейшим портовым городом Китая?',
  options: [
    { id: 'o1', zh: '广州' }, { id: 'o2', zh: '上海' },
    { id: 'o3', zh: '北京' }, { id: 'o4', zh: '西安' },
  ],
  occurrences: [{ year: '2015-16', stage: 'школьный', stageCode: 'shk', number: 56 }],
  answer: { optionId: 'o2', state: 'verified' },
  ...overrides,
});

const NO_FILTERS = { topics: [], years: [], stages: [], onlyUnfinished: false, onlyVerified: false };

test('метки идут A–D по видимому порядку при любом перемешивании', () => {
  const reversed = labelledOptions(record('a'), () => 0.99);
  assert.deepEqual(reversed.map((option) => option.label), ['A', 'B', 'C', 'D']);
  assert.equal(new Set(reversed.map((option) => option.optionId)).size, 4);
});

test('правильность считается по optionId, а не по букве', () => {
  const shuffled = labelledOptions(record('a'), () => 0.99);
  const correct = shuffled.find((option) => option.optionId === 'o2');
  assert.equal(grade(record('a'), correct.optionId).correct, true);
  assert.equal(grade(record('a'), 'o1').correct, false);
});

test('conflict и needs-review в раунд не попадают', () => {
  const bank = [
    record('a'),
    record('b', { answer: { optionId: null, state: 'conflict' } }),
    record('c', { answer: { optionId: null, state: 'needs-review' } }),
    record('d', { answer: { optionId: 'o1', state: 'unverified' } }),
  ];
  assert.deepEqual(eligible(bank, NO_FILTERS, {}).map((r) => r.id), ['a', 'd']);
});

test('«только проверенные» отсекает unverified', () => {
  const bank = [record('a'), record('d', { answer: { optionId: 'o1', state: 'unverified' } })];
  assert.deepEqual(eligible(bank, { ...NO_FILTERS, onlyVerified: true }, {}).map((r) => r.id), ['a']);
});

test('«только непройденные» уважает прогресс', () => {
  const bank = [record('a'), record('b')];
  const progress = { a: { completed: true } };
  assert.deepEqual(eligible(bank, { ...NO_FILTERS, onlyUnfinished: true }, progress).map((r) => r.id), ['b']);
});

test('фильтры по теме, году и этапу складываются', () => {
  const bank = [
    record('a'),
    record('b', { topic: 'Россия и межкультурный блок' }),
    record('c', { occurrences: [{ year: '2024-25', stage: 'региональный', stageCode: 'reg', number: 4 }] }),
  ];
  assert.deepEqual(eligible(bank, { ...NO_FILTERS, topics: ['Россия и межкультурный блок'] }, {}).map((r) => r.id), ['b']);
  assert.deepEqual(eligible(bank, { ...NO_FILTERS, years: ['2024-25'] }, {}).map((r) => r.id), ['c']);
  assert.deepEqual(eligible(bank, { ...NO_FILTERS, stages: ['reg'] }, {}).map((r) => r.id), ['c']);
});

test('раунд не повторяет вопрос и не превышает подходящее множество', () => {
  const bank = [record('a'), record('b'), record('c')];
  const round = buildRound(bank, NO_FILTERS, {}, 10, () => 0.5);
  assert.equal(round.length, 3);
  assert.equal(new Set(round.map((r) => r.id)).size, 3);
});
```

- [ ] **Step 2: Прогнать тест и убедиться, что он падает**

Run: `node --test test/quiz.test.mjs`
Expected: FAIL — `Cannot find module '../src/quiz.mjs'`

- [ ] **Step 3: Написать модуль**

```js
// src/quiz.mjs
const PLAYABLE = new Set(['verified', 'unverified']);
const LABELS = ['A', 'B', 'C', 'D'];

export function eligible(bank, filters, progress) {
  return bank.filter((record) => {
    if (!PLAYABLE.has(record.answer.state) || !record.answer.optionId) return false;
    if (filters.onlyVerified && record.answer.state !== 'verified') return false;
    if (filters.onlyUnfinished && progress[record.id]?.completed) return false;
    if (filters.topics.length && !filters.topics.includes(record.topic)) return false;
    if (filters.years.length && !record.occurrences.some((o) => filters.years.includes(o.year))) return false;
    if (filters.stages.length && !record.occurrences.some((o) => filters.stages.includes(o.stageCode))) return false;
    return true;
  });
}

function shuffled(items, random) {
  const copy = [...items];
  for (let index = copy.length - 1; index > 0; index -= 1) {
    const swap = Math.floor(random() * (index + 1));
    [copy[index], copy[swap]] = [copy[swap], copy[index]];
  }
  return copy;
}

export function buildRound(bank, filters, progress, size, random = Math.random) {
  const pool = eligible(bank, filters, progress);
  return shuffled(pool, random).slice(0, Math.min(size, pool.length));
}

export function labelledOptions(record, random = Math.random) {
  return shuffled(record.options, random).map((option, index) => ({
    label: LABELS[index],
    optionId: option.id,
    zh: option.zh,
  }));
}

export function grade(record, optionId) {
  return { correct: record.answer.optionId === optionId, answerOptionId: record.answer.optionId };
}
```

- [ ] **Step 4: Прогнать тесты**

Run: `node --test test/quiz.test.mjs`
Expected: PASS, 7 тестов

- [ ] **Step 5: Коммит**

```bash
git add src/quiz.mjs test/quiz.test.mjs
git commit -m "Логика раунда: стабильные optionId и метки по видимому порядку"
```

---

### Task 12: Сборка одного HTML

**Files:**
- Create: `src/template.html`, `src/quiz.css`, `src/quiz.ui.js`, `scripts/build_html.py`
- Test: `test/build.test.mjs`, `test/test_build_invariants.py`

**Interfaces:**
- Consumes: `data/bank.json`, `src/template.html`, `src/quiz.css`, `src/quiz.mjs`, `src/quiz.ui.js`, проверки из Task 2, `TOPICS` из Task 10.
- Produces: `dist/lingvostranovedenie-trainer.html`; `build_html.validate(bank) -> list[str]`.

Шаблон содержит три экрана и подставляет четыре места: `/*QUIZ_CSS*/`, `/*QUIZ_ENGINE*/`, `/*QUESTION_BANK*/`, `/*QUIZ_UI*/`. Порядок подстановки важен: банк и движок объявляются раньше обвязки, которая на них ссылается.

- [ ] **Step 1: Написать падающий тест на инварианты сборки**

```python
# test/test_build_invariants.py
import json, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_html import validate


def record(**overrides):
    base = {
        'id': '2015-16-shk-56', 'topic': 'География и административное устройство',
        'questionRu': 'Какой город является крупнейшим портовым городом Китая?',
        'questionZh': '中国最大的港口城市是哪一个？',
        'options': [{'id': 'o1', 'zh': '广州'}, {'id': 'o2', 'zh': '上海'},
                    {'id': 'o3', 'zh': '北京'}, {'id': 'o4', 'zh': '西安'}],
        'occurrences': [{'year': '2015-16', 'stage': 'школьный', 'stageCode': 'shk', 'number': 56}],
        'answer': {'optionId': 'o2', 'state': 'verified'},
        'explanation': {'ru': 'Шанхай (上海) — крупнейший порт мира по контейнерообороту.'},
        'evidence': [{'title': 'Порт Шанхая', 'url': 'https://example.org', 'checkedAt': '2026-09-18'}],
        'wave': 1,
    }
    base.update(overrides)
    return base


class ValidateTest(unittest.TestCase):
    def test_accepts_a_healthy_bank(self):
        self.assertEqual(validate([record()]), [])

    def test_rejects_chinese_question(self):
        self.assertTrue(validate([record(questionRu='中国最大的港口城市是哪一个？')]))

    def test_rejects_cyrillic_option(self):
        broken = record(options=[{'id': 'o1', 'zh': 'Шанхай'}])
        self.assertTrue(validate([broken]))

    def test_rejects_truncated_question(self):
        self.assertTrue(validate([record(questionRu='дминистративный центр провинции Цзянсу')]))

    def test_rejects_answer_pointing_nowhere(self):
        self.assertTrue(validate([record(answer={'optionId': 'o9', 'state': 'verified'})]))

    def test_rejects_verified_without_explanation_or_evidence(self):
        self.assertTrue(validate([record(explanation={'ru': ''})]))
        self.assertTrue(validate([record(evidence=[])]))

    def test_rejects_duplicate_ids(self):
        self.assertTrue(validate([record(), record()]))

    def test_rejects_unknown_topic(self):
        self.assertTrue(validate([record(topic='Разное')]))


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Прогнать тест и убедиться, что он падает**

Run: `python3 -m unittest test.test_build_invariants -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'build_html'`

- [ ] **Step 3: Написать сборщик**

```python
# scripts/build_html.py
"""Проверка инвариантов и сборка одного самодостаточного HTML."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from normalize import completeness_errors, fragment_pairs, language_errors
from taxonomy import TOPICS

TARGET = ROOT / 'dist/lingvostranovedenie-trainer.html'


def validate(bank: list[dict]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for record in bank:
        where = record['id']
        if where in seen:
            errors.append(f'{where}: повторяющийся id')
        seen.add(where)
        options = [option['zh'] for option in record['options']]
        errors += [f'{where}: {message}' for message in language_errors(record['questionRu'], options)]
        errors += [f'{where}: {message}'
                   for message in completeness_errors(record['questionRu'], record.get('questionZh'), options)]
        if record['topic'] not in TOPICS:
            errors.append(f'{where}: тема вне списка семи категорий: {record["topic"]!r}')
        ids = {option['id'] for option in record['options']}
        if record['answer']['optionId'] and record['answer']['optionId'] not in ids:
            errors.append(f'{where}: ответ указывает на несуществующий вариант')
        if record['answer']['state'] == 'verified':
            if not record['explanation']['ru'].strip():
                errors.append(f'{where}: проверенный ответ без пояснения')
            if not record['evidence']:
                errors.append(f'{where}: проверенный ответ без ссылки на источник')
    errors += [f'{left}: формулировка выглядит обрезком {right}' for left, right in
               fragment_pairs([(r['id'], r['questionRu']) for r in bank])]
    return errors


def main() -> None:
    bank = json.loads((ROOT / 'data/bank.json').read_text('utf-8'))
    errors = validate(bank)
    if errors:
        print(f'сборка остановлена, нарушений: {len(errors)}')
        for message in errors[:40]:
            print(' -', message)
        raise SystemExit(1)

    html = (ROOT / 'src/template.html').read_text('utf-8')
    html = html.replace('/*QUIZ_CSS*/', (ROOT / 'src/quiz.css').read_text('utf-8'))
    engine = (ROOT / 'src/quiz.mjs').read_text('utf-8').replace('export ', '')
    html = html.replace('/*QUIZ_ENGINE*/', engine)
    html = html.replace('/*QUESTION_BANK*/', json.dumps(bank, ensure_ascii=False))
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(html, encoding='utf-8')
    verified = sum(1 for record in bank if record['answer']['state'] == 'verified')
    print(f'собрано: {TARGET} ({TARGET.stat().st_size // 1024} КБ), проверено {verified} из {len(bank)}')


if __name__ == '__main__':
    main()
```

- [ ] **Step 4: Прогнать тест инвариантов**

Run: `python3 -m unittest test.test_build_invariants -v`
Expected: PASS, 8 тестов

- [ ] **Step 5: Написать шаблон и стили**

`src/template.html` — три экрана, подстановочные метки и обвязка. Логика берётся из `quiz.mjs`, разметка заполняется на месте:

```html
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Лингвострановедение — тренажёр ВсОШ</title>
<style>/*QUIZ_CSS*/</style>
</head>
<body>
<header><h1>Лингвострановедение</h1><p id="stats"></p></header>

<main>
  <section id="start" class="screen">
    <h2>Новый раунд</h2>
    <div id="topicChips" class="chips"></div>
    <div id="yearChips" class="chips"></div>
    <div id="stageChips" class="chips"></div>
    <label><input type="checkbox" id="onlyUnfinished"> только непройденные</label>
    <label><input type="checkbox" id="onlyVerified"> только проверенные</label>
    <div id="sizes" class="chips"></div>
    <p id="eligibleCount"></p>
    <button id="startRound">Начать раунд</button>
    <button id="openDatabase">База вопросов</button>
  </section>

  <section id="round" class="screen" hidden>
    <p id="roundMeta"></p>
    <h2 id="questionText"></h2>
    <div id="optionList"></div>
    <div id="feedback" hidden>
      <p id="verdict"></p>
      <p id="explanation"></p>
      <ul id="evidence"></ul>
      <p id="unverifiedNote" hidden>Ответ взят из официального ключа, но ещё не перепроверен.</p>
      <button id="nextQuestion">Дальше</button>
    </div>
  </section>

  <section id="database" class="screen" hidden>
    <input id="search" type="search" placeholder="Поиск по русскому тексту">
    <select id="statusFilter">
      <option value="">любой статус</option>
      <option value="verified">проверено</option>
      <option value="unverified">не проверено</option>
      <option value="conflict">расхождение</option>
      <option value="needs-review">нет ответа</option>
    </select>
    <p id="databaseCount"></p>
    <div id="databaseList"></div>
    <button id="backToStart">Назад</button>
  </section>
</main>

<script>
const QUESTION_BANK = /*QUESTION_BANK*/;
/*QUIZ_ENGINE*/
</script>
<script>/*QUIZ_UI*/</script>
</body>
</html>
```

- [ ] **Step 6: Написать обвязку экранов**

`src/quiz.ui.js` подставляется в метку `/*QUIZ_UI*/`. В `build_html.py` в `main()` добавить строку рядом с остальными подстановками:

```python
    html = html.replace('/*QUIZ_UI*/', (ROOT / 'src/quiz.ui.js').read_text('utf-8'))
```

```js
// src/quiz.ui.js
const STORAGE_KEY = 'lingvo-trainer:v1';
const $ = (id) => document.getElementById(id);

const state = {
  filters: { topics: [], years: [], stages: [], onlyUnfinished: false, onlyVerified: false },
  size: 10,
  round: [],
  position: 0,
  correct: 0,
  progress: loadProgress(),
};

function loadProgress() {
  try {
    const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
    return stored.version === 1 && stored.progress ? stored.progress : {};
  } catch {
    return {};
  }
}

function saveProgress() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ version: 1, progress: state.progress }));
  } catch {
    /* приватный режим — прогресс живёт только до перезагрузки */
  }
}

function show(screen) {
  for (const id of ['start', 'round', 'database']) $(id).hidden = id !== screen;
}

function chips(container, values, selected, onToggle) {
  container.innerHTML = '';
  for (const value of values) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = selected.includes(value) ? 'chip chip-on' : 'chip';
    button.textContent = value;
    button.addEventListener('click', () => { onToggle(value); renderStart(); });
    container.append(button);
  }
}

function renderStart() {
  const topics = [...new Set(QUESTION_BANK.map((record) => record.topic))].sort();
  const years = [...new Set(QUESTION_BANK.flatMap((r) => r.occurrences.map((o) => o.year)))].sort();
  const stages = [...new Set(QUESTION_BANK.flatMap((r) => r.occurrences.map((o) => o.stageCode)))].sort();
  const toggle = (key) => (value) => {
    const list = state.filters[key];
    const index = list.indexOf(value);
    if (index === -1) list.push(value); else list.splice(index, 1);
  };
  chips($('topicChips'), topics, state.filters.topics, toggle('topics'));
  chips($('yearChips'), years, state.filters.years, toggle('years'));
  chips($('stageChips'), stages, state.filters.stages, toggle('stages'));
  chips($('sizes'), [5, 10, 20, 50, 'все'], [state.size], (value) => {
    state.size = value === 'все' ? Number.MAX_SAFE_INTEGER : value;
  });

  const pool = eligible(QUESTION_BANK, state.filters, state.progress);
  $('eligibleCount').textContent = pool.length
    ? `Подходит вопросов: ${pool.length}`
    : 'Под текущие фильтры не подходит ни один вопрос — снимите часть ограничений.';
  $('startRound').disabled = pool.length === 0;

  const verified = QUESTION_BANK.filter((r) => r.answer.state === 'verified').length;
  const done = Object.values(state.progress).filter((item) => item.completed).length;
  $('stats').textContent = `Вопросов ${QUESTION_BANK.length} · проверено ${verified} · пройдено ${done}`;
}

function startRound() {
  state.round = buildRound(QUESTION_BANK, state.filters, state.progress, state.size);
  state.position = 0;
  state.correct = 0;
  show('round');
  renderQuestion();
}

function renderQuestion() {
  const record = state.round[state.position];
  if (!record) {
    $('roundMeta').textContent = `Раунд окончен: ${state.correct} из ${state.round.length}`;
    $('questionText').textContent = '';
    $('optionList').innerHTML = '';
    $('feedback').hidden = true;
    renderStart();
    return;
  }
  const first = record.occurrences[0];
  $('roundMeta').textContent =
    `${record.topic} · ${first.year}, ${first.stage} · ${state.position + 1} из ${state.round.length} · верных ${state.correct}`;
  $('questionText').textContent = record.questionRu;
  $('feedback').hidden = true;
  $('optionList').innerHTML = '';
  for (const option of labelledOptions(record)) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'option';
    button.textContent = `${option.label}. ${option.zh}`;
    button.addEventListener('click', () => answer(record, option.optionId));
    $('optionList').append(button);
  }
}

function answer(record, optionId) {
  const verdict = grade(record, optionId);
  const previous = state.progress[record.id] || { attempts: 0, correct: 0 };
  state.progress[record.id] = {
    attempts: previous.attempts + 1,
    correct: previous.correct + (verdict.correct ? 1 : 0),
    completed: true,
    lastCorrect: verdict.correct,
  };
  saveProgress();
  if (verdict.correct) state.correct += 1;

  const right = record.options.find((option) => option.id === verdict.answerOptionId);
  $('verdict').textContent = verdict.correct ? 'Верно' : `Неверно. Правильный ответ: ${right.zh}`;
  $('explanation').textContent = record.explanation.ru;
  $('evidence').innerHTML = '';
  for (const source of record.evidence) {
    const item = document.createElement('li');
    const link = document.createElement('a');
    link.href = source.url;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.textContent = `${source.title} (проверено ${source.checkedAt})`;
    item.append(link);
    $('evidence').append(item);
  }
  $('unverifiedNote').hidden = record.answer.state !== 'unverified';
  $('feedback').hidden = false;
  for (const button of $('optionList').querySelectorAll('button')) button.disabled = true;
}

function renderDatabase() {
  const needle = $('search').value.trim().toLocaleLowerCase('ru');
  const status = $('statusFilter').value;
  const rows = QUESTION_BANK.filter((record) =>
    (!needle || record.questionRu.toLocaleLowerCase('ru').includes(needle)) &&
    (!status || record.answer.state === status));
  $('databaseCount').textContent = `Показано ${rows.length} из ${QUESTION_BANK.length}`;
  $('databaseList').innerHTML = '';
  for (const record of rows) {
    const article = document.createElement('article');
    article.className = 'row';
    const answered = record.options.find((option) => option.id === record.answer.optionId);
    article.innerHTML =
      `<h3>${record.questionRu}</h3>` +
      `<p class="meta">${record.topic} · ${record.occurrences.map((o) => `${o.year} ${o.stage}`).join(' · ')} · ${record.answer.state}</p>` +
      `<p class="zh">${record.options.map((o) => o.zh).join(' · ')}</p>` +
      (answered ? `<p class="answer">Ответ: ${answered.zh}</p>` : '') +
      (record.explanation.ru ? `<p>${record.explanation.ru}</p>` : '') +
      (record.questionZh ? `<p class="zh">${record.questionZh}</p>` : '');
    $('databaseList').append(article);
  }
}

$('startRound').addEventListener('click', startRound);
$('nextQuestion').addEventListener('click', () => { state.position += 1; renderQuestion(); });
$('onlyUnfinished').addEventListener('change', (event) => {
  state.filters.onlyUnfinished = event.target.checked; renderStart();
});
$('onlyVerified').addEventListener('change', (event) => {
  state.filters.onlyVerified = event.target.checked; renderStart();
});
$('openDatabase').addEventListener('click', () => { show('database'); renderDatabase(); });
$('backToStart').addEventListener('click', () => { show('start'); renderStart(); });
$('search').addEventListener('input', renderDatabase);
$('statusFilter').addEventListener('change', renderDatabase);

renderStart();
show('start');
```

- [ ] **Step 7: Написать тест сборки**

```js
// test/build.test.mjs
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFileSync, statSync } from 'node:fs';
import test from 'node:test';

const HTML = new URL('../dist/lingvostranovedenie-trainer.html', import.meta.url);

test('сборка выпускает один файл без внешних ссылок', () => {
  execFileSync('python3', ['scripts/build_html.py'], { cwd: new URL('..', import.meta.url) });
  const html = readFileSync(HTML, 'utf8');
  assert.ok(statSync(HTML).size > 100_000);
  assert.equal(/<script[^>]+src=/.test(html), false, 'внешний скрипт');
  assert.equal(/<link[^>]+href="https?:/.test(html), false, 'внешний стиль');
  assert.ok(html.includes('const QUESTION_BANK = ['), 'банк не встроен');
});

test('в собранном файле вопросы по-русски, а варианты по-китайски', () => {
  const html = readFileSync(HTML, 'utf8');
  const bank = JSON.parse(html.match(/const QUESTION_BANK = (\[.*?\]);\n/s)[1]);
  assert.ok(bank.length > 400);
  for (const record of bank) {
    assert.match(record.questionRu, /[А-Яа-яЁё]/, record.id);
    assert.doesNotMatch(record.questionRu, /[一-鿿]/, record.id);
    for (const option of record.options) assert.doesNotMatch(option.zh, /[А-Яа-яЁё]/, record.id);
  }
});
```

- [ ] **Step 8: Прогнать всё**

Run: `python3 -m unittest discover -s test -v && node --test test/`
Expected: PASS во всех файлах; в `dist/` появился собранный тренажёр.

- [ ] **Step 9: Открыть тренажёр и пройти раунд руками**

Run: `open dist/lingvostranovedenie-trainer.html`
Expected: вопрос по-русски, четыре варианта по-китайски с метками A–D по порядку; после ответа видны пояснение и ссылки; после перезагрузки страницы пройденные вопросы остаются пройденными.

- [ ] **Step 10: Коммит**

```bash
git add src scripts/build_html.py dist test/build.test.mjs test/test_build_invariants.py
git commit -m "Сборка одного самодостаточного HTML с проверкой инвариантов"
```

---

### Task 13: Инструменты волн и первая волна проверки

**Files:**
- Create: `scripts/wave.py`, `data/review/wave-1.md`
- Modify: `data/bank.json` (через скрипт)
- Test: `test/test_wave.py`

**Interfaces:**
- Consumes: `data/bank.json`.
- Produces:
  - `select_wave(bank: list[dict], size: int) -> list[dict]` — очередная партия в порядке приоритета;
  - `apply_results(bank: list[dict], results: list[dict], wave: int) -> tuple[list[dict], list[dict]]` — банк и список расхождений с официальным ключом.

Порядок приоритета: сначала `needs-review` и `conflict`, затем `unverified` по темам. Формат результата проверки — список записей `{id, optionId, explanation, evidence: [{title, url}], note}`.

- [ ] **Step 1: Написать падающий тест**

```python
# test/test_wave.py
import sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from wave import apply_results, select_wave


def record(record_id, state, option_id='o2', topic='География и административное устройство'):
    return {
        'id': record_id, 'topic': topic,
        'questionRu': 'Какой город является крупнейшим портовым городом Китая?',
        'options': [{'id': 'o1', 'zh': '广州'}, {'id': 'o2', 'zh': '上海'}],
        'occurrences': [{'year': '2015-16', 'stage': 'школьный', 'stageCode': 'shk',
                         'number': 56, 'officialKey': 1}],
        'answer': {'optionId': option_id, 'state': state},
        'explanation': {'ru': ''}, 'evidence': [], 'wave': 0,
    }


class SelectWaveTest(unittest.TestCase):
    def test_unanswered_and_conflicting_go_first(self):
        bank = [record('a', 'unverified'), record('b', 'needs-review', None), record('c', 'conflict', None)]
        self.assertEqual([r['id'] for r in select_wave(bank, 2)], ['b', 'c'])

    def test_already_verified_are_not_offered_again(self):
        bank = [record('a', 'verified'), record('b', 'unverified')]
        self.assertEqual([r['id'] for r in select_wave(bank, 5)], ['b'])


class ApplyResultsTest(unittest.TestCase):
    def test_verified_record_gets_explanation_evidence_and_wave(self):
        bank = [record('a', 'unverified')]
        bank, mismatches = apply_results(bank, [{
            'id': 'a', 'optionId': 'o2',
            'explanation': 'Шанхай (上海) — крупнейший порт мира по контейнерообороту; 广州 уступает ему.',
            'evidence': [{'title': 'Порт Шанхая', 'url': 'https://example.org'}], 'note': '',
        }], wave=1)
        self.assertEqual(bank[0]['answer']['state'], 'verified')
        self.assertEqual(bank[0]['wave'], 1)
        self.assertTrue(bank[0]['evidence'][0]['checkedAt'])
        self.assertEqual(mismatches, [])

    def test_result_against_the_official_key_becomes_conflict(self):
        bank = [record('a', 'unverified')]
        bank, mismatches = apply_results(bank, [{
            'id': 'a', 'optionId': 'o1', 'explanation': 'Источники называют другой город.',
            'evidence': [{'title': 'Источник', 'url': 'https://example.org'}], 'note': 'расходится с ключом',
        }], wave=1)
        self.assertEqual(bank[0]['answer']['state'], 'conflict')
        self.assertEqual(len(mismatches), 1)

    def test_result_without_evidence_is_rejected(self):
        bank = [record('a', 'unverified')]
        with self.assertRaises(ValueError):
            apply_results(bank, [{'id': 'a', 'optionId': 'o2', 'explanation': 'Потому что.', 'evidence': [], 'note': ''}], wave=1)


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Прогнать тест и убедиться, что он падает**

Run: `python3 -m unittest test.test_wave -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'wave'`

- [ ] **Step 3: Написать инструмент волн**

```python
# scripts/wave.py
"""Отбор очередной партии на проверку и приём её результатов."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRIORITY = {'needs-review': 0, 'conflict': 1, 'unverified': 2}


def select_wave(bank: list[dict], size: int) -> list[dict]:
    pending = [record for record in bank if record['answer']['state'] in PRIORITY]
    pending.sort(key=lambda record: (PRIORITY[record['answer']['state']], record['topic'] or '', record['id']))
    return pending[:size]


def apply_results(bank: list[dict], results: list[dict], wave: int) -> tuple[list[dict], list[dict]]:
    today = dt.date.today().isoformat()
    by_id = {record['id']: record for record in bank}
    mismatches: list[dict] = []

    for result in results:
        record = by_id[result['id']]
        if not result.get('evidence'):
            raise ValueError(f'{result["id"]}: результат без ссылки на источник')
        if not result.get('explanation', '').strip():
            raise ValueError(f'{result["id"]}: результат без пояснения')

        official = {occurrence['officialKey'] for occurrence in record['occurrences']
                    if occurrence.get('officialKey') is not None}
        official_ids = {record['options'][index]['id'] for index in official if index < len(record['options'])}

        record['explanation'] = {'ru': result['explanation'].strip()}
        record['evidence'] = [{'title': item['title'], 'url': item['url'], 'checkedAt': today}
                              for item in result['evidence']]
        record['wave'] = wave

        if official_ids and result['optionId'] not in official_ids:
            record['answer'] = {'optionId': None, 'state': 'conflict'}
            mismatches.append({'id': record['id'], 'official': sorted(official_ids),
                               'found': result['optionId'], 'note': result.get('note', '')})
        else:
            record['answer'] = {'optionId': result['optionId'], 'state': 'verified'}

    return bank, mismatches


def write_report(wave: int, done: list[dict], mismatches: list[dict]) -> None:
    lines = [f'# Волна проверки {wave}', '',
             f'Проверено вопросов: {len(done)}',
             f'Расхождений с официальным ключом: {len(mismatches)}', '',
             '## Расхождения', '']
    lines += [f"- `{item['id']}`: ключ {item['official']}, источники дают {item['found']} — {item['note']}"
              for item in mismatches] or ['- нет']
    (ROOT / f'data/review/wave-{wave}.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--wave', type=int, required=True)
    parser.add_argument('--size', type=int, default=50)
    parser.add_argument('--results', type=Path, help='JSON с результатами проверки')
    args = parser.parse_args()

    bank = json.loads((ROOT / 'data/bank.json').read_text('utf-8'))
    if args.results is None:
        batch = select_wave(bank, args.size)
        print(json.dumps([{'id': r['id'], 'questionRu': r['questionRu'],
                           'options': r['options'], 'answer': r['answer'],
                           'occurrences': r['occurrences']} for r in batch], ensure_ascii=False, indent=2))
        return

    results = json.loads(args.results.read_text('utf-8'))
    bank, mismatches = apply_results(bank, results, args.wave)
    (ROOT / 'data/bank.json').write_text(
        json.dumps(bank, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    write_report(args.wave, results, mismatches)
    print(f'волна {args.wave}: принято {len(results)}, расхождений {len(mismatches)}')


if __name__ == '__main__':
    main()
```

- [ ] **Step 4: Прогнать тесты**

Run: `python3 -m unittest test.test_wave -v`
Expected: PASS, 5 тестов

- [ ] **Step 5: Отобрать первую партию**

Run: `python3 scripts/wave.py --wave 1 --size 50 > /tmp/wave-1-batch.json && head -40 /tmp/wave-1-batch.json`
Expected: 50 вопросов, первыми — те, у кого нет ключа и у кого ключи разошлись.

- [ ] **Step 6: Проверить каждый вопрос партии**

Для каждого вопроса найти источник, прямо отвечающий на него. Приоритет: официальные сайты (gov.cn, ВСНП, ЮНЕСКО, Росстат, сайты музеев, вузов и оргкомитета ВсОШ) → энциклопедические справочники → прочие. Записать результат в `/tmp/wave-1-results.json`:

```json
[
  {
    "id": "2023-24-shk-138",
    "optionId": "o4",
    "explanation": "Административный центр Цзянсу — 南京 (Нанкин), одна из четырёх древних столиц. 西安 — столица Шэньси, 北京 — столица КНР, 洛阳 — город в Хэнани.",
    "evidence": [{"title": "Народное правительство провинции Цзянсу", "url": "http://www.jiangsu.gov.cn/"}],
    "note": ""
  }
]
```

Правила, которые нельзя ослаблять: вопрос, зависящий от времени, оценивается по году своей олимпиады из `occurrences`; источник, не отвечающий на этот конкретный вопрос, не годится; если источника нет — вопрос в результаты не попадает и остаётся `needs-review` до следующей волны.

- [ ] **Step 7: Принять результаты и пересобрать**

Run:

```bash
python3 scripts/wave.py --wave 1 --results /tmp/wave-1-results.json
python3 -m unittest discover -s test && node --test test/
python3 scripts/build_html.py
```

Expected: отчёт `data/review/wave-1.md` с разделом расхождений; сборка проходит; в шапке тренажёра число проверенных выросло.

- [ ] **Step 8: Коммит**

```bash
git add scripts/wave.py data/bank.json data/review/wave-1.md dist test/test_wave.py
git commit -m "Инструменты волн и первая волна проверки"
```

---

## Дальнейшие волны

Волны 2 и далее повторяют шаги 5–8 задачи 13 с увеличением номера волны. Волна заканчивается коммитом, отчётом и пересборкой. Работа прерывается на любой волне: номер хранится в каждой записи, `select_wave` сам отдаёт следующую партию.

Отдельно, по мере накопления: разобрать расхождения из отчётов волн. Каждое расхождение закрывается либо подтверждением официального ключа, либо решением владельца проекта в пользу источников — и только после этого запись выходит из `conflict`.
