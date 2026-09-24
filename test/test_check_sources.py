import http.client, ssl, sys, unittest
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from check_sources import build_report, check_url, collect_urls, confirmed_broken


class CollectUrlsTest(unittest.TestCase):
    def test_groups_record_ids_by_url(self):
        bank = [
            {'id': 'a', 'evidence': [{'url': 'https://x.org/1'}, {'url': 'https://x.org/2'}]},
            {'id': 'b', 'evidence': [{'url': 'https://x.org/1'}]},
            {'id': 'c', 'evidence': []},
        ]
        self.assertEqual(collect_urls(bank), {
            'https://x.org/1': ['a', 'b'],
            'https://x.org/2': ['a'],
        })


def _response(status):
    response = MagicMock()
    response.status = status
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    return response


class CheckUrlTest(unittest.TestCase):
    def test_200_is_alive_and_conclusive(self):
        opener = MagicMock(return_value=_response(200))
        self.assertEqual(check_url('https://x.org', opener=opener), (True, '200', True))

    def test_404_is_broken_and_conclusive(self):
        """Сервер реально ответил «нет такой страницы» — с этим можно работать
        сразу, без недели ожидания подтверждения."""
        def opener(request, timeout):
            raise urllib.error.HTTPError('https://x.org', 404, 'Not Found', {}, None)
        self.assertEqual(check_url('https://x.org', opener=opener), (False, '404', True))

    def test_head_405_falls_back_to_get(self):
        calls = []

        def opener(request, timeout):
            calls.append(request.get_method())
            if request.get_method() == 'HEAD':
                raise urllib.error.HTTPError('https://x.org', 405, 'Method Not Allowed', {}, None)
            return _response(200)

        self.assertEqual(check_url('https://x.org', opener=opener), (True, '200', True))
        self.assertEqual(calls, ['HEAD', 'GET'])

    def test_head_404_still_falls_back_to_get(self):
        """baike.baidu.com реально отдаёт 404 на HEAD и 200 на GET для одного
        и того же адреса — HEAD там просто не поддерживается нормально,
        это не значит, что ссылка битая."""
        def opener(request, timeout):
            if request.get_method() == 'HEAD':
                raise urllib.error.HTTPError('https://x.org', 404, 'Not Found', {}, None)
            return _response(200)

        self.assertEqual(check_url('https://x.org', opener=opener), (True, '200', True))

    def test_broken_on_both_head_and_get_reports_the_get_reason(self):
        def opener(request, timeout):
            code = 404 if request.get_method() == 'HEAD' else 410
            raise urllib.error.HTTPError('https://x.org', code, 'x', {}, None)

        self.assertEqual(check_url('https://x.org', opener=opener), (False, '410', True))

    def test_connection_error_is_broken_but_not_conclusive(self):
        """Таймаут/обрыв соединения ничего не доказывает про саму ссылку —
        это может быть путь до сайта с этой конкретной машины, а не сайт.
        Реально наблюдалось на china gov.cn под GitHub Actions/локально."""
        def opener(request, timeout):
            raise urllib.error.URLError('нет соединения')
        ok, reason, conclusive = check_url('https://x.org', opener=opener)
        self.assertFalse(ok)
        self.assertIn('соединения', reason)
        self.assertFalse(conclusive)

    def test_timeout_is_broken_but_not_conclusive(self):
        def opener(request, timeout):
            raise TimeoutError()
        ok, reason, conclusive = check_url('https://x.org', opener=opener)
        self.assertFalse(ok)
        self.assertEqual(reason, 'timeout')
        self.assertFalse(conclusive)

    def test_403_is_broken_but_not_conclusive(self):
        """403 слишком неоднозначен, чтобы доверять ему безоговорочно: реально
        наблюдалось на baike.baidu.com — 44 ссылки из банка стабильно
        отвечали 403 после нескольких прогонов подряд с одной машины (похоже
        на антибот-блокировку), хотя по отдельности открывались нормально."""
        def opener(request, timeout):
            raise urllib.error.HTTPError('https://x.org', 403, 'Forbidden', {}, None)
        ok, reason, conclusive = check_url('https://x.org', opener=opener)
        self.assertFalse(ok)
        self.assertEqual(reason, '403')
        self.assertFalse(conclusive)

    def test_head_404_proves_nothing_when_get_cannot_connect(self):
        """Решает только ответ на GET: HEAD на baike.baidu.com отвечает 404 даже
        для живых страниц, поэтому его ошибка сама по себе ничего не доказывает."""
        def opener(request, timeout):
            if request.get_method() == 'HEAD':
                raise urllib.error.HTTPError('https://x.org', 404, 'x', {}, None)
            raise urllib.error.URLError('обрыв')

        ok, reason, conclusive = check_url('https://x.org', opener=opener)
        self.assertFalse(ok)
        self.assertEqual(reason, 'обрыв')
        self.assertFalse(conclusive)

    def test_head_404_then_get_403_is_not_conclusive(self):
        """Пойман на реальных данных 2026-09-24: три ссылки baike.baidu.com
        (太原市, 夸父逐日, 抓周) числились «404 под наблюдением», хотя в браузере
        открываются. HEAD дал свой обычный 404, GET упёрся в антибот (403) —
        прежняя логика принимала 404 от HEAD за убедительный ответ и через
        неделю подтвердила бы живые страницы как битые."""
        def opener(request, timeout):
            code = 404 if request.get_method() == 'HEAD' else 403
            raise urllib.error.HTTPError('https://x.org', code, 'x', {}, None)

        ok, reason, conclusive = check_url('https://x.org', opener=opener)
        self.assertFalse(ok)
        self.assertEqual(reason, '403')
        self.assertFalse(conclusive)

    def test_waf_418_is_not_conclusive(self):
        """csx.gov.cn отвечает 418 и страницей «request intercepted» даже обычному
        браузеру — это защита сайта, а не сведения о самой странице."""
        def opener(request, timeout):
            raise urllib.error.HTTPError('https://x.org', 418, "I'm a teapot", {}, None)
        ok, reason, conclusive = check_url('https://x.org', opener=opener)
        self.assertFalse(ok)
        self.assertEqual(reason, '418')
        self.assertFalse(conclusive)

    def test_dropped_connection_does_not_crash_the_run(self):
        """Еженедельный прогон 2026-09-21 упал целиком: сервер закрыл соединение
        без ответа, http.client.RemoteDisconnected не обёрнут в URLError и не
        ловился. Такой обрыв — сетевой шум, как таймаут."""
        def opener(request, timeout):
            raise http.client.RemoteDisconnected('Remote end closed connection without response')
        ok, reason, conclusive = check_url('https://x.org', opener=opener)
        self.assertFalse(ok)
        self.assertIn('RemoteDisconnected', reason)
        self.assertFalse(conclusive)

    def test_tls_failure_does_not_crash_the_run(self):
        def opener(request, timeout):
            raise ssl.SSLError('handshake failure')
        ok, _, conclusive = check_url('https://x.org', opener=opener)
        self.assertFalse(ok)
        self.assertFalse(conclusive)

    def test_non_ascii_url_is_percent_encoded_before_the_request(self):
        """Большинство ссылок — статьи Wikipedia с кириллицей/иероглифами прямо
        в пути (https://ru.wikipedia.org/wiki/Лена); http.client падает с
        UnicodeEncodeError, если их не закодировать сначала."""
        seen = {}

        def opener(request, timeout):
            seen['url'] = request.full_url
            return _response(200)

        ok, _, _ = check_url('https://ru.wikipedia.org/wiki/Лена', opener=opener)
        self.assertTrue(ok)
        self.assertTrue(seen['url'].isascii())
        self.assertIn('%D0%9B%D0%B5%D0%BD%D0%B0', seen['url'])


