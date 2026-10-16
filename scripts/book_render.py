"""Книга для чтения: вёрстка уроков в XHTML, сборка PDF (Google Chrome без окна) и EPUB 3."""
import shutil
import subprocess
import tempfile
import uuid
import zipfile
from datetime import datetime, timezone
from html import escape
from pathlib import Path

from book_lesson import BOOK
from book_level import Annotated, Block, Run

TITLE = '中国文化故事'
SUBTITLE = 'Мифы, легенды, чэнъюй и культура Китая · HSK 4+'
XHTML_HEAD = ('<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE html>\n'
              '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" '
              'lang="zh" xml:lang="zh">\n<head><meta charset="utf-8"/><title>{title}</title>'
              '<link rel="stylesheet" href="style.css"/></head>\n<body>\n')
HOWTO = [
    'Каждый урок — текст по-китайски для тех, кто знает слова HSK 1–4.',
    'Над словами сложнее HSK 4 и над именами при первом появлении в уроке стоит пиньинь; дальше слово идёт без него.',
    'Самые нужные слова урока собраны в рамке «生词» с переводом на русский.',
    'После текста — задания «判断正误» (верно или нет) и «回答问题» (ответьте на вопросы). Ключи — в конце книги.',
    'Мелким шрифтом в конце урока — примечание по-русски: другие версии легенды, даты, связь с олимпиадными темами.',
]
MEDIA = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp'}


def _runs(runs: list[Run]) -> str:
    return ''.join(f'<ruby>{escape(r.text)}<rt>{escape(r.pinyin)}</rt></ruby>' if r.pinyin else escape(r.text)
                   for r in runs)


def _block(b: Block) -> str:
    if b.kind == 'h3':
        return f'<h3>{_runs(b.runs)}</h3>'
    if b.kind == 'quote':
        return f'<blockquote>{escape(b.text)}</blockquote>'
    if b.kind == 'label':
        return f'<p class="label">{escape(b.text)}</p>'
    if b.kind == 'examples':
        return '<ol class="examples">' + ''.join(f'<li>{_runs(item)}</li>' for item in b.items) + '</ol>'
    return f'<p>{_runs(b.runs)}</p>'


def _image(image: str, root: Path, img_base: str, alt: str) -> str:
    if (root / image).exists():
        return f'<figure class="img"><img src="{escape(img_base + image)}" alt="{escape(alt)}"/></figure>'
    return f'<div class="img-placeholder">иллюстрация · {escape(image)}</div>'


def lesson_xhtml(a: Annotated, block: dict, root: Path, draft_mark: bool, img_base: str = '') -> str:
    l = a.lesson
    parts = [f'<section class="lesson" id="{escape(l.id)}">',
             f'<p class="block">{escape(block["ru"])}</p>',
             f'<h1>{escape(l.title)}</h1>']
    if draft_mark:
        parts.append('<p class="draft">черновик</p>')
    parts.append(_image(l.image, root, img_base, l.title))
    parts += [_block(b) for b in a.blocks]
    gloss = ''.join(f'<div><b>{escape(g.word)}</b> <i>{escape(g.pinyin)}</i> — {escape(g.ru)}</div>' for g in l.gloss)
    parts.append(f'<div class="box"><h2>生词</h2><div class="gloss">{gloss}</div></div>')
    tf = ''.join(f'<li>{n}) ☐ {escape(i.text)}</li>' for n, i in enumerate(l.tf, 1))
    parts.append(f'<div class="box ex"><h2>判断正误</h2><ol class="tf">{tf}</ol></div>')
    qa = ''.join(f'<li>{escape(i.text)}</li>' for i in l.qa)
    parts.append(f'<div class="box ex"><h2>回答问题</h2><ol>{qa}</ol></div>')
    if l.note:
        parts.append(f'<div class="note">{escape(l.note)}</div>')
    parts.append('</section>')
    return '\n'.join(parts)


