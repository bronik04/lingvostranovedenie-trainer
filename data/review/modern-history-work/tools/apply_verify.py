"""Применить вердикты сверщиков к черновикам: python3 apply_verify.py verify-<часть>.json [...].

Для каждой записи {"table", "row", "verdict", "fix"}: `fix` — поле = новое значение (null убирает
поле), `remove` убирает строку. Черновик строки ищется по id во всех drafts/*.json. Проверяет, что у
каждой строки затронутых черновиков есть вердикт. Копия черновиков до правки — drafts-before-verify/.
"""
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DRAFTS = HERE / 'drafts'


def main() -> None:
    files = {f: json.loads(f.read_text('utf-8')) for f in sorted(DRAFTS.glob('*.json'))}
    backup = HERE / 'drafts-before-verify'
    if not backup.exists():
        shutil.copytree(DRAFTS, backup)
    where = {row['id']: f for f, rows in files.items() for row in rows}
    seen, touched = set(), set()
    for path in sys.argv[1:]:
        for item in json.loads(Path(path).read_text('utf-8')):
            rid = item['row']
            if rid not in where:
                print(f'{path}: нет строки {rid}')
                continue
            f = where[rid]
            touched.add(f)
            seen.add(rid)
            rows = files[f]
            index = next(i for i, r in enumerate(rows) if r['id'] == rid)
            if item['verdict'] == 'remove':
                rows.pop(index)
                print(f'{rid}: убрана')
                continue
            for field, value in (item.get('fix') or {}).items():
                if value is None:
                    rows[index].pop(field, None)
                else:
                    rows[index][field] = value
    for f in touched:
        missing = [r['id'] for r in json.loads((backup / f.name).read_text('utf-8')) if r['id'] not in seen]
        if missing:
            print(f'{f.name}: нет вердикта у {missing}')
        f.write_text(json.dumps(files[f], ensure_ascii=False, indent=2) + '\n', 'utf-8')
    print('применено к', sorted(f.name for f in touched))


if __name__ == '__main__':
    main()
