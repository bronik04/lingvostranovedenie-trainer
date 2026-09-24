"""Проверка, что ссылки-источники (evidence) в банке ещё живы.

Не пересобирает банк и ничего в нём не меняет — отдельная, независимая от
сайта задача для CI: раз в неделю бьёт все уникальные URL и пишет отчёт.
"""

from __future__ import annotations

import http.client
import json
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'data/review/broken-links.md'
STATE = ROOT / 'data/review/broken-links.json'
USER_AGENT = 'Mozilla/5.0 (compatible; lingvostranovedenie-trainer-linkcheck/1.0)'
TIMEOUT = 12
# Коды, которыми отвечает защита от ботов, а не сама страница: 403 — baike.baidu.com
# банит после пары прогонов подряд, 418 — WAF csx.gov.cn («request intercepted»
# даже обычному браузеру), 429 — ограничение частоты запросов.
AMBIGUOUS_CODES = {403, 418, 429}
# Код выхода, когда есть подтверждённо битые ссылки. Отличается от 1, с которым
# Python завершается на необработанном исключении: падение скрипта не должно
# выглядеть в CI как «ссылки битые».
EXIT_CONFIRMED = 3


def collect_urls(bank: list[dict]) -> dict[str, list[str]]:
    """URL -> id записей, где он встречается (для отчёта, куда чинить)."""
    by_url: dict[str, list[str]] = defaultdict(list)
    for record in bank:
        for entry in record.get('evidence', []):
            by_url[entry['url']].append(record['id'])
    return dict(by_url)


def check_url(url: str, opener=urllib.request.urlopen) -> tuple[bool, str, bool]:
    """(жива ли ссылка, код/причина, дал ли сервер осмысленный ответ).

    Большая часть ссылок — статьи Wikipedia с кириллицей/иероглифами прямо
    в пути (https://ru.wikipedia.org/wiki/Лена); http.client умеет отправлять
    только ASCII, поэтому URL сперва процент-кодируется (уже закодированные
    последовательности — %XX — не трогаются повторно).

    HEAD — только быстрый путь к ответу «жива». Решает ответ на GET:
    baike.baidu.com стабильно отвечает 404 на HEAD и 200 на GET для того же
    адреса. Если GET при этом упрётся в антибот, 404 от HEAD нельзя считать
    ответом про страницу (так три живые страницы Baike числились «404 под
    наблюдением» и через неделю подтвердились бы как битые).

    conclusive=True только когда GET получил от сервера HTTP-код, который
    говорит о самой странице (404, 410, 500…). Таймаут, обрыв соединения,
    TLS, DNS и коды защиты от ботов (AMBIGUOUS_CODES) ничего не доказывают:
    это может быть путь от текущей машины до сайта, а не сама страница
    (реально наблюдалось на китайских gov.cn: 403/timeout под нагрузкой
    прогона на страницах, которые по отдельности открывались)."""
    safe_url = urllib.parse.quote(url, safe=":/?#[]@!$&'()*+,;=%")
    reason, conclusive = 'нет ответа', False
    for method in ('HEAD', 'GET'):
        request = urllib.request.Request(safe_url, method=method, headers={'User-Agent': USER_AGENT})
        try:
            with opener(request, timeout=TIMEOUT) as response:
                return True, str(response.status), True
        except urllib.error.HTTPError as error:
            reason, conclusive = str(error.code), error.code not in AMBIGUOUS_CODES
        except urllib.error.URLError as error:
            reason, conclusive = str(error.reason), False
        except TimeoutError:
            reason, conclusive = 'timeout', False
        except (OSError, http.client.HTTPException) as error:
            # обрыв без ответа (RemoteDisconnected), сброс соединения, TLS —
            # urllib не заворачивает их в URLError, если они случились при
            # чтении ответа; прогон 2026-09-21 упал на таком целиком
            reason, conclusive = f'{type(error).__name__}: {error}', False
    return False, reason, conclusive