def block_xhtml(block: dict) -> str:
    return (f'<section class="block-title" id="block-{escape(block["slug"])}">'
            f'<h1>{escape(block["zh"])}</h1><p>{escape(block["ru"])}</p></section>')


def _grouped(annotated: list[Annotated], blocks: list[dict]):
    for block in blocks:
        items = [a for a in annotated if a.lesson.block == block['slug']]
        if items:
            yield block, items


def front_xhtml(annotated: list[Annotated], blocks: list[dict], root: Path, drafts: bool, img_base: str = '') -> str:
    cover = (f'<img src="{escape(img_base)}img/cover.png" alt="{TITLE}"/>' if (root / 'img' / 'cover.png').exists()
             else f'<h1>{TITLE}</h1><p>{escape(SUBTITLE)}</p>')
    if drafts:
        cover += '<p class="draft">черновик</p>'
    toc = ''.join(
        f'<li><p class="toc-block">{escape(b["zh"])} · {escape(b["ru"])}</p><ol>'
        + ''.join(f'<li>{escape(a.lesson.title)}</li>' for a in items) + '</ol></li>'
        for b, items in _grouped(annotated, blocks))
    howto = ''.join(f'<p>{escape(p)}</p>' for p in HOWTO)
    return (f'<section class="cover">{cover}</section>'
            f'<section class="toc"><h2>目录 · Содержание</h2><ol>{toc}</ol></section>'
            f'<section class="howto"><h2>Как читать эту книгу</h2>{howto}</section>')


def key_xhtml(annotated: list[Annotated]) -> str:
    parts = ['<section class="key" id="key"><h1>答案 · Ключи</h1>']
    for a in annotated:
        l = a.lesson
        tf = '；'.join(f'{i}) {item.answer}' for i, item in enumerate(l.tf, 1))
        qa = ''.join(f'<li>{escape(item.answer)}</li>' for item in l.qa)
        parts.append(f'<h3>{escape(l.title)}</h3><p>判断正误：{escape(tf)}</p><ol>{qa}</ol>')
    parts.append('</section>')
    return '\n'.join(parts)


def book_html(annotated: list[Annotated], blocks: list[dict], root: Path = BOOK, drafts: bool = False,
              img_base: str = '../') -> str:
    css = (root / 'style.css').read_text(encoding='utf-8') if (root / 'style.css').exists() \
        else (BOOK / 'style.css').read_text(encoding='utf-8')
    body = [front_xhtml(annotated, blocks, root, drafts, img_base)]
    for block, items in _grouped(annotated, blocks):
        body.append(block_xhtml(block))
        body += [lesson_xhtml(a, block, root, a.lesson.status != 'accepted', img_base) for a in items]
    body.append(key_xhtml(annotated))
    return (f'<!doctype html>\n<html lang="zh"><head><meta charset="utf-8"/><title>{TITLE}</title>'
            f'<style>{css}</style></head>\n<body>\n' + '\n'.join(body) + '\n</body></html>\n')


def chrome_path() -> str | None:
    mac = Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
    if mac.exists():
        return str(mac)
    return shutil.which('google-chrome') or shutil.which('google-chrome-stable') or shutil.which('chromium')


def write_pdf(html_path: Path, pdf_path: Path) -> None:
    chrome = chrome_path()
    if chrome is None:
        raise RuntimeError('для PDF нужен Google Chrome')
    profile = tempfile.mkdtemp(prefix='book-chrome-')
    try:
        subprocess.run([chrome, '--headless=new', '--disable-gpu', '--no-pdf-header-footer',
                        f'--user-data-dir={profile}', f'--print-to-pdf={pdf_path.resolve()}',
                        html_path.resolve().as_uri()], check=True, capture_output=True, timeout=300)
    finally:
        shutil.rmtree(profile, ignore_errors=True)


