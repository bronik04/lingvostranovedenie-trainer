"""Уровень языка урока: разбор на слова (jieba), сверка с HSK 2.0 и решение, где ставить пиньинь.

Правила — docs/superpowers/specs/2026-10-16-culture-reader-design.md, раздел «Как проверяется»:
знакомы слова HSK 1–4; у слова выше HSK 4 и у имени пиньинь при первом появлении в уроке.
Пиньинь берётся из ручной пометки {слово|pinyin}, из «生词» или из списка HSK 5–6; слово вне
HSK без пиньиня — ошибка.
"""
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

import jieba

from book_lesson import BOOK, MARK, Lesson

jieba.setLogLevel(logging.WARNING)

HAN = re.compile(r'[一-鿿]')
# Многозначные иероглифы: правило «уже был в слове с пиньинем» на них не распространяется
# (藏 в 西藏 — zàng, в 藏药 — cáng). Одиночное слово HSK 5–6 пометки требует всегда.
POLYPHONES = frozenset('长行重还得了着调传好干种便藏几朝都为相觉没地乐少只数难教分当应假空背'
                       '倒圈称露嚷薄曾会处冲差降散似量缝扎折卷弹奔担挑劲落血削恶尽')
# Многозначные иероглифы, второе чтение которых ученик HSK 4 обычно не знает (当成 — dàng,
# 背着 — bēi): если такой стоит в слове вне HSK, разобранном на части, нужна пометка.
# Базовые 地/着/得/了/还/长 ученик читает в обоих чтениях — их здесь нет.
RARE_READINGS = frozenset('当藏调传倒重朝背数难降散似缝扎折卷弹奔担挑劲削恶尽称露嚷薄曾冲量')
FORCE_FREQ = 10 ** 6


@dataclass
class Vocab:
    level: dict[str, int]
    pinyin: dict[str, str]


@dataclass
class Run:
    text: str
    pinyin: str | None = None


@dataclass
class Block:
    kind: str  # p | h3 | quote | label | examples
    runs: list[Run] | None = None
    items: list[list[Run]] | None = None
    text: str = ''


@dataclass
class Annotated:
    lesson: Lesson
    blocks: list[Block]
    errors: list[str] = field(default_factory=list)
    hsk5: list[str] = field(default_factory=list)
    hsk6: list[str] = field(default_factory=list)


def load_vocab(hsk_dir: Path = BOOK / 'hsk') -> Vocab:
    level, pinyin = {}, {}
    for name in ('hsk20.tsv', 'extra.tsv'):
        path = hsk_dir / name
        if not path.exists():
            continue
        for line in path.read_text(encoding='utf-8').splitlines():
            if not line.strip() or line.startswith('#'):
                continue
            word, py, lv = line.split('\t')[:3]
            if word not in level or int(lv) < level[word]:
                level[word], pinyin[word] = int(lv), py
    fixes = hsk_dir / 'fixes.tsv'  # исправленные чтения: в колодах Anki бывают опечатки (从此 cōngcǐ)
    if fixes.exists():
        for line in fixes.read_text(encoding='utf-8').splitlines():
            if line.strip() and not line.startswith('#'):
                word, py = line.split('\t')[:2]
                pinyin[word] = py
    return Vocab(level, pinyin)


_TOKENIZER = None


def _tokenizer() -> 'jieba.Tokenizer':
    global _TOKENIZER
    if _TOKENIZER is None:
        _TOKENIZER = jieba.Tokenizer()
        _TOKENIZER.initialize()
    return _TOKENIZER


def _merge(runs: list[Run]) -> list[Run]:
    out: list[Run] = []
    for r in runs:
        if out and r.pinyin is None and out[-1].pinyin is None:
            out[-1] = Run(out[-1].text + r.text)
        else:
            out.append(r)
    return out