def check_all(urls: list[str], max_workers: int = 4) -> dict[str, tuple[bool, str, bool]]:
    # baike.baidu.com реально банит по IP уже на восьми параллельных запросах
    # (проверено: 403 на все baidu-ссылки в первом прогоне, при том что до
    # этого те же адреса по одному отвечали 200) — щадящая конкурентность
    # снижает шанс словить бан антибота ещё на этапе самой проверки.
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        results = pool.map(check_url, urls)
    return dict(zip(urls, results))


def confirmed_broken(currently_broken: set[str], previously_broken: set[str]) -> set[str]:
    """Один прогон ничего не доказывает: антибот-защиты (baidu, zhihu) и
    таймауты китайских gov.cn под нагрузкой прогона дают ложные 403/timeout
    на живых страницах. Считаем ссылку действительно битой, только если она
    битая второй прогон подряд (то есть примерно неделю)."""
    return currently_broken & previously_broken


def build_report(results: dict[str, tuple[bool, str, bool]], by_url: dict[str, list[str]],
                  confirmed: set[str]) -> str:
    """Чистая функция без побочных эффектов — сборка текста отчёта. Запись на
    диск отдельно, в write_report(), чтобы тесты не портили настоящий отчёт
    в data/review при каждом запуске тестов."""
    broken = sorted(url for url, (ok, _, _) in results.items() if not ok)
    watching = [url for url in broken if results[url][2] and url not in confirmed]
    network_noise = [url for url in broken if not results[url][2]]
    lines = ['# Проверка ссылок-источников', '',
              f'Проверено ссылок: {len(results)}', f'Битых сейчас: {len(broken)}',
              f'Подтверждено два прогона подряд: {len(confirmed)}', '']

    def section(title: str, items: list[str]) -> None:
        lines.append(f'## {title}')
        lines.append('')
        for url in items:
            _, reason, _ = results[url]
            ids = ', '.join(f'`{i}`' for i in by_url.get(url, []))
            lines.append(f'- {url} — {reason} (записи: {ids})')
        lines.append('')

    if confirmed:
        section('Подтверждённые (нужно чинить)', sorted(confirmed))
    if watching:
        section('Под наблюдением (есть ответ сервера, но подтвердим на следующей неделе)', watching)
    if network_noise:
        section('Неубедительные (таймаут, обрыв соединения, TLS/DNS, 403/418/429 — может быть '
                'путь до сайта или антибот-блокировка, а не сама ссылка; не считаются и не '
                'подтверждаются)',
                sorted(network_noise))
    if not broken:
        lines.append('Все ссылки отвечают.')
    return '\n'.join(lines).rstrip() + '\n'


def write_report(results: dict[str, tuple[bool, str, bool]], by_url: dict[str, list[str]],
                  confirmed: set[str]) -> str:
    text = build_report(results, by_url, confirmed)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text, encoding='utf-8')
    return text


def main() -> None:
    bank = json.loads((ROOT / 'data/bank.json').read_text('utf-8'))
    by_url = collect_urls(bank)
    urls = sorted(by_url)
    results = check_all(urls)
    # только убедительные (реальный HTTP-ответ) сбои идут в накопительное
    # состояние между прогонами — сетевой шум не должен уметь «подтвердиться»
    # даже если повторяется из недели в неделю
    currently_broken = {url for url, (ok, _, conclusive) in results.items() if not ok and conclusive}

    previously_broken: set[str] = set()
    if STATE.exists():
        previously_broken = set(json.loads(STATE.read_text('utf-8')))
    confirmed = confirmed_broken(currently_broken, previously_broken)

    write_report(results, by_url, confirmed)
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(sorted(currently_broken), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    all_broken = [url for url, (ok, _, _) in results.items() if not ok]
    print(f'проверено {len(urls)}, битых сейчас {len(all_broken)} '
          f'(из них с ответом сервера {len(currently_broken)}), подтверждено {len(confirmed)}')
    for url in sorted(all_broken):
        if url in confirmed:
            mark = 'подтверждено'
        elif url in currently_broken:
            mark = 'под наблюдением'
        else:
            mark = 'сетевая ошибка'
        print(f' - [{mark}]', url, results[url][1])
    if confirmed:
        raise SystemExit(EXIT_CONFIRMED)


if __name__ == '__main__':
    main()
