"""Урок книги для чтения: разбор Markdown-файла и проверка формата.

Формат урока описан в book/README.md; спецификация —
docs/superpowers/specs/2026-10-16-culture-reader-design.md.
"""
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

BOOK = Path(__file__).resolve().parents[1] / 'book'
STATUSES = ('draft', 'checked', 'accepted')
SOURCE_KINDS = ('official', 'academic', 'retelling')
HAN = re.compile(r'[一-鿿]')
MARK = re.compile(r'\{([^{}|]+)\|([^{}]+)\}')
TF_RANGE = (4, 5)
QA_RANGE = (3, 5)


class LessonError(Exception):
    pass


@dataclass
class Gloss:
    word: str
    pinyin: str
    ru: str


@dataclass
class Item:
    text: str
    answer: str


@dataclass
class Source:
    kind: str
    title: str
    url: str
    quote: str
    checked_at: str


@dataclass
class Lesson:
    id: str
    block: str
    title: str
    image: str
    status: str
    body: str
    gloss: list[Gloss] = field(default_factory=list)
    tf: list[Item] = field(default_factory=list)
    qa: list[Item] = field(default_factory=list)
    note: str = ''
    sources: list[Source] = field(default_factory=list)
    path: Path | None = None


def _rows(text: str, path: Path, width: int, name: str) -> list[list[str]]:
    rows = []
    for line in text.splitlines():
        if not line.startswith('- '):
            continue
        cells = [c.strip() for c in line[2:].split(' | ')]
        if len(cells) != width:
            raise LessonError(f'{path}: «{name}» — нужно {width} полей через « | », а в строке {len(cells)}: {line}')
        rows.append(cells)
    return rows


def parse_lesson(path: Path) -> Lesson:
    text = path.read_text(encoding='utf-8')
    m = re.match(r'---\n(.*?)\n---\n(.*)', text, re.S)
    if not m:
        raise LessonError(f'{path}: нет заголовка между строками ---')
    meta = {}
    for line in m.group(1).splitlines():
        key, sep, value = line.partition(': ')
        if not sep:
            raise LessonError(f'{path}: строка заголовка без «: »: {line}')
        meta[key.strip()] = value.strip()
    missing = [k for k in ('id', 'block', 'title', 'image', 'status') if k not in meta]
    if missing:
        raise LessonError(f'{path}: в заголовке нет {", ".join(missing)}')
    parts = re.split(r'^## ', m.group(2), flags=re.M)
    lesson = Lesson(meta['id'], meta['block'], meta['title'], meta['image'], meta['status'],
                    parts[0].strip(), path=path)
    for part in parts[1:]:
        head, _, rest = part.partition('\n')
        head = head.strip()
        if head == '生词':
            lesson.gloss = [Gloss(*r) for r in _rows(rest, path, 3, head)]
        elif head in ('判断正误', '回答问题'):
            items = [Item(*r) for r in _rows(rest, path, 2, head)]
            setattr(lesson, 'tf' if head == '判断正误' else 'qa', items)
        elif head == '来源':
            lesson.sources = [Source(*r) for r in _rows(rest, path, 5, head)]
        elif head == '注':
            lesson.note = rest.strip()
        else:
            raise LessonError(f'{path}: неизвестный раздел «## {head}»')
    return lesson


def body_text(lesson: Lesson) -> str:
    """Основной текст без пометок пиньиня, без «原文» и подписи «例句»."""
    lines = [l for l in lesson.body.splitlines()
             if not l.startswith('> ') and l.strip() != '**例句**']
    return MARK.sub(r'\1', '\n'.join(lines))


def count_han(text: str) -> int:
    return len(HAN.findall(text))


def load_blocks(path: Path = BOOK / 'blocks.json') -> list[dict]:
    return json.loads(path.read_text(encoding='utf-8'))


def load_lessons(src: Path = BOOK / 'src') -> list[Lesson]:
    lessons = []
    for block in load_blocks():
        folder = src / block['slug']
        if folder.is_dir():
            lessons += [parse_lesson(p) for p in sorted(folder.glob('*.md'))]
    return lessons


def _in_range(n: int, bounds) -> bool:
    return bounds[0] <= n <= bounds[1]


def validate_lesson(lesson: Lesson, blocks: list[dict]) -> list[str]:
    errors = []
    block = next((b for b in blocks if b['slug'] == lesson.block), None)
    if lesson.path is not None and not re.fullmatch(rf'\d\d-{re.escape(lesson.id)}\.md', lesson.path.name):
        errors.append(f'имя файла {lesson.path.name} не совпадает с id {lesson.id} (нужно NN-{lesson.id}.md)')
    if block is None:
        errors.append(f'блок «{lesson.block}» не из book/blocks.json')
    if lesson.status not in STATUSES:
        errors.append(f'status «{lesson.status}» — допустимы {", ".join(STATUSES)}')
    if not _in_range(len(lesson.tf), TF_RANGE):
        errors.append(f'«判断正误»: {len(lesson.tf)} пунктов, нужно {TF_RANGE[0]}–{TF_RANGE[1]}')
    bad = [i.text for i in lesson.tf if i.answer not in ('对', '错')]
    if bad:
        errors.append(f'«判断正误»: ответ должен быть 对/错 — {"; ".join(bad)}')
    if not _in_range(len(lesson.qa), QA_RANGE):
        errors.append(f'«回答问题»: {len(lesson.qa)} вопросов, нужно {QA_RANGE[0]}–{QA_RANGE[1]}')
    text = body_text(lesson)
    if block is not None:
        if not _in_range(len(lesson.gloss), block['gloss']):
            errors.append(f'«生词»: {len(lesson.gloss)} слов, нужно {block["gloss"][0]}–{block["gloss"][1]}')
        n = count_han(text)
        if not (block['min'] <= n <= block['max']):
            errors.append(f'длина {n} иероглифов, для блока нужно {block["min"]}–{block["max"]}')
    absent = [g.word for g in lesson.gloss
              if '…' not in g.word and g.word not in text and g.word not in lesson.title]
    if absent:
        errors.append(f'слов «生词» нет в тексте: {" ".join(absent)}')
    for s in lesson.sources:
        if s.kind not in SOURCE_KINDS:
            errors.append(f'источник «{s.title}»: kind «{s.kind}» — допустимы {", ".join(SOURCE_KINDS)}')
        if not s.url.startswith(('http://', 'https://')):
            errors.append(f'источник «{s.title}»: ссылка должна начинаться с http(s)://')
        if not re.fullmatch(r'\d{4}-\d\d-\d\d', s.checked_at):
            errors.append(f'источник «{s.title}»: дата проверки «{s.checked_at}» — нужно ГГГГ-ММ-ДД')
    if lesson.status in ('checked', 'accepted') and not any(s.kind in ('official', 'academic') for s in lesson.sources):
        errors.append('нет ни одного официального или академического источника (нужен для status checked/accepted)')
    return errors
