"""Проверка черновиков досье «История XIX–XX веков».

    python3 check_rows.py [<файл со строками> <таблица>]

Черновики всех частей из drafts/ подставляются в свои таблицы по началу имени файла
(`drafts/ev-*.json` → events, `drafts/fig-*.json` → figures, `drafts/tr-*.json` → treaties), чтобы
проверялись ссылки ref/from и уникальность id. Файл вне drafts/ добавляется к таблице <таблица>.
Проверяет:
- формат досье (`validate_dossier` проекта): ячейки, подписи ≤ 90 знаков, два источника с цитатой;
- ссылки ref/from (внутри досье и в другие досье: dynasties, holidays, literature, provinces…);
- id в `olympiad` — есть ли такие вопросы в банке;
- одинаковый текст ячейки в колонке — одинаковая подпись (во всех частях);
- правила этого досье: префиксы id, значения country и kind, короткие русские названия, вид года;
- бюджет цитат: не больше 25 слов на одну публикацию (url) по всем черновикам вместе;
- каких ячеек ещё не хватает встраиваемым вопросам (embed-targets.json).
Ошибки ссылок на строки другой, ещё не собранной части допустимы — их сведу при сборке.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path('/Users/bronik04/Documents/Projects/lingvostranovedenie-trainer/.claude/worktrees/dossier-modern-history-6f7767')
HERE = Path(__file__).resolve().parent
DRAFTS = HERE / 'drafts'
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(HERE))
from dossiers import validate_dossier, validate_links  # noqa: E402
from words import LIMIT, count  # noqa: E402

TABLE_OF = {'ev': 'events', 'fig': 'figures', 'tr': 'treaties'}
PREFIX = {'events': 'ev-', 'figures': 'per-', 'treaties': 'tr-'}
COUNTRIES = {'中国', '俄罗斯'}
KINDS = {'战争', '起义', '运动', '革命', '改革', '事变', '战役', '会议', '事件'}
YEAR = re.compile(r'\d{4} 年')
WORD = re.compile(r'[А-Яа-яЁё0-9]+')
DOSSIER = 'modern-history'


def table_of(file: Path) -> str:
    return TABLE_OF[file.name.split('-', 1)[0]]


def main() -> None:
    args = sys.argv[1:]
    dossiers = {}
    for file in sorted((ROOT / 'data/dossiers').glob('*.json')):
        if not file.name.endswith('-questions.json'):
            data = json.loads(file.read_text('utf-8'))
            dossiers[data['id']] = data
    own = dossiers[DOSSIER]
    # строки досье в проекте — это уже сведённые черновики: проверяем черновики, а не их сумму
    for name in own['tables']:
        own['tables'][name]['rows'] = []
    for file in sorted(DRAFTS.glob('*.json')):
        own['tables'][table_of(file)]['rows'] += json.loads(file.read_text('utf-8'))
    if args:
        path = Path(args[0]).resolve()
        if path.parent != DRAFTS.resolve():
            own['tables'][args[1]]['rows'] += json.loads(path.read_text('utf-8'))

    errors = validate_dossier(own)
    errors += [e for e in validate_links(dossiers) if e.startswith(f'{DOSSIER}/')]
    bank = json.loads((ROOT / 'data/bank.json').read_text('utf-8'))
    known = {r['id'] for r in bank} | {i for r in bank for i in r.get('mergedIds', [])}
    rows = {name: [r for r in t['rows'] if isinstance(r, dict)] for name, t in own['tables'].items()}
    per_url: dict[str, list] = {}
    for name, table_rows in rows.items():
        for row in table_rows:
            rid = str(row.get('id', '?'))
            country = (row.get('country') or {}).get('zh')
            if not rid.startswith(PREFIX[name]):
                errors.append(f'{name}/{rid}: id начинается с {PREFIX[name]}')
            if country not in COUNTRIES:
                errors.append(f'{name}/{rid}: country — 中国 или 俄罗斯')
            elif (country == '俄罗斯') != rid.startswith(PREFIX[name] + 'ru-'):
                errors.append(f'{name}/{rid}: российские строки — {PREFIX[name]}ru-…, китайские — без ru-')
            if 'ru' in (row.get('country') or {}):
                errors.append(f'{name}/{rid}: у country нет ru')
            if name == 'events':
                kind = row.get('kind') or {}
                if kind.get('zh') not in KINDS:
                    errors.append(f'{name}/{rid}: kind — один из {sorted(KINDS)}')
                if 'ru' in kind:
                    errors.append(f'{name}/{rid}: у kind нет ru')
            year = row.get('year')
            if isinstance(year, dict) and not YEAR.fullmatch(year.get('zh', '')):
                errors.append(f'{name}/{rid}.year: вид «1840 年» (четыре цифры, пробел, 年)')
            for olympiad_id in row.get('olympiad', []):
                if not re.match(r'(20\d\d-\d\d-|addition-)', olympiad_id):
                    errors.append(f'{name}/{rid}: olympiad {olympiad_id} — это не олимпиадный вопрос')
                elif olympiad_id not in known:
                    errors.append(f'{name}/{rid}: olympiad {olympiad_id} — нет такого вопроса в банке')
            for column, cell in row.items():
                if not isinstance(cell, dict):
                    continue
                for ru in cell.get('ru', []):
                    words = WORD.findall(ru)
                    if len(words) == 1 and len(words[0]) < 6:
                        errors.append(f'{name}/{rid}.{column}: русское название {ru!r} короче шести букв — '
                                      'дать из двух слов («Владимир Ленин») или убрать')
            for source in row.get('sources', []):
                per_url.setdefault(source.get('url'), []).append((rid, count(source.get('quote', ''))))
    for url, uses in per_url.items():
        total = sum(n for _, n in uses)
        if total > LIMIT:
            errors.append(f'цитаты с {url}: {total} слов (строки {", ".join(r for r, _ in uses)}) — '
                          f'больше {LIMIT} на публикацию; сократи цитату или возьми другую страницу')

    glosses = {}
    for name, table_rows in rows.items():
        for row in table_rows:
            for column, cell in row.items():
                if isinstance(cell, dict) and 'gloss' in cell:
                    glosses.setdefault((name, column, cell.get('zh')), {}).setdefault(cell['gloss'], []).append(row.get('id'))
    for (name, column, zh), variants in glosses.items():
        if len(variants) > 1:
            errors.append(f'{name}.{column} {zh}: у одинакового текста разные подписи: '
                          + '; '.join(f'{ids} — {gloss!r}' for gloss, ids in variants.items()))

    targets = json.loads((HERE / 'embed-targets.json').read_text('utf-8'))
    missing = []
    for qid, target in targets.items():
        tab, col = target['place'].split('.')
        cells = {r[col]['zh'] for r in rows[tab] if isinstance(r.get(col), dict)}
        lack = [o for o in target['options'] if o not in cells]
        if lack:
            missing.append(f'{qid} ({target["place"]}): нет ячеек {lack}')

    print('\n'.join(errors) if errors else 'ошибок нет')
    print('встраивание — пока нет ячеек:' if missing else 'встраивание: ячейки всех вариантов есть')
    print('\n'.join('  ' + m for m in missing))
    for name, table_rows in rows.items():
        ru = sum(1 for r in table_rows if (r.get('country') or {}).get('zh') == '俄罗斯')
        print(f'{name}: строк {len(table_rows)} (из них России {ru})')


if __name__ == '__main__':
    main()