class _Annotator:
    def __init__(self, lesson: Lesson, vocab: Vocab, tokenizer):
        self.vocab = vocab
        self.tok = tokenizer
        self.gloss = {g.word: g.pinyin for g in lesson.gloss if '…' not in g.word}
        self.marked = {w for w, _ in MARK.findall(lesson.body)}
        self.shown: set[str] = set()
        self.flagged: set[str] = set()
        self.errors: list[str] = []
        self.hsk5: list[str] = []
        self.hsk6: list[str] = []

    def error(self, word: str, message: str) -> None:
        if word not in self.flagged:
            self.flagged.add(word)
            self.errors.append(f'{word}: {message}')

    def char_shown(self, char: str) -> bool:
        """Иероглиф уже был в слове с пиньинем в этом уроке (射 после 射箭)."""
        return len(char) == 1 and char not in POLYPHONES and any(char in w for w in self.shown)

    def known(self, piece: str) -> bool:
        level = self.vocab.level.get(piece, 9)
        # часть — слово HSK 1–4 или многосложное HSK 5–6 (у одиночного чтение из списка ненадёжно)
        return (level <= 4 or (level <= 6 and len(piece) > 1) or piece in self.shown
                or piece in self.gloss or piece in self.marked or self.char_shown(piece))

    def split(self, token: str) -> list[str] | None:
        """Жадное деление слева на известные слова; None — если не делится."""
        pieces, i = [], 0
        while i < len(token):
            for size in range(min(6, len(token) - i), 0, -1):
                if self.known(token[i:i + size]):
                    pieces.append(token[i:i + size])
                    i += size
                    break
            else:
                return None
        return pieces

    def word(self, token: str) -> list[Run]:
        if not HAN.search(token) or token in self.shown:
            return [Run(token)]
        if token in self.gloss:
            self.shown.add(token)
            return [Run(token, self.gloss[token])]
        if token in self.marked:
            self.shown.add(token)
            self.error(token, 'первое появление без пиньиня — поставьте пометку здесь')
            return [Run(token)]
        lv = self.vocab.level.get(token)
        if (lv is not None and lv <= 4) or self.char_shown(token):
            return [Run(token)]
        if lv is not None:
            return [self.upper(token, lv)]
        pieces = self.split(token)
        if pieces and len(pieces) > 1:
            risky = [p for p in pieces if len(p) == 1 and p in RARE_READINGS and p not in self.shown]
            if risky:  # 当成: 当 здесь dàng, а ученик знает dāng
                self.shown.add(token)
                self.error(token, f'многозначный иероглиф {"、".join(risky)} в слове вне HSK: поставьте {{{token}|…}}')
                return [Run(token)]
            return [r for p in pieces for r in self.word(p)]
        self.error(token, 'нет пиньиня (слово вне HSK) — поставьте {слово|pinyin} или внесите в «生词»')
        return [Run(token)]

    def upper(self, token: str, lv: int) -> Run:
        self.shown.add(token)
        (self.hsk5 if lv == 5 else self.hsk6).append(token)
        if len(token) == 1:
            kind = 'многозначный иероглиф' if token in POLYPHONES else 'одиночный иероглиф HSK 5–6'
            self.error(token, f'{kind}: чтение из списка ненадёжно, поставьте {{{token}|…}} или внесите в «生词»')
            return Run(token)
        return Run(token, self.vocab.pinyin.get(token) or None)

    def runs(self, text: str) -> list[Run]:
        out: list[Run] = []
        pos = 0
        for m in MARK.finditer(text):
            out += self.plain(text[pos:m.start()])
            w, py = m.groups()
            out.append(Run(w) if w in self.shown else Run(w, py))
            self.shown.add(w)
            pos = m.end()
        out += self.plain(text[pos:])
        return _merge(out)

    def plain(self, text: str) -> list[Run]:
        return [r for t in self.tok.lcut(text) for r in self.word(t)]


def _blocks(body: str, a: _Annotator) -> list[Block]:
    blocks = []
    for chunk in re.split(r'\n\s*\n', body.strip()):
        chunk = chunk.strip()
        if not chunk:
            continue
        if chunk.startswith('### '):
            blocks.append(Block('h3', runs=a.runs(chunk[4:].strip())))
        elif chunk.startswith('> '):
            blocks.append(Block('quote', text='\n'.join(l[2:] if l.startswith('> ') else l
                                                         for l in chunk.splitlines())))
        elif chunk == '**例句**':
            blocks.append(Block('label', text='例句'))
        elif re.match(r'\d+\. ', chunk):
            blocks.append(Block('examples', items=[a.runs(re.sub(r'^\d+\. ', '', l))
                                                   for l in chunk.splitlines() if l.strip()]))
        else:
            blocks.append(Block('p', runs=a.runs(chunk.replace('\n', ''))))
    return blocks


def annotate(lesson: Lesson, vocab: Vocab) -> Annotated:
    tok = _tokenizer()
    a = _Annotator(lesson, vocab, tok)
    words = a.marked | set(a.gloss)
    saved = {w: tok.FREQ.get(w, 0) for w in words}
    total = tok.total
    try:
        for w in words:
            tok.add_word(w, max(saved[w], FORCE_FREQ))
        blocks = _blocks(lesson.body, a)
    finally:
        for w, freq in saved.items():
            if freq:
                tok.add_word(w, freq)
            else:
                tok.del_word(w)
        tok.total = total
    return Annotated(lesson, blocks, a.errors, a.hsk5, a.hsk6)
