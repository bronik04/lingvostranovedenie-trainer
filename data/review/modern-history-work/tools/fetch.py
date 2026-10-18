"""Скачивание страниц с кэшем для сборщиков досье «Провинции и города».

    python3 fetch.py <кэш> <имя> <url> [<имя> <url> …]

Сохраняет <кэш>/<имя>.html (исходник, уже в UTF-8; у PDF — <имя>.pdf, текст через pdftotext) и <кэш>/<имя>.txt (текст без разметки, первая
строка — URL). Понимает gzip/deflate/br (curl --compressed) и кодировки GB2312 / GBK / GB18030,
Big5, windows-1251. Ответ не 200 не сохраняется. Уже скачанную страницу не качает (флаг -f — перекачать). Тайм-аут 25 с, два
повтора. В запросах — только обезличенный User-Agent, никаких личных данных.
Кэш — путь относительно этой папки или абсолютный.
"""
import html
import re
import subprocess
import tempfile
import time
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/126.0 Safari/537.36')
ENCODINGS = {'gb2312': 'gb18030', 'gbk': 'gb18030', 'gb18030': 'gb18030', 'big5': 'big5',
             'windows-1251': 'cp1251', 'cp1251': 'cp1251', 'utf-8': 'utf-8', 'utf8': 'utf-8'}


def download(url: str) -> tuple[bytes, str]:
    """Тело и заголовки ответа (заголовки всех редиректов подряд)."""
    error = ''
    with tempfile.TemporaryDirectory() as tmp:
        head, body = Path(tmp) / 'head', Path(tmp) / 'body'
        for attempt in range(3):
            if attempt:
                time.sleep(3)
            done = subprocess.run(['curl', '-sSL', '--compressed', '--max-time', '25', '-A', UA,
                                   '-H', 'Accept-Language: zh-CN,zh;q=0.9,ru;q=0.8,en;q=0.5',
                                   '-D', str(head), '-o', str(body), url], capture_output=True)
            if done.returncode == 0 and body.exists() and body.stat().st_size:
                return body.read_bytes(), head.read_text('latin-1')
            error = done.stderr.decode('utf-8', 'replace').strip()
    raise RuntimeError(error or 'пустой ответ')


def decode(body: bytes, headers: str) -> str:
    found = re.findall(r'charset=["\']?([\w-]+)', headers, re.I)
    found += [m.decode() for m in re.findall(rb'charset=["\']?([\w-]+)', body[:4000], re.I)]
    order = [ENCODINGS.get(name.lower(), name.lower()) for name in found] + ['utf-8', 'gb18030']
    for encoding in order:
        try:
            return body.decode(encoding)
        except (LookupError, UnicodeDecodeError):
            continue
    # на странице испорченный байт: берём кодировку, где меньше всего замен «�»
    tried = []
    for encoding in dict.fromkeys(order):
        try:
            text = body.decode(encoding, 'replace')
        except LookupError:
            continue
        tried.append((text.count('\ufffd'), text))
    return min(tried, key=lambda item: item[0])[1]


def to_text(page: str) -> str:
    text = re.sub(r'(?is)<(script|style|noscript)[^>]*>.*?</\1>', '', page)
    text = re.sub(r'(?is)<!--.*?-->', '', text)
    text = re.sub(r'(?i)<br\s*/?>|</(p|div|li|h\d|tr|td|section|article)>', '\n', text)
    text = html.unescape(re.sub(r'<[^>]+>', '', text)).replace('\xa0', ' ')
    return '\n'.join(line.strip() for line in text.splitlines() if line.strip())


def main() -> None:
    args = sys.argv[1:]
    force = '-f' in args
    args = [a for a in args if a != '-f']
    if len(args) < 3 or len(args) % 2 == 0:
        sys.exit(__doc__)
    cache = Path(args[0]) if Path(args[0]).is_absolute() else HERE / args[0]
    cache.mkdir(parents=True, exist_ok=True)
    for name, url in zip(args[1::2], args[2::2]):
        target = cache / f'{name}.txt'
        if target.exists() and not force:
            print(f'{name}: из кэша, {len(target.read_text("utf-8"))} знаков')
            continue
        try:
            body, headers = download(url)
        except RuntimeError as error:
            print(f'{name}: НЕ СКАЧАНО — {error}')
            continue
        status = re.findall(r'HTTP/\S+ (\d+)', headers)
        if status and status[-1] != '200':
            print(f'{name}: НЕ СОХРАНЕНО — HTTP {status[-1]}')
            continue
        if body[:5] == b'%PDF-':
            pdf = cache / f'{name}.pdf'
            pdf.write_bytes(body)
            done = subprocess.run(['pdftotext', '-layout', str(pdf), '-'], capture_output=True)
            text = '\n'.join(line.strip() for line in done.stdout.decode('utf-8', 'replace').splitlines()
                             if line.strip())
        else:
            page = decode(body, headers)
            text = to_text(page)
            (cache / f'{name}.html').write_text(page, 'utf-8')
        target.write_text(url + '\n' + text, 'utf-8')
        code = status[-1] if status else '?'
        warn = '' if code == '200' and len(text) > 300 else '  ← проверь: мало текста или не 200'
        print(f'{name}: HTTP {code}, {len(body)} байт, текста {len(text)} знаков{warn}')


if __name__ == '__main__':
    main()
