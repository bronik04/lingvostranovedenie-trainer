"""Перерисовать site-assets/og-image.jpg из site-assets/og-image.html.

Запускается вручную после правки исходника, в сборку и CI не входит: нужен
установленный Google Chrome, а картинка меняется редко.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'site-assets/og-image.html'
TARGET = ROOT / 'site-assets/og-image.jpg'
CHROME_CANDIDATES = [
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    'google-chrome', 'google-chrome-stable', 'chromium',
]


def find_chrome() -> str:
    for candidate in CHROME_CANDIDATES:
        path = shutil.which(candidate) or (candidate if Path(candidate).exists() else None)
        if path:
            return path
    raise SystemExit('не найден Google Chrome или Chromium')


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        png = Path(tmp) / 'og-image.png'
        # код выхода не проверяется: на части macOS Chrome без окна падает при закрытии,
        # уже записав снимок; признак успеха — сам файл снимка
        run = subprocess.run([
            find_chrome(), '--headless', '--disable-gpu', '--hide-scrollbars',
            '--force-device-scale-factor=1', '--window-size=1200,630',
            f'--screenshot={png}', SOURCE.as_uri(),
        ], capture_output=True, text=True)
        if not png.exists() or png.stat().st_size == 0:
            raise SystemExit(f'Chrome не сделал снимок (код {run.returncode}):\n{run.stderr[-2000:]}')
        # sips есть на любом macOS; на Linux подойдёт ImageMagick
        if shutil.which('sips'):
            subprocess.run(['sips', '-s', 'format', 'jpeg', '-s', 'formatOptions', '88',
                            str(png), '--out', str(TARGET)], check=True, capture_output=True)
        else:
            subprocess.run(['convert', str(png), '-quality', '88', str(TARGET)], check=True)
    print(f'готово: {TARGET} ({TARGET.stat().st_size // 1024} КБ)')


if __name__ == '__main__':
    main()