def _doc(title: str, body: str) -> str:
    return XHTML_HEAD.format(title=escape(title)) + body + '\n</body>\n</html>\n'


def write_epub(annotated: list[Annotated], blocks: list[dict], out: Path, root: Path = BOOK,
               drafts: bool = False) -> None:
    docs: list[tuple[str, str, str]] = [('front', 'front.xhtml', _doc(TITLE, front_xhtml(annotated, blocks, root, drafts)))]
    nav_items = []
    for block, items in _grouped(annotated, blocks):
        name = f'block-{block["slug"]}.xhtml'
        docs.append((f'block-{block["slug"]}', name, _doc(block['zh'], block_xhtml(block))))
        sub = []
        for a in items:
            lname = f'lesson-{a.lesson.id}.xhtml'
            docs.append((f'lesson-{a.lesson.id}', lname,
                         _doc(a.lesson.title, lesson_xhtml(a, block, root, a.lesson.status != 'accepted'))))
            sub.append(f'<li><a href="{lname}">{escape(a.lesson.title)}</a></li>')
        nav_items.append(f'<li><a href="{name}">{escape(block["zh"])} · {escape(block["ru"])}</a><ol>{"".join(sub)}</ol></li>')
    docs.append(('key', 'key.xhtml', _doc('答案', key_xhtml(annotated))))
    nav_items.append('<li><a href="key.xhtml">答案 · Ключи</a></li>')
    nav = _doc('目录', f'<nav epub:type="toc" id="toc"><h1>目录</h1><ol>{"".join(nav_items)}</ol></nav>')

    images = sorted(p for p in (root / 'img').glob('*') if p.suffix.lower() in MEDIA) if (root / 'img').is_dir() else []
    book_id = uuid.uuid5(uuid.NAMESPACE_URL, 'lingvostranovedenie-trainer/book/' + TITLE)
    modified = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    manifest = ['<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
                '<item id="css" href="style.css" media-type="text/css"/>']
    manifest += [f'<item id="{i}" href="{n}" media-type="application/xhtml+xml"/>' for i, n, _ in docs]
    manifest += [f'<item id="img-{k}" href="img/{escape(p.name)}" media-type="{MEDIA[p.suffix.lower()]}"/>'
                 for k, p in enumerate(images)]
    spine = ''.join(f'<itemref idref="{i}"/>' for i, _, _ in docs)
    opf = ('<?xml version="1.0" encoding="utf-8"?>\n'
           '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid" xml:lang="zh">'
           '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">'
           f'<dc:identifier id="bookid">urn:uuid:{book_id}</dc:identifier><dc:title>{TITLE}</dc:title>'
           f'<dc:language>zh</dc:language><meta property="dcterms:modified">{modified}</meta></metadata>'
           f'<manifest>{"".join(manifest)}</manifest><spine>{spine}</spine></package>\n')
    container = ('<?xml version="1.0" encoding="utf-8"?>\n'
                 '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
                 '<rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>'
                 '</rootfiles></container>\n')
    css = (root / 'style.css') if (root / 'style.css').exists() else BOOK / 'style.css'

    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, 'w') as z:
        z.writestr(zipfile.ZipInfo('mimetype'), 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
        z.writestr('META-INF/container.xml', container, compress_type=zipfile.ZIP_DEFLATED)
        z.writestr('OEBPS/content.opf', opf, compress_type=zipfile.ZIP_DEFLATED)
        z.writestr('OEBPS/nav.xhtml', nav, compress_type=zipfile.ZIP_DEFLATED)
        z.writestr('OEBPS/style.css', css.read_text(encoding='utf-8'), compress_type=zipfile.ZIP_DEFLATED)
        for _, name, text in docs:
            z.writestr(f'OEBPS/{name}', text, compress_type=zipfile.ZIP_DEFLATED)
        for p in images:
            z.write(p, f'OEBPS/img/{p.name}', compress_type=zipfile.ZIP_DEFLATED)
