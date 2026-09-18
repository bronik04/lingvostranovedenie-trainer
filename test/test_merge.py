import json, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from merge_bank import merge, record_id
from normalize import normalize_text

WHOLE = 'Административный центр провинции Цзянсу, одна из четырех древних столиц Китая.'
TRUNCATED = 'Административный центр провинции Цзянсу, одна из четырех древних столиц'


def raw(**overrides):
    record = {
        'sourceFile': 'Банк вопросов — лингвострановедение (423, с ответами).docx',
        'year': '2023-24', 'stage': 'школьный', 'stageCode': 'shk', 'grades': '9-11',
        'number': 138, 'sourceOrdinal': None, 'questionRu': WHOLE,
        'questionZh': None, 'options': ['西安', '北京', '洛阳', '南京'],
        'officialKeyIndex': None, 'topic': None, 'parseWarnings': [],
    }
    record.update(overrides)
    return record


class RecordIdTest(unittest.TestCase):
    def test_id_is_built_from_year_stage_and_number(self):
        self.assertEqual(record_id({'year': '2015-16', 'stageCode': 'shk', 'number': 56}), '2015-16-shk-56')


class MergeTest(unittest.TestCase):
    def test_merges_duplicates_by_option_set(self):
        bank, _ = merge([raw(), raw(year='2018-19', stageCode='mun', number=29)], {})
        self.assertEqual(len(bank), 1)
        self.assertEqual(len(bank[0]['occurrences']), 2)

    def test_record_with_a_missing_option_joins_the_complete_one(self):
        """В банке 423 у вопроса про восемь кухонь нет варианта D, в сборнике он есть."""
        question = '中国的菜有很多种类，请问“宫保鸡丁”和“鱼香肉丝”属于哪一个菜系？'
        broken = raw(questionRu=None, questionZh=question, options=['粤菜', '川菜', '湘菜', ''])
        whole = raw(sourceFile='Лингвострановедение ВсОШ.docx', questionRu=None, questionZh=question,
                    options=['粤菜', '川菜', '湘菜', '浙菜'], officialKeyIndex=1)
        russian = 'К какой из восьми кулинарных традиций Китая относятся гунбао цзидин и юйсян жоусы?'
        bank, _ = merge([broken, whole], {normalize_text(question): russian})
        self.assertEqual(len(bank), 1)
        self.assertEqual([option['zh'] for option in bank[0]['options']], ['粤菜', '川菜', '湘菜', '浙菜'])

    def test_record_whose_defect_is_in_the_original_paper_is_dropped_with_a_reason(self):
        """У вопроса про достопримечательность четвёртый вариант испорчен в самом бланке ВсОШ."""
        bank, report = merge([raw(options=['兵马俑', '十三陵', '大唐芙蓉园', ''])], {})
        self.assertEqual(bank, [])
        self.assertEqual(len(report['dropped']), 1)
        self.assertTrue(any('пустой вариант' in error for error in report['dropped'][0]['errors']))

    def test_keeps_the_whole_wording_over_the_truncated_one(self):
        """В банке 423 у этого вопроса отрезано «Китая.», в базе «310» текст целый."""
        bank, _ = merge([
            raw(questionRu=TRUNCATED),
            raw(sourceFile='Вопросы по категориям (310 шт).docx', questionRu=WHOLE,
                topic='География и административное устройство'),
        ], {})
        self.assertEqual(bank[0]['questionRu'], WHOLE)

    def test_truncated_wording_alone_is_dropped_not_silently_accepted(self):
        bank, report = merge([raw(questionRu=TRUNCATED)], {})
        self.assertEqual(bank, [])
        self.assertTrue(any('обрывается' in error for error in report['dropped'][0]['errors']))

    def test_takes_russian_text_from_translations_for_chinese_questions(self):
        bank, _ = merge(
            [raw(questionRu=None, questionZh='现在中国的人口总数是多少？',
                 options=['接近20亿', '接近1亿', '接近15亿', '超过18亿'])],
            {'现在中国的人口总数是多少': 'Какова общая численность населения Китая в настоящее время?'})
        self.assertEqual(bank[0]['questionRu'], 'Какова общая численность населения Китая в настоящее время?')

    def test_official_key_becomes_the_answer_but_stays_unverified(self):
        bank, _ = merge([raw(officialKeyIndex=3)], {})
        self.assertEqual(bank[0]['answer'], {'optionId': 'o4', 'state': 'unverified'})

    def test_conflicting_keys_are_not_resolved_silently(self):
        bank, report = merge([raw(officialKeyIndex=3), raw(year='2018-19', stageCode='mun', officialKeyIndex=0)], {})
        self.assertEqual(bank[0]['answer']['state'], 'conflict')
        self.assertEqual(len(report['conflicts']), 1)

    def test_question_without_key_is_needs_review(self):
        bank, _ = merge([raw()], {})
        self.assertEqual(bank[0]['answer']['state'], 'needs-review')
        self.assertIsNone(bank[0]['answer']['optionId'])

    def test_report_lists_questions_left_without_russian_text(self):
        bank, report = merge([raw(questionRu=None, questionZh='某个没有翻译的问题？')], {})
        self.assertEqual(len(report['untranslated']), 1)
        self.assertEqual(bank, [])

    def test_merge_is_deterministic_regardless_of_input_order(self):
        first = raw(questionRu=TRUNCATED)
        second = raw(sourceFile='Вопросы по категориям (310 шт).docx', questionRu=WHOLE,
                     topic='География и административное устройство')
        forward, _ = merge([first, second], {})
        backward, _ = merge([second, first], {})
        self.assertEqual(json.dumps(forward, ensure_ascii=False, sort_keys=True),
                         json.dumps(backward, ensure_ascii=False, sort_keys=True))


if __name__ == '__main__':
    unittest.main()
