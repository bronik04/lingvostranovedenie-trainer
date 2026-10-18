"""Сборка черновика части из rows.py со сверкой каждой цитаты.

    python3 build.py <rows.py> <черновик.json>

rows.py задаёт CACHE (папка кэша части, относительно этой папки) и ROWS — список строк в формате
досье. У каждого источника, кроме обычных полей (title, url, quote, authority), — поле `page`:
имя страницы в кэше (`hubei-xinhua` → <CACHE>/hubei-xinhua.txt) или путь с «/» относительно этой
папки (`common/gov/gov-taiwan`). build.py:
- проверяет, что страница скачана и её URL (первая строка .txt) совпадает с `url` источника;
- ищет цитату дословно (quote.py: без пробелов, NFKC, кавычки и тире приводятся к одному виду);
- убирает `page`, ставит `checkedAt` (сегодня), если его нет;
- источник с несошедшейся цитатой или чужой страницей в черновик НЕ пишет и печатает почему;
- печатает строки, у которых осталось меньше двух источников;
- считает слова цитат по url (words.py): больше 25 слов на одну публикацию — предупреждение
  (общий счёт по всем черновикам — check_rows.py).
Потом — check_rows.py.
"""
import datetime
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from quote import find  # noqa: E402
from words import LIMIT, count  # noqa: E402

TODAY = datetime.date.today().isoformat()


def load_rows(path: Path):
    spec = importlib.util.spec_from_file_location('rows', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.CACHE, module.ROWS


def page_file(cache: str, page: str) -> Path:
    return HERE / f'{page}.txt' if '/' in page else HERE / cache / f'{page}.txt'


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    cache, rows = load_rows(Path(sys.argv[1]).resolve())
    problems, out = [], []
    for row in rows:
        kept = []
        for index, source in enumerate(row.get('sources', []), start=1):
            where = f'{row.get("id")} источник {index}'
            source = dict(source)
            page = source.pop('page', None)
            if not page:
                problems.append(f'{where}: нет поля page — не с чем сверить цитату')
                continue
            file = page_file(cache, page)
            if not file.exists():
                problems.append(f'{where}: страница {file.relative_to(HERE)} не скачана')
                continue
            text = file.read_text('utf-8')
            url = text.split('\n', 1)[0].strip()
            if url.rstrip('/') != source.get('url', '').rstrip('/'):
                problems.append(f'{where}: url источника {source.get("url")} ≠ url страницы {url}')
                continue
            ok, fragment = find(text, source.get('quote', ''))
            if not ok:
                problems.append(f'{where}: цитаты нет дословно; похожее: {fragment[:120]!r}')
                continue
            source.setdefault('checkedAt', TODAY)
            kept.append(source)
        row = {**row, 'sources': kept}
        if len(kept) < 2:
            problems.append(f'{row.get("id")}: подтверждённых источников {len(kept)} — нужно два')
        out.append(row)
    per_url = {}
    for row in out:
        for source in row['sources']:
            per_url[source['url']] = per_url.get(source['url'], 0) + count(source.get('quote', ''))
    problems += [f'цитаты с {url}: {n} слов — больше {LIMIT}, сократи' for url, n in per_url.items() if n > LIMIT]
    Path(sys.argv[2]).write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n', 'utf-8')
    print(f'строк: {len(out)}, записано в {sys.argv[2]}')
    print('\n'.join(problems) if problems else 'все цитаты сошлись')


if __name__ == '__main__':
    main()
