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