class ConfirmedBrokenTest(unittest.TestCase):
    def test_only_urls_broken_in_both_runs_are_confirmed(self):
        """Один прогон ничего не решает: baidu.com на практике то и дело
        отвечает 403 под нагрузкой прогона, хотя ссылка жива. Тревогу
        поднимаем только если сайт мёртв два прогона подряд."""
        currently = {'https://a.org', 'https://b.org'}
        previously = {'https://b.org', 'https://c.org'}
        self.assertEqual(confirmed_broken(currently, previously), {'https://b.org'})

    def test_nothing_previously_broken_confirms_nothing(self):
        self.assertEqual(confirmed_broken({'https://a.org'}, set()), set())


class BuildReportTest(unittest.TestCase):
    def test_separates_confirmed_watching_and_network_noise(self):
        results = {
            'https://x.org/1': (True, '200', True),
            'https://x.org/2': (False, '404', True),   # подтверждён
            'https://x.org/3': (False, '500', True),   # под наблюдением: убедительный, но первый раз
            'https://x.org/4': (False, 'timeout', False),  # неубедительный, сетевой
        }
        by_url = {u: ['a'] for u in results}
        text = build_report(results, by_url, confirmed={'https://x.org/2'})
        self.assertIn('Битых сейчас: 3', text)
        self.assertIn('Подтверждено два прогона подряд: 1', text)
        self.assertIn('## Подтверждённые', text)
        self.assertIn('https://x.org/2', text)
        self.assertIn('## Под наблюдением', text)
        self.assertIn('https://x.org/3', text)
        self.assertIn('## Неубедительные', text)
        self.assertIn('https://x.org/4', text)
        self.assertNotIn('https://x.org/1 —', text)

    def test_all_alive_says_so(self):
        text = build_report({'https://x.org/1': (True, '200', True)}, {'https://x.org/1': ['a']}, confirmed=set())
        self.assertIn('Все ссылки отвечают', text)


if __name__ == '__main__':
    unittest.main()
