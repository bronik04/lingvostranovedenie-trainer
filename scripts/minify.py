"""Безопасная минификация CSS/JS перед встраиванием в готовый HTML.

Только снятие комментариев и лишних пробелов — без переименования переменных
и без склейки строк, чтобы не рисковать поведением проверенного тренажёра.
"""

from __future__ import annotations

import re

CSS_COMMENT = re.compile(r'/\*.*?\*/', re.S)
CSS_WHITESPACE = re.compile(r'\s+')
CSS_PUNCTUATION = re.compile(r'\s*([{}:;,])\s*')


def minify_css(css: str) -> str:
    css = CSS_COMMENT.sub('', css)
    css = CSS_WHITESPACE.sub(' ', css)
    css = CSS_PUNCTUATION.sub(r'\1', css)
    css = css.replace(';}', '}')
    return css.strip()


def minify_js(js: str) -> str:
    """Снимает `//` и `/* */` комментарии, не трогая содержимое строк и шаблонных
    литералов (в кавычки может быть завёрнут URL с `//` или текст, похожий на
    комментарий, — его нельзя вырезать)."""
    out: list[str] = []
    i, n = 0, len(js)
    while i < n:
        ch = js[i]
        if ch in ("'", '"', '`'):
            quote = ch
            start = i
            i += 1
            while i < n:
                if js[i] == '\\':
                    i += 2
                    continue
                if js[i] == quote:
                    i += 1
                    break
                i += 1
            out.append(js[start:i])
            continue
        if js[i:i + 2] == '//':
            while i < n and js[i] != '\n':
                i += 1
            continue
        if js[i:i + 2] == '/*':
            end = js.find('*/', i + 2)
            i = end + 2 if end != -1 else n
            continue
        out.append(ch)
        i += 1
    return ''.join(out)
