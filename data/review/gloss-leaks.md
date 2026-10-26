<!-- Отчёт пишет сборка (scripts/merge_bank.py): не править, перезапишется. -->

# Утечки через подписи вариантов

Подпись неверного варианта и название верного ответа (подпись под ним, решение автора 2026-10-26)
ученик видит после ответа. Утечка — когда вариант с подписью называет
ответ соседнего вопроса и то, о чём тот спрашивает: сам вариант или другое название из его текста
(зацепку). Проверка — `gloss_leaks` в `scripts/dossiers.py`, исключения те же, что у текстов: группы
фактов, одна строка, мостик. Сборку не останавливает: закрыть утечку — правка подписи (с «да» автора)
или группа фактов. Подпись ячейки досье называет свою строку, и её пары с вопросами о том же факте
(«та же строка», тот же факт в связанной таблице или в олимпиадном вопросе) в счёте ниже есть, но это
повторение, а не утечка (решение автора 2026-10-26). Название верного ответа рядом с вопросом с тем же
ответом утечкой не считается: ответ выдаёт сам вариант. Названия помечены «(название ответа)».

Подписей с утечкой: 605; выданных вопросов: 407; пар «вопрос с подписью → соседний вопрос»: 2869, из них 1670 — подпись о той же строке досье, о которой спрашивает соседний вопрос («та же строка»). Черновиков досье в банке нет: пары с ними помечены «(черновик)».

## 特别行政区 — Особый административный район — Сянган и Аомэнь (название ответа)

- выдаёт 2015-16-shk-64: ответ Сянган; зацепка 特别行政区, та же строка
- выдаёт 2016-17-shk-3: ответ Аомэнь; зацепка 特别行政区
- выдаёт 2025-26-mun-chel-9: ответ Сянган; зацепка Особый административный район
- выдаёт provinces/provinces-q88: ответ 特别行政区; зацепка Аомэнь
- видна в 3: provinces/provinces-q109, provinces/provinces-q88, provinces/provinces-q98

## 2001 年 — 2001 — основание Шанхайской организации сотрудничества

- выдаёт 2022-23-reg-9: ответ 2001; зацепка Шанхайская организация сотрудничества
- выдаёт modern-china/modern-china-q10: ответ Шанхайская организация сотрудничества; зацепка 2001 год
- выдаёт provinces/provinces-q29: ответ Шанхай; зацепка 2001 год
- видна в 1: 2021-22-mun-q833ea2

## 农奴制改革 — Отмена крепостного права: манифест Александра II 19 февраля 1861 года (название ответа)

- выдаёт 2020-21-mun-lenobl-3: ответ Александр II; зацепка Отмена крепостного права
- выдаёт dynasties/dynasties-q119: ответ 农奴制改革; зацепка Александр II, та же строка
- выдаёт modern-history/modern-history-q97: ответ 1861 год; зацепка Отмена крепостного права
- видна в 5: dynasties/dynasties-q117, dynasties/dynasties-q118, dynasties/dynasties-q119, dynasties/dynasties-q121, dynasties/dynasties-q122

## 外滩 — Вайтань — набережная вдоль реки Хуанпу в Шанхае

- выдаёт 2016-17-shk-7: ответ Хуанпу, река Хуанпу; зацепка Шанхай
- выдаёт 2021-22-mun-q5434f2: ответ 外滩, Вайтань; зацепка Шанхай
- выдаёт landmarks/landmarks-q100: ответ Шанхай; зацепка набережная Вайтань, 外滩
- видна в 1: provinces/provinces-q56

## 外滩 — Вайтань — набережная реки Хуанпу в Шанхае с ансамблем зданий разных стилей

- выдаёт 2016-17-shk-7: ответ Хуанпу, река Хуанпу; зацепка Шанхай
- выдаёт 2021-22-mun-q5434f2: ответ 外滩, Вайтань; зацепка Шанхай
- выдаёт landmarks/landmarks-q100: ответ Шанхай; зацепка набережная Вайтань, 外滩, та же строка
- видна в 1: landmarks/landmarks-q106

## 林则徐 — Линь Цзэсюй — императорский комиссар, в 1839 году уничтожил опиум в Хумэне

- выдаёт modern-history/modern-history-q109: ответ 林则徐, Линь Цзэсюй; зацепка Хумэнь, та же строка
- выдаёт modern-history/modern-history-q54: ответ 1839 год; зацепка Линь Цзэсюй, Хумэнь, императорский комиссар, та же строка
- выдаёт modern-history/modern-history-q95: ответ императорский комиссар; зацепка Линь Цзэсюй, 林则徐, та же строка
- видна в 10: modern-history/modern-history-q04, modern-history/modern-history-q05, modern-history/modern-history-q06, modern-history/modern-history-q110, modern-history/modern-history-q111, modern-history/modern-history-q113, modern-history/modern-history-q12, modern-history/modern-history-q17, modern-history/modern-history-q60, modern-history/modern-history-q96

## 粤绣 — Гуандунская (кантонская) вышивка, центр — Гуанчжоу

- выдаёт 2024-25-mun-irk-10: ответ 粤绣, кантонская вышивка; зацепка Гуандун
- выдаёт ethnos/ethnos-q86: ответ кантонский; зацепка Гуандун
- выдаёт provinces/provinces-q99: ответ Гуанчжоу; зацепка Гуандун
- видна в 2: crafts/crafts-q129, crafts/crafts-q14

## 鲁迅 — Лу Синь — автор «Дневника сумасшедшего» и «Подлинной истории А-Кью» (название ответа)

- выдаёт literature/literature-q04: ответ 鲁迅, Лу Синь; зацепка Подлинная история А-Кью, та же строка
- выдаёт literature/literature-q19: ответ Дневник сумасшедшего; зацепка Лу Синь
- выдаёт literature/literature-q90: ответ Подлинная история А-Кью, история А-Кью; зацепка Лу Синь, 鲁迅, та же строка
- видна в 10: literature/literature-q01, literature/literature-q02, literature/literature-q03, literature/literature-q04, literature/literature-q05, literature/literature-q43, literature/literature-q44, literature/literature-q46, literature/literature-q96, literature/literature-q97

## 黄山 — Хуаншань — гора в Аньхое, известная причудливыми соснами и морем облаков

- выдаёт 2021-22-mun-mosobl-59: ответ 黄山; зацепка сосна
- выдаёт nature/nature-q147: ответ Аньхой; зацепка гора Хуаншань, 黄山, та же строка
- выдаёт nature/nature-q51: ответ 黄山; зацепка сосна, та же строка
- видна в 2: nature/nature-q144, nature/nature-q46

## 1839 年 — 1839 год: Линь Цзэсюй уничтожил опиум в Хумэне

- выдаёт modern-history/modern-history-q109: ответ Линь Цзэсюй; зацепка Хумэнь, та же строка
- выдаёт modern-history/modern-history-q54: ответ 1839 年, 1839 год; зацепка Линь Цзэсюй, Хумэнь, та же строка
- видна в 4: modern-history/modern-history-q56, modern-history/modern-history-q57, modern-history/modern-history-q59, modern-history/modern-history-q62

## 1911 — 1911 — Учанское восстание, начало Синьхайской революции

- выдаёт 2015-16-shk-60: ответ 1911; зацепка Синьхайская революция
- выдаёт modern-history/modern-history-q63: ответ Учанское восстание; зацепка Синьхайская революция
- видна в 1: 2016-17-reg-6

## 1911 年 — 1911 — Учанское восстание, начало Синьхайской революции

- выдаёт 2015-16-shk-60: ответ 1911; зацепка Синьхайская революция
- выдаёт modern-history/modern-history-q63: ответ Учанское восстание; зацепка Синьхайская революция
- видна в 1: 2025-26-shk-31

## 三国演义 — «Троецарствие» — роман, по традиции приписываемый Ло Гуаньчжуну

- выдаёт literature/literature-q17: ответ 三国演义, Троецарствие, Троецарствия; зацепка Ло Гуаньчжун
- выдаёт literature/literature-q96: ответ Ло Гуаньчжун; зацепка Троецарствие, Троецарствия, 三国演义
- видна в 5: literature/literature-q88, literature/literature-q89, literature/literature-q90, literature/literature-q91, literature/literature-q92

## 三民主义 — «Три народных принципа» — учение Сунь Ятсена о нации, правах и благосостоянии народа

- выдаёт modern-history/modern-history-q05: ответ Сунь Ятсен; зацепка три народных принципа, 三民主义, та же строка
- выдаёт modern-history/modern-history-q93: ответ 三民主义, три народных принципа; зацепка Сунь Ятсен, та же строка
- видна в 4: modern-history/modern-history-q11, modern-history/modern-history-q24, modern-history/modern-history-q26, modern-history/modern-history-q27

## 上海 — Шанхай — здесь набережная Вайтань с домами в европейских стилях

- выдаёт 2021-22-mun-q5434f2: ответ Вайтань, Набережная Вайтань, набережная Вайтань; зацепка город Шанхай
- выдаёт landmarks/landmarks-q100: ответ 上海, Шанхай; зацепка набережная Вайтань, та же строка
- видна в 1: landmarks/landmarks-q99

## 中华民国临时大总统 — Временный президент Китайской Республики — им в 1912 году стал Сунь Ятсен

- выдаёт 2020-21-reg-q227d55: ответ 1912; зацепка Китайская Республика
- выдаёт modern-history/modern-history-q96: ответ Сунь Ятсен; зацепка Китайская Республика, временный президент Китайской Республики, та же строка
- видна в 1: modern-history/modern-history-q95

## 习近平 — Си Цзиньпин — председатель КНР с 2013 года

- выдаёт 2023-24-mun-30: ответ 2013 год, 2013; зацепка Си Цзиньпин, председатель КНР, та же строка
- выдаёт modern-history/modern-history-q02: ответ 习近平, Си Цзиньпин; зацепка председатель КНР, та же строка
- видна в 9: modern-history/modern-history-q01, modern-history/modern-history-q03, modern-history/modern-history-q04, modern-history/modern-history-q05, modern-history/modern-history-q07, modern-history/modern-history-q17, modern-history/modern-history-q25, modern-history/modern-history-q28, modern-history/modern-history-q96

## 亚历山大二世 — Александр II — император в 1855–1881 годах, в 1861 году отменил крепостное право (название ответа)

- выдаёт 2020-21-mun-lenobl-3: ответ 亚历山大二世, Александр II; зацепка Отмена крепостного права
- выдаёт modern-history/modern-history-q97: ответ 1861 год; зацепка Отмена крепостного права
- видна в 10: dynasties/dynasties-q41, dynasties/dynasties-q42, dynasties/dynasties-q43, dynasties/dynasties-q44, dynasties/dynasties-q45, dynasties/dynasties-q47, dynasties/dynasties-q49, dynasties/dynasties-q50, dynasties/dynasties-q55, dynasties/dynasties-q56

## 亚历山大二世 — Александр II — император, при котором в 1861 году отменили крепостное право

- выдаёт 2020-21-mun-lenobl-3: ответ 亚历山大二世, Александр II; зацепка Отмена крепостного права
- выдаёт modern-history/modern-history-q97: ответ 1861 год; зацепка Отмена крепостного права, та же строка
- видна в 2: modern-history/modern-history-q101, modern-history/modern-history-q98

## 俄罗斯联邦总统 — Президент Российской Федерации — первым на этот пост в 1991 году избран Борис Ельцин (название ответа)

- выдаёт 2023-24-mun-udm-5: ответ 1991; зацепка Российская Федерация
- выдаёт modern-history/modern-history-q33: ответ 俄罗斯联邦总统, президент Российской Федерации; зацепка 1991 год, Борис Ельцин, та же строка
- видна в 5: modern-history/modern-history-q103, modern-history/modern-history-q104, modern-history/modern-history-q29, modern-history/modern-history-q31, modern-history/modern-history-q33

## 元宵节 — Праздник фонарей — 15-е число 1-го лунного месяца, едят танъюань (название ответа)

- выдаёт 2021-22-mun-mosobl-53: ответ танъюань; зацепка Праздник фонарей
- выдаёт holidays/holidays-q45: ответ 元宵节, Праздник фонарей; зацепка танъюань, та же строка
- видна в 6: holidays/holidays-q16, holidays/holidays-q43, holidays/holidays-q44, holidays/holidays-q45, holidays/holidays-q46, holidays/holidays-q47

## 刘邦 — Лю Бан — основатель династии Хань, победитель в войне Чу и Хань

- выдаёт dynasties/dynasties-q115: ответ династия Хань; зацепка Лю Бан, 刘邦
- выдаёт dynasties/dynasties-q92: ответ война Чу и Хань; зацепка Лю Бан, 刘邦, та же строка
- видна в 3: dynasties/dynasties-q09, dynasties/dynasties-q10, dynasties/dynasties-q39

## 勒拿河 — Лена — на ней стоит Якутск, крупнейший город на вечной мерзлоте

- выдаёт provinces/provinces-q113: ответ Якутск; зацепка река Лена, та же строка
- выдаёт provinces/provinces-q77: ответ Якутск; зацепка вечная мерзлота, та же строка
- видна в 3: provinces/provinces-q104, provinces/provinces-q105, provinces/provinces-q83

## 北京 — Пекин — здесь Храм Неба, где императоры Мин и Цин приносили жертвы Небу

- выдаёт 2022-23-mun-lenobl-52: ответ Храм Неба; зацепка город Пекин
- выдаёт 2024-25-mun-mosobl-4: ответ Храм Неба; зацепка Пекин
- видна в 4: landmarks/landmarks-q48, landmarks/landmarks-q96, landmarks/landmarks-q97, landmarks/landmarks-q98

## 北方首都 — «Северная столица» — прозвище Санкт-Петербурга (название ответа)

- выдаёт 2025-26-mun-chel-5: ответ Петербург, Санкт-Петербург; зацепка Северная столица
- выдаёт provinces/provinces-q106: ответ 北方首都, Северная столица; зацепка Санкт-Петербург, та же строка
- видна в 2: provinces/provinces-q106, provinces/provinces-q107

## 台湾 — Тайвань отошёл Японии по Симоносекскому договору 1895 года

- выдаёт modern-history/modern-history-q116: ответ 台湾, Тайвань; зацепка Симоносекский договор, Япония, та же строка
- выдаёт modern-history/modern-history-q78: ответ 1895 год; зацепка Симоносекский договор, та же строка
- видна в 1: modern-history/modern-history-q115

## 圣彼得堡 — Санкт-Петербург — «Северная столица» в устье Невы

- выдаёт 2025-26-mun-chel-5: ответ 圣彼得堡, Петербург, Санкт-Петербург; зацепка Северная столица
- выдаёт provinces/provinces-q106: ответ Северная столица; зацепка Санкт-Петербург, та же строка
- видна в 15: provinces/provinces-q108, provinces/provinces-q113, provinces/provinces-q114, provinces/provinces-q124, provinces/provinces-q64, provinces/provinces-q65, provinces/provinces-q66, provinces/provinces-q67, provinces/provinces-q68, provinces/provinces-q69, provinces/provinces-q70, provinces/provinces-q71, provinces/provinces-q75, provinces/provinces-q77, provinces/provinces-q85

## 孙中山 — Сунь Ятсен — революционер, в 1912 г. временный президент Китайской Республики

- выдаёт 2020-21-reg-q227d55: ответ 1912; зацепка Китайская Республика
- выдаёт modern-history/modern-history-q96: ответ 孙中山, Сунь Ятсен; зацепка Китайская Республика, временный президент Китайской Республики, та же строка
- видна в 3: modern-history/modern-history-q04, modern-history/modern-history-q12, modern-history/modern-history-q17

## 孙中山 — Сунь Ятсен — руководитель Синьхайской революции 1911 года

- выдаёт 2015-16-shk-60: ответ 1911 год, 1911; зацепка Синьхайская революция, та же строка
- выдаёт modern-history/modern-history-q111: ответ 孙中山, Сунь Ятсен; зацепка Синьхайская революция, та же строка
- видна в 5: modern-history/modern-history-q109, modern-history/modern-history-q110, modern-history/modern-history-q113, modern-history/modern-history-q60, modern-history/modern-history-q66

## 寒食节 — Ханьши — праздник холодной пищи в память Цзе Цзытуя, погибшего в огне

- выдаёт holidays/holidays-q11: ответ Цзе Цзытуй; зацепка праздник Ханьши, праздник холодной пищи, та же строка
- выдаёт holidays/holidays-q34: ответ 寒食节, праздник холодной пищи; зацепка Цзе Цзытуй, та же строка
- видна в 1: holidays/holidays-q33

## 山东 — Шаньдун — здесь Тайшань, Восточный пик пяти священных гор

- выдаёт nature/nature-q146: ответ 山东; зацепка Тайшань, та же строка
- выдаёт nature/nature-q47: ответ Тайшань; зацепка пять священных гор, та же строка
- видна в 7: nature/nature-q03, nature/nature-q145, nature/nature-q147, nature/nature-q148, nature/nature-q149, nature/nature-q23, nature/nature-q50

## 山西 — Шаньси — здесь гора 恒山 (Хэншань), Северный пик пяти священных гор

- выдаёт nature/nature-q03: ответ 山西; зацепка 恒山, та же строка
- выдаёт nature/nature-q49: ответ 恒山; зацепка Северный пик, пять священных гор, та же строка
- видна в 6: nature/nature-q145, nature/nature-q146, nature/nature-q147, nature/nature-q149, nature/nature-q23, nature/nature-q50

## 广东 — Гуандун — родина кантонской вышивки, одной из четырёх знаменитых в Китае

- выдаёт 2024-25-mun-irk-10: ответ кантонская вышивка; зацепка провинция Гуандун
- выдаёт ethnos/ethnos-q86: ответ кантонский; зацепка провинция Гуандун, 广东
- видна в 1: crafts/crafts-q132

## 明 — Мин (1368–1644) — при ней, в 1406–1420 годах, построен Запретный город

- выдаёт 2016-17-mun-8: ответ Запретный город; зацепка династия Мин
- выдаёт landmarks/landmarks-q90: ответ 明; зацепка Запретный город, та же строка
- видна в 1: landmarks/landmarks-q91

## 春节 — Праздник весны — Новый год по лунному календарю, с 2024 года в списке ЮНЕСКО

- выдаёт holidays/holidays-q32: ответ 春节, Праздник весны; зацепка 2024 год, та же строка
- выдаёт holidays/holidays-q53: ответ 春节, Праздник весны; зацепка Новый год, та же строка
- видна в 7: holidays/holidays-q01, holidays/holidays-q02, holidays/holidays-q04, holidays/holidays-q08, holidays/holidays-q09, holidays/holidays-q13, holidays/holidays-q52

## 春节 — Праздник весны — красные надписи и петарды отпугивают чудовище Нянь

- выдаёт holidays/holidays-q05: ответ 春节, Праздник весны; зацепка петарды
- выдаёт holidays/holidays-q33: ответ 春节, Праздник весны; зацепка чудовище Нянь, та же строка
- видна в 1: holidays/holidays-q34

## 曹雪芹 — Цао Сюэцинь — автор романа «Сон в красном тереме»

- выдаёт literature/literature-q16: ответ Сон в красном тереме; зацепка Цао Сюэцинь, та же строка
- выдаёт literature/literature-q97: ответ 曹雪芹, Цао Сюэцинь; зацепка Сон в красном тереме, та же строка
- видна в 6: literature/literature-q01, literature/literature-q03, literature/literature-q09, literature/literature-q101, literature/literature-q40, literature/literature-q96

## 李安 — Ли Ань — режиссёр «Крадущийся тигр, затаившийся дракон» (2000)

- выдаёт cinema/cinema-q03: ответ Крадущийся тигр, затаившийся дракон; зацепка Ли, та же строка
- выдаёт cinema/cinema-q33: ответ 李安, Ли Ань; зацепка Крадущийся тигр, затаившийся дракон, та же строка
- видна в 2: cinema/cinema-q01, cinema/cinema-q32

## 李白 — Ли Бо — «бессмертный поэт» эпохи Тан, автор «Дум тихой ночью»

- выдаёт literature/literature-q23: ответ 李白, Ли Бо; зацепка бессмертный поэт, эпоха Тан
- выдаёт literature/literature-q88: ответ Думы тихой ночью; зацепка Ли Бо, 李白, та же строка
- видна в 8: literature/literature-q01, literature/literature-q02, literature/literature-q03, literature/literature-q07, literature/literature-q101, literature/literature-q24, literature/literature-q25, literature/literature-q46

## 杜甫 — Ду Фу — поэт эпохи Тан, прозванный «мудрецом поэзии»

- выдаёт literature/literature-q07: ответ 杜甫, Ду Фу; зацепка эпоха Тан, та же строка
- выдаёт literature/literature-q24: ответ 杜甫, Ду Фу; зацепка мудрец поэзии, эпоха Тан, та же строка
- видна в 3: literature/literature-q01, literature/literature-q03, literature/literature-q101

## 杨利伟 — Ян Ливэй — первый китайский космонавт, полёт на «Шэньчжоу-5» (2003)

- выдаёт 2025-26-mun-tat-55: ответ 2003; зацепка Шэньчжоу-5
- выдаёт space/space-q01: ответ Шэньчжоу-5; зацепка 2003, Ян Ливэй
- видна в 2: space/space-q12, space/space-q13

## 汤圆 — Танъюань — сладкие рисовые шарики, их едят на Праздник фонарей

- выдаёт 2021-22-mun-mosobl-53: ответ 汤圆, танъюань; зацепка Праздник фонарей
- выдаёт holidays/holidays-q45: ответ Праздник фонарей; зацепка танъюань, 汤圆, та же строка
- видна в 1: holidays/holidays-q07

## 洛阳 — Лоян — город в западной части провинции Хэнань

- выдаёт 2017-18-reg-8: ответ провинция Хэнань; зацепка Лоян, 洛阳
- выдаёт 2024-25-zak-qfce692: ответ 洛阳, Лоян; зацепка провинция Хэнань
- видна в 18: provinces/provinces-q115, provinces/provinces-q116, provinces/provinces-q117, provinces/provinces-q119, provinces/provinces-q121, provinces/provinces-q20, provinces/provinces-q21, provinces/provinces-q22, provinces/provinces-q24, provinces/provinces-q25, provinces/provinces-q26, provinces/provinces-q27, provinces/provinces-q28, provinces/provinces-q29, provinces/provinces-q30, provinces/provinces-q52, provinces/provinces-q53, provinces/provinces-q87

## 洞庭湖 — Дунтинху в Хунани — второе по величине пресноводное озеро Китая

- выдаёт nature/nature-q30: ответ 洞庭湖, Дунтинху; зацепка второе по величине пресноводное озеро Китая, та же строка
- выдаёт provinces/provinces-q90: ответ 洞庭湖, Дунтинху; зацепка Хунань
- видна в 2: nature/nature-q107, nature/nature-q143

## 海景画 — Морской пейзаж — жанр Айвазовского, автора «Девятого вала»

- выдаёт painting/painting-q106: ответ Айвазовский; зацепка Девятый вал
- выдаёт painting/painting-q83: ответ Айвазовский; зацепка морской пейзаж, 海景画, та же строка
- видна в 1: painting/painting-q81

## 湖南 — Хунань — провинция в среднем течении Янцзы, к югу от Дунтинху, центр — Чанша

- выдаёт nature/nature-q142: ответ 湖南; зацепка Дунтинху
- выдаёт provinces/provinces-q90: ответ Дунтинху; зацепка Хунань
- видна в 12: provinces/provinces-q01, provinces/provinces-q02, provinces/provinces-q04, provinces/provinces-q05, provinces/provinces-q06, provinces/provinces-q07, provinces/provinces-q08, provinces/provinces-q09, provinces/provinces-q10, provinces/provinces-q110, provinces/provinces-q32, provinces/provinces-q42

## 湖南 — Хунань — провинция, где лежит озеро Дунтинху

- выдаёт nature/nature-q142: ответ 湖南; зацепка озеро Дунтинху, та же строка
- выдаёт provinces/provinces-q90: ответ озеро Дунтинху, Дунтинху; зацепка Хунань
- видна в 1: nature/nature-q31

## 皇帝 — Император, титул монарха, введённый Цинь Шихуаном

- выдаёт dynasties/dynasties-q09: ответ Цинь Шихуан; зацепка 皇帝
- выдаёт dynasties/dynasties-q10: ответ Цинь Шихуан; зацепка 皇帝
- видна в 1: 2016-17-reg-1

## 神舟五号 — «Шэньчжоу-5» — корабль первого пилотируемого полёта Китая (2003, Ян Ливэй)

- выдаёт 2025-26-mun-tat-55: ответ 2003; зацепка Шэньчжоу-5
- выдаёт space/space-q01: ответ 神舟五号, Шэньчжоу-5; зацепка 2003, Ян Ливэй, та же строка
- видна в 1: space/space-q20

## 离骚 — «Лисао» — поэма Цюй Юаня, образец чуских строф

- выдаёт literature/literature-q20: ответ 离骚; зацепка Цюй Юань, та же строка
- выдаёт literature/literature-q21: ответ Чуские строфы; зацепка Цюй Юань
- видна в 5: literature/literature-q88, literature/literature-q89, literature/literature-q90, literature/literature-q91, literature/literature-q92

## 红楼梦 — «Сон в красном тереме» — роман Цао Сюэциня об упадке семьи Цзя

- выдаёт literature/literature-q16: ответ 红楼梦, Сон в красном тереме; зацепка Цао Сюэцинь
- выдаёт literature/literature-q97: ответ Цао Сюэцинь; зацепка Сон в красном тереме, 红楼梦
- видна в 5: literature/literature-q88, literature/literature-q89, literature/literature-q90, literature/literature-q91, literature/literature-q92

## 红楼梦 — «Сон в красном тереме», роман Цао Сюэциня, XVIII век

- выдаёт literature/literature-q16: ответ 红楼梦, Сон в красном тереме; зацепка Цао Сюэцинь
- выдаёт literature/literature-q97: ответ Цао Сюэцинь; зацепка Сон в красном тереме, 红楼梦
- видна в 1: 2017-18-shk-4

## 罗贯中 — Ло Гуаньчжун — автор романа «Троецарствие»

- выдаёт literature/literature-q17: ответ Троецарствие, Троецарствия; зацепка Ло Гуаньчжун, та же строка
- выдаёт literature/literature-q96: ответ 罗贯中, Ло Гуаньчжун; зацепка Троецарствие, Троецарствия, та же строка
- видна в 4: literature/literature-q01, literature/literature-q03, literature/literature-q101, literature/literature-q97

## 罪与罚 — «Преступление и наказание» — роман Достоевского из «великого пятикнижия»

- выдаёт literature/literature-q60: ответ Достоевский; зацепка Преступление и наказание, 罪与罚, та же строка
- выдаёт literature/literature-q94: ответ Достоевский; зацепка Преступление и наказание
- видна в 1: literature/literature-q67

## 罪与罚 — «Преступление и наказание» — роман Достоевского, печатался в 1866 г.

- выдаёт literature/literature-q60: ответ Достоевский; зацепка Преступление и наказание, 罪与罚
- выдаёт literature/literature-q94: ответ Достоевский; зацепка Преступление и наказание, та же строка
- видна в 5: literature/literature-q65, literature/literature-q72, literature/literature-q77, literature/literature-q84, literature/literature-q85

## 老舍 — Лао Шэ — автор романа «Рикша» и пьесы «Чайная»

- выдаёт literature/literature-q02: ответ 老舍, Лао Шэ; зацепка Чайная, роман «Рикша», та же строка
- выдаёт literature/literature-q91: ответ роман «Рикша»; зацепка Лао Шэ, 老舍, та же строка
- видна в 7: literature/literature-q01, literature/literature-q03, literature/literature-q04, literature/literature-q43, literature/literature-q46, literature/literature-q96, literature/literature-q97

## 莫言 — Мо Янь — лауреат Нобелевской премии 2012 г., автор «Красного гаоляна»

- выдаёт literature/literature-q49: ответ 莫言, Мо Янь; зацепка Нобелевская премия, та же строка
- выдаёт literature/literature-q92: ответ Красный гаолян; зацепка 莫言, та же строка
- видна в 7: literature/literature-q01, literature/literature-q03, literature/literature-q05, literature/literature-q101, literature/literature-q51, literature/literature-q96, literature/literature-q97

## 西安 — Сиань — древняя столица 13 династий, прежде Чанъань (Шэньси)

- выдаёт provinces/provinces-q37: ответ 西安; зацепка Шэньси
- выдаёт state/state-q06: ответ 西安, Сиань; зацепка Чанъань, та же строка
- видна в 3: state/state-q07, state/state-q08, state/state-q09

## 西安 — Сиань — здесь Большая пагода диких гусей для сутр Сюаньцзана

- выдаёт landmarks/landmarks-q59: ответ Большая пагода диких гусей; зацепка Сюаньцзан, та же строка
- выдаёт landmarks/landmarks-q96: ответ 西安; зацепка Большая пагода диких гусей, та же строка
- видна в 3: landmarks/landmarks-q48, landmarks/landmarks-q97, landmarks/landmarks-q98

## 西湖醋鱼 — Рыба озера Сиху в уксусном соусе — знаменитое блюдо Ханчжоу, чжэцзянская кухня

- выдаёт provinces/provinces-q101: ответ Ханчжоу; зацепка Чжэцзян
- выдаёт provinces/provinces-q87: ответ Ханчжоу; зацепка озеро Сиху
- видна в 1: cuisine/cuisine-q84

## 论语 — «Лунь юй» («Беседы и суждения») — записи слов Конфуция, сделанные учениками

- выдаёт 2016-17-zak-10: ответ 论语, «Лунь юй»; зацепка Конфуций
- выдаёт people/people-q09: ответ 论语, «Лунь юй»; зацепка Конфуций, та же строка
- видна в 1: people/people-q10

## 论语 — «Лунь юй», главная книга конфуцианства, записи учеников Конфуция

- выдаёт 2016-17-zak-10: ответ 论语, «Лунь юй»; зацепка Конфуций, конфуцианство
- выдаёт people/people-q09: ответ 论语, «Лунь юй»; зацепка Конфуций
- видна в 1: 2017-18-shk-4

## 诗体长篇小说 — Роман в стихах — так Пушкин назвал «Евгения Онегина»

- выдаёт literature/literature-q69: ответ 诗体长篇小说; зацепка Евгений Онегин, Пушкин, та же строка
- выдаёт literature/literature-q93: ответ Пушкин; зацепка Евгений Онегин, Роман в стихах, та же строка
- видна в 1: literature/literature-q68

## 贵州 — Гуйчжоу — одна из основных областей расселения мяо

- выдаёт crafts/crafts-q132: ответ 贵州, Гуйчжоу; зацепка Мяо
- выдаёт ethnos/ethnos-q04: ответ 贵州; зацепка Мяо, та же строка
- видна в 2: ethnos/ethnos-q78, ethnos/ethnos-q79

## 道家 — Даосизм — школа, основанная Лао-цзы, автором «Дао дэ цзин»

- выдаёт people/people-q01: ответ Лао-цзы; зацепка «Дао дэ цзин», та же строка
- выдаёт people/people-q10: ответ «Дао дэ цзин»; зацепка Лао-цзы, та же строка
- видна в 2: people/people-q06, people/people-q08

## 道德经 — «Дао дэ цзин» — книга о Дао и дэ в 81 главе, её приписывают Лао-цзы

- выдаёт people/people-q01: ответ Лао-цзы; зацепка «Дао дэ цзин», та же строка
- выдаёт people/people-q10: ответ 道德经, «Дао дэ цзин»; зацепка Лао-цзы, та же строка
- видна в 1: people/people-q09

## 长安 — Чанъань (ныне Сиань) — столица Западной Хань и династии Тан

- выдаёт dynasties/dynasties-q103: ответ 长安, Чанъань; зацепка династия Тан
- выдаёт state/state-q06: ответ Сиань; зацепка Тан, Чанъань
- видна в 4: dynasties/dynasties-q08, dynasties/dynasties-q104, dynasties/dynasties-q105, dynasties/dynasties-q106

## 长安 — Чанъань — прежнее название Сианя, столицы Хань и Тан

- выдаёт dynasties/dynasties-q103: ответ 长安, Чанъань; зацепка Тан
- выдаёт state/state-q06: ответ Сиань; зацепка Тан, Чанъань, та же строка
- видна в 1: state/state-q14

## 阿Q正传 — «Подлинная история А-Кью» — повесть Лу Синя, 1921–1922 гг.

- выдаёт literature/literature-q04: ответ Лу Синь; зацепка Подлинная история А-Кью, та же строка
- выдаёт literature/literature-q90: ответ 阿Q正传, Подлинная история А-Кью, история А-Кью; зацепка Лу Синь, та же строка
- видна в 7: literature/literature-q10, literature/literature-q19, literature/literature-q53, literature/literature-q88, literature/literature-q89, literature/literature-q91, literature/literature-q92

## 阿Q正传 — «Подлинная история А-Кью», повесть Лу Синя, 1921–1922

- выдаёт literature/literature-q04: ответ Лу Синь; зацепка Подлинная история А-Кью
- выдаёт literature/literature-q90: ответ 阿Q正传, Подлинная история А-Кью, история А-Кью; зацепка Лу Синь
- видна в 1: 2017-18-shk-4

## 陀思妥耶夫斯基 — Достоевский — автор «Преступления и наказания» и «Братьев Карамазовых»

- выдаёт literature/literature-q60: ответ 陀思妥耶夫斯基, Достоевский; зацепка Братья Карамазовы, Преступление и наказание, та же строка
- выдаёт literature/literature-q94: ответ 陀思妥耶夫斯基, Достоевский; зацепка Преступление и наказание, та же строка
- видна в 12: literature/literature-q61, literature/literature-q62, literature/literature-q63, literature/literature-q71, literature/literature-q73, literature/literature-q80, literature/literature-q81, literature/literature-q82, literature/literature-q86, literature/literature-q87, literature/literature-q93, literature/literature-q95

## 霸王别姬 — «Прощай, моя наложница» — фильм о судьбах двух актёров пекинской оперы (название ответа)

- выдаёт 2016-17-mun-yar-8: ответ Пекин; зацепка Пекинская опера
- выдаёт cinema/cinema-q02: ответ 霸王别姬, Прощай, моя наложница; зацепка Пекинская опера, та же строка
- видна в 5: cinema/cinema-q02, cinema/cinema-q03, cinema/cinema-q09, cinema/cinema-q31, cinema/cinema-q34

## 饺子 — Цзяоцзы — пельмени, их едят в новогоднюю ночь на Праздник весны

- выдаёт 2019-20-mun-kgd-7: ответ новогодняя ночь; зацепка Праздник весны
- выдаёт holidays/holidays-q42: ответ Праздник весны; зацепка пельмени, 饺子
- видна в 1: holidays/holidays-q07

## 马关条约 — Симоносекский договор 1895 года — итог японо-китайской войны, Тайвань отошёл Японии

- выдаёт modern-history/modern-history-q116: ответ Тайвань; зацепка Симоносекский договор, Япония, та же строка
- выдаёт modern-history/modern-history-q78: ответ 1895 год; зацепка Симоносекский договор, та же строка
- видна в 1: modern-history/modern-history-q108

## 骆驼祥子 — «Рикша» — роман Лао Шэ о рикше, трижды покупавшем коляску

- выдаёт literature/literature-q02: ответ Лао Шэ; зацепка роман «Рикша», та же строка
- выдаёт literature/literature-q91: ответ 骆驼祥子; зацепка Лао Шэ, та же строка
- видна в 11: literature/literature-q10, literature/literature-q11, literature/literature-q13, literature/literature-q16, literature/literature-q17, literature/literature-q18, literature/literature-q19, literature/literature-q88, literature/literature-q89, literature/literature-q90, literature/literature-q92

## 麻沸散 — «Мафэйсань» — обезболивающее для операций, его приписывают Хуа То

- выдаёт addition-b2-12: ответ Хуа То; зацепка «мафэйсань», 麻沸散
- выдаёт people/people-q13: ответ 麻沸散, «мафэйсань»; зацепка Хуа То, та же строка
- видна в 6: people/people-q11, people/people-q12, people/people-q14, people/people-q15, people/people-q16, people/people-q17

## 10 元 — 10 юаней: на обороте Три ущелья Янцзы

- выдаёт money/money-q05: ответ Три ущелья; зацепка 10, та же строка
- видна в 1: money/money-q04

## 10 卢布 — 10 рублей образца 1997 года: Красноярск

- выдаёт money/money-q08: ответ 10 卢布; зацепка 1997 год, та же строка
- видна в 1: money/money-q38

## 1000 卢布 — 1000 рублей образца 1997 года: Ярославль

- выдаёт money/money-q10: ответ Ярославль; зацепка 1997 год, та же строка
- видна в 2: money/money-q08, money/money-q38

## 1812 年 — 1812 год: Бородинское сражение

- выдаёт 2024-25-mun-udm-2: ответ 1812; зацепка Бородинское сражение
- видна в 6: modern-history/modern-history-q100, modern-history/modern-history-q80, modern-history/modern-history-q81, modern-history/modern-history-q82, modern-history/modern-history-q97, modern-history/modern-history-q99

## 1825 年 — 1825 год: восстание декабристов

- выдаёт modern-history/modern-history-q80: ответ 1825 年, 1825 год; зацепка Восстание декабристов, та же строка
- видна в 5: modern-history/modern-history-q100, modern-history/modern-history-q81, modern-history/modern-history-q82, modern-history/modern-history-q97, modern-history/modern-history-q99

## 1840 年 — 1840 год: начало Первой опиумной войны

- выдаёт modern-history/modern-history-q55: ответ 1840 年, 1840 год; зацепка Первая опиумная война, та же строка
- видна в 4: modern-history/modern-history-q54, modern-history/modern-history-q57, modern-history/modern-history-q59, modern-history/modern-history-q62

## 1851 年 — 1851 год: Цзиньтяньское восстание, начало Тайпинского восстания

- выдаёт modern-history/modern-history-q57: ответ 1851 年, 1851 год; зацепка Тайпинское восстание, та же строка
- видна в 5: modern-history/modern-history-q54, modern-history/modern-history-q55, modern-history/modern-history-q56, modern-history/modern-history-q59, modern-history/modern-history-q62

## 1853 年 — 1853 год: начало Крымской войны

- выдаёт modern-history/modern-history-q81: ответ 1853 年, 1853 год; зацепка Крымская война, та же строка
- видна в 5: modern-history/modern-history-q100, modern-history/modern-history-q80, modern-history/modern-history-q82, modern-history/modern-history-q97, modern-history/modern-history-q99

## 1856 年 — 1856 год: начало Второй опиумной войны

- выдаёт modern-history/modern-history-q56: ответ 1856 年, 1856 год; зацепка Вторая опиумная война, та же строка
- видна в 4: modern-history/modern-history-q54, modern-history/modern-history-q57, modern-history/modern-history-q59, modern-history/modern-history-q62

## 1860 年 — 1860 год: Пекинские договоры — английский и русский

- выдаёт modern-history/modern-history-q108: ответ Пекинский договор; зацепка 1860 год, та же строка
- видна в 2: modern-history/modern-history-q78, modern-history/modern-history-q92

## 1861 年 — 1861 год: отмена крепостного права

- выдаёт modern-history/modern-history-q97: ответ 1861 年, 1861 год; зацепка Отмена крепостного права, та же строка
- видна в 5: modern-history/modern-history-q100, modern-history/modern-history-q80, modern-history/modern-history-q81, modern-history/modern-history-q82, modern-history/modern-history-q99

## 1894 年 — 1894 год: начало японо-китайской войны

- выдаёт modern-history/modern-history-q59: ответ 1894 年, 1894 год; зацепка Японо-китайская война, та же строка
- видна в 5: modern-history/modern-history-q54, modern-history/modern-history-q55, modern-history/modern-history-q56, modern-history/modern-history-q57, modern-history/modern-history-q62

## 1911 年 — 1911 год: Синьхайская революция

- выдаёт 2015-16-shk-60: ответ 1911 год, 1911; зацепка Синьхайская революция, та же строка
- видна в 9: modern-history/modern-history-q112, modern-history/modern-history-q54, modern-history/modern-history-q55, modern-history/modern-history-q56, modern-history/modern-history-q57, modern-history/modern-history-q59, modern-history/modern-history-q62, modern-history/modern-history-q68, modern-history/modern-history-q71

## 1919 年 — 1919 год: Движение 4 мая

- выдаёт 2016-17-reg-6: ответ 1919; зацепка Движение 4 мая, та же строка
- видна в 3: modern-history/modern-history-q112, modern-history/modern-history-q68, modern-history/modern-history-q71

## 1919 年 — 1919 — «Движение 4 мая» в Пекине

- выдаёт 2016-17-reg-6: ответ 1919; зацепка Движение 4 мая
- видна в 1: 2025-26-shk-31

## 1919 年 — 1919 — Движение 4 мая, студенческие протесты в Пекине

- выдаёт 2016-17-reg-6: ответ 1919; зацепка Движение 4 мая
- видна в 1: 2015-16-shk-60

## 1931 年 — 1931 год: Мукденский инцидент, начало японской оккупации Северо-Востока

- выдаёт modern-history/modern-history-q69: ответ Мукден; зацепка 1931 год, та же строка
- видна в 3: modern-history/modern-history-q112, modern-history/modern-history-q68, modern-history/modern-history-q71

## 1934 年 — 1934 год: начало Великого похода Красной армии

- выдаёт modern-history/modern-history-q68: ответ 1934 年, 1934 год; зацепка Великий поход, та же строка
- видна в 2: modern-history/modern-history-q112, modern-history/modern-history-q71

## 1949 年 — 1949 год: «Общая программа» НПКСК, временная конституция

- выдаёт addition-b1-09: ответ НПКСК; зацепка 1949, Общая программа
- видна в 1: state/state-q05

## 1961 年 — 1961 год: полёт Гагарина на «Востоке-1», первый человек в космосе

- выдаёт space/space-q14: ответ Восток-1; зацепка 1961 год, Гагарин
- видна в 1: space/space-q03

## 1963 年 — 1963 год: полёт Терешковой на «Востоке-6», первая женщина в космосе

- выдаёт space/space-q15: ответ Терешкова; зацепка 1963 год, Восток-6
- видна в 1: space/space-q03

## 1970 年 — 1970 год — запуск первого китайского спутника «Дунфанхун-1»

- выдаёт space/space-q20: ответ Дунфанхун-1; зацепка 1970 год
- видна в 1: space/space-q03

## 1970 年 — 1970 — Китай запустил первый искусственный спутник «Дунфанхун-1»

- выдаёт space/space-q20: ответ Дунфанхун-1; зацепка 1970 год
- видна в 1: 2015-16-mun-9

## 1978 年 — 1978 год: III пленум ЦК КПК 11-го созыва начал курс реформ и открытости

- выдаёт modern-history/modern-history-q53: ответ 1978 年, 1978 год; зацепка Реформы и открытость, та же строка
- видна в 2: modern-history/modern-history-q112, modern-history/modern-history-q117

## 1982 年 — 1982 — принята действующая Конституция КНР

- выдаёт state/state-q05: ответ 1982 年; зацепка Действующая конституция
- видна в 1: 2021-22-mun-q97fb5b

## 1999 年 — 1999 год: Аомэнь вернулся под суверенитет Китая

- выдаёт 2016-17-shk-3: ответ Аомэнь; зацепка 1999 год, та же строка
- видна в 3: modern-history/modern-history-q112, modern-history/modern-history-q117, modern-history/modern-history-q53

## 19世纪 — XIX век — тогда в память о 1812 годе построен храм Христа Спасителя

- выдаёт landmarks/landmarks-q109: ответ Храм Христа Спасителя; зацепка 1812 год, та же строка
- видна в 1: landmarks/landmarks-q80

## 200 卢布 — 200 рублей образца 2017 года: Севастополь

- выдаёт money/money-q14: ответ Севастополь; зацепка 2017, та же строка
- видна в 2: money/money-q08, money/money-q38

## 2001 — 2001 — Китай вступил во Всемирную торговую организацию

- выдаёт 2015-16-mun-9: ответ 2001; зацепка Всемирная торговая организация
- видна в 1: 2016-17-mun-4

## 5 卢布 — 5 рублей образца 1997 года: Великий Новгород

- выдаёт money/money-q09: ответ Великий Новгород; зацепка 1997 год, 5, та же строка
- видна в 2: money/money-q08, money/money-q38

## 50 卢布 — 50 рублей образца 1997 года: Санкт-Петербург

- выдаёт 2024-25-zak-qe3452d: ответ Петербург, Санкт-Петербург; зацепка 1997 год, та же строка
- видна в 2: money/money-q08, money/money-q38

## 5000 卢布 — 5000 рублей образца 1997 года: Хабаровск

- выдаёт money/money-q12: ответ Хабаровск; зацепка 1997 год, та же строка
- видна в 2: money/money-q08, money/money-q38

## 一国两制 — «Одна страна — две системы» — принцип воссоединения Китая, выдвинутый Дэн Сяопином

- выдаёт modern-history/modern-history-q28: ответ Дэн Сяопин; зацепка одна страна — две системы, 一国两制, та же строка
- видна в 5: modern-history/modern-history-q11, modern-history/modern-history-q24, modern-history/modern-history-q26, modern-history/modern-history-q27, modern-history/modern-history-q93

## 一带一路 — «Один пояс, один путь» — китайская инициатива 2013 года, а не организация

- выдаёт 2021-22-mun-q833ea2: ответ 2013 год, 2013; зацепка Один пояс, один путь
- видна в 2: modern-china/modern-china-q10, modern-china/modern-china-q11

## 一月七日 — 7 января по григорианскому календарю — Рождество в России (25 декабря по юлианскому)

- выдаёт holidays/holidays-q50: ответ 一月七日; зацепка Рождество, та же строка
- видна в 3: holidays/holidays-q26, holidays/holidays-q31, holidays/holidays-q51

## 一月二十七日 — 27 января — День воинской славы: снятие блокады Ленинграда

- выдаёт modern-history/modern-history-q86: ответ 一月二十七日, 27 января; зацепка Блокада Ленинграда, та же строка
- видна в 1: modern-history/modern-history-q85

## 三个代表 — «Три представительства» — важная идея, главный создатель которой — Цзян Цзэминь

- выдаёт modern-history/modern-history-q26: ответ 三个代表, три представительства; зацепка Цзян Цзэминь, та же строка
- видна в 4: modern-history/modern-history-q11, modern-history/modern-history-q24, modern-history/modern-history-q27, modern-history/modern-history-q93

## 三位一体 — «Троица» — икона Андрея Рублёва XV века

- выдаёт painting/painting-q105: ответ 三位一体; зацепка Андрей Рублёв
- видна в 3: painting/painting-q86, painting/painting-q88, painting/painting-q94

## 三勇士 — «Богатыри» — картина Виктора Васнецова о трёх былинных героях

- выдаёт painting/painting-q80: ответ Виктор Васнецов; зацепка Богатыри, та же строка
- видна в 1: painting/painting-q105

## 三月十二日 — 12 марта по солнечному календарю — День посадки деревьев

- выдаёт 2018-19-reg-6: ответ 三月十二日; зацепка День посадки деревьев, та же строка
- видна в 4: holidays/holidays-q03, holidays/holidays-q21, holidays/holidays-q38, holidays/holidays-q39

## 三维动画 — Трёхмерная анимация — так снят фильм «Нэчжа: Рождение демона» (2019)

- выдаёт cinema/cinema-q18: ответ Нэчжа: Рождение демона; зацепка 2019, та же строка
- видна в 2: cinema/cinema-q13, cinema/cinema-q14

## 上海合作组织 — ШОС — организация, основанная в 2001 году в Шанхае; Россия и Китай — её члены (название ответа)

- выдаёт provinces/provinces-q29: ответ 上海, Шанхай; зацепка 2001 год
- видна в 1: modern-china/modern-china-q10

## 下西洋 — Плавания в «Западный океан» — семь походов флота Чжэн Хэ, 1405–1433 гг.

- выдаёт people/people-q19: ответ 下西洋, плавания в Западный океан; зацепка Чжэн Хэ, та же строка
- видна в 2: people/people-q18, people/people-q20

## 世界屋脊 — Крыша мира — так называют Цинхай-Тибетское нагорье

- выдаёт nature/nature-q13: ответ Тибетское нагорье, Цинхай-Тибетское нагорье; зацепка крыша мира, 世界屋脊, та же строка
- видна в 1: nature/nature-q60

## 东方6号 — «Восток-6» — корабль Терешковой, первой женщины в космосе (1963)

- выдаёт space/space-q15: ответ Терешкова; зацепка Восток-6, та же строка
- видна в 1: space/space-q14

## 东方明珠 — «Восточная жемчужина» — телебашня в Шанхае высотой 468 м

- выдаёт 2018-19-mun-lenobl-49: ответ Шанхай; зацепка Телебашня «Восточная жемчужина», 东方明珠
- видна в 1: landmarks/landmarks-q106

## 东汉 — Восточная Хань (25–220) — эпоха бронзового «Летящего коня» из Увэя

- выдаёт crafts/crafts-q133: ответ 东汉, Восточная Хань; зацепка бронза, та же строка
- видна в 1: crafts/crafts-q01

## 中共中央主席 — Председатель ЦК КПК — пост, который Мао Цзэдун занимал до смерти в 1976 году

- выдаёт 2024-25-mun-spb-8: ответ 1976 год, 1976; зацепка Мао Цзэдун
- видна в 1: modern-history/modern-history-q95

## 中华人民共和国主席 — Председатель КНР — глава государства, избирается ВСНП

- выдаёт 2016-17-reg-1: ответ 主席, Председатель; зацепка Глава государства, та же строка
- видна в 3: state/state-q01, state/state-q04, state/state-q16

## 中国人民解放军总司令 — Главнокомандующий НОАК — пост Чжу Дэ, первого из десяти маршалов КНР

- выдаёт modern-history/modern-history-q25: ответ Чжу Дэ; зацепка 中国人民解放军总司令, та же строка
- видна в 1: modern-history/modern-history-q95

## 中国人民银行 — Народный банк Китая — центральный банк КНР, ведомство Госсовета

- выдаёт 2016-17-mun-3: ответ 中国人民银行, Народный банк Китая; зацепка Центральный банк
- видна в 3: state/state-q01, state/state-q04, state/state-q16

## 中国航天 — Китайская космонавтика — её основоположником называют Цянь Сюэсэня

- выдаёт people/people-q15: ответ 中国航天, китайская космонавтика; зацепка Цянь Сюэсэнь, та же строка
- видна в 6: people/people-q11, people/people-q12, people/people-q13, people/people-q14, people/people-q16, people/people-q17

## 中秋节 — Праздник середины осени — 15-е число 8-го лунного месяца: луна и юэбины

- выдаёт holidays/holidays-q07: ответ юэбины; зацепка Праздник середины осени, 中秋节, та же строка
- видна в 19: holidays/holidays-q01, holidays/holidays-q02, holidays/holidays-q04, holidays/holidays-q05, holidays/holidays-q08, holidays/holidays-q09, holidays/holidays-q13, holidays/holidays-q16, holidays/holidays-q32, holidays/holidays-q33, holidays/holidays-q34, holidays/holidays-q41, holidays/holidays-q42, holidays/holidays-q43, holidays/holidays-q44, holidays/holidays-q45, holidays/holidays-q46, holidays/holidays-q47, holidays/holidays-q53

## 中苏友好同盟互助条约 — Договор о дружбе, союзе и взаимной помощи СССР и КНР, подписан 14 февраля 1950 года

- выдаёт modern-history/modern-history-q92: ответ 1950 год; зацепка Договор о дружбе, союзе и взаимной помощи, та же строка
- видна в 2: modern-history/modern-history-q108, modern-history/modern-history-q52

## 临安 — Линьань (ныне Ханчжоу) — столица Южной Сун

- выдаёт dynasties/dynasties-q08: ответ 临安, Линьань; зацепка Ханчжоу, Южная Сун, та же строка
- видна в 5: dynasties/dynasties-q103, dynasties/dynasties-q104, dynasties/dynasties-q105, dynasties/dynasties-q106, dynasties/dynasties-q20

## 临安 — Линьань — название Ханчжоу как столицы Южной Сун

- выдаёт dynasties/dynasties-q08: ответ 临安, Линьань; зацепка Ханчжоу, Южная Сун
- видна в 1: state/state-q14

## 乌苏里江以东 — Уссурийский край отошёл России по Пекинскому договору 1860 года

- выдаёт modern-history/modern-history-q108: ответ Пекинский договор; зацепка 1860 год, та же строка
- видна в 2: modern-history/modern-history-q115, modern-history/modern-history-q116

## 乌鲁木齐 — Урумчи — центр Синьцзян-Уйгурского автономного района

- выдаёт provinces/provinces-q96: ответ 乌鲁木齐, Урумчи; зацепка Синьцзян, та же строка
- видна в 10: provinces/provinces-q100, provinces/provinces-q101, provinces/provinces-q33, provinces/provinces-q35, provinces/provinces-q36, provinces/provinces-q37, provinces/provinces-q38, provinces/provinces-q92, provinces/provinces-q97, provinces/provinces-q99

## 九华山 — Цзюхуашань — буддийская гора в Аньхое, высшая точка — 1344 м

- выдаёт nature/nature-q149: ответ Аньхой; зацепка Цзюхуашань, 九华山, та же строка
- видна в 4: nature/nature-q144, nature/nature-q156, nature/nature-q46, nature/nature-q51

## 九月一日 — 1 сентября по григорианскому календарю — День знаний в России

- выдаёт holidays/holidays-q26: ответ 九月一日; зацепка День знаний, та же строка
- видна в 3: holidays/holidays-q31, holidays/holidays-q50, holidays/holidays-q51

## 九月初九 — 9-е число 9-го лунного месяца — праздник Чунъян

- выдаёт holidays/holidays-q37: ответ 九月初九; зацепка праздник Чунъян, та же строка
- видна в 4: holidays/holidays-q03, holidays/holidays-q14, holidays/holidays-q35, holidays/holidays-q36

## 九月十日 — 10 сентября по солнечному календарю — День учителя в Китае

- выдаёт holidays/holidays-q02: ответ День учителя; зацепка 10, 九月十日, та же строка
- видна в 4: holidays/holidays-q03, holidays/holidays-q21, holidays/holidays-q38, holidays/holidays-q39

## 九级浪 — «Девятый вал» — морская картина Айвазовского, 1850 год

- выдаёт painting/painting-q106: ответ Айвазовский; зацепка Девятый вал, 九级浪, та же строка
- видна в 3: painting/painting-q86, painting/painting-q88, painting/painting-q94

## 九级浪 — «Девятый вал» — морская картина Ивана Айвазовского 1850 года

- выдаёт painting/painting-q106: ответ Иван Айвазовский, Айвазовский; зацепка Девятый вал, 九级浪
- видна в 1: painting/painting-q105

## 九转大肠 — Свиные кишки «девять оборотов» — традиционное блюдо Цзинаня, шаньдунская кухня

- выдаёт cuisine/cuisine-q79: ответ Шаньдунская кухня; зацепка 九转大肠
- видна в 1: cuisine/cuisine-q84

## 乞巧 — Девушки просят у Ткачихи мастерства в рукоделии — обычай праздника Циси

- выдаёт holidays/holidays-q15: ответ 乞巧; зацепка праздник Циси, та же строка
- видна в 1: holidays/holidays-q06

## 乾隆 — Император Цяньлун — правил 60 лет, по его указу составлен «Сыку цюаньшу»

- выдаёт dynasties/dynasties-q12: ответ 乾隆, император Цяньлун; зацепка Сыку цюаньшу, та же строка
- видна в 6: dynasties/dynasties-q09, dynasties/dynasties-q10, dynasties/dynasties-q11, dynasties/dynasties-q32, dynasties/dynasties-q35, dynasties/dynasties-q39

## 二十世纪 — XX век — перенос столицы из Петрограда в Москву (1918)

- выдаёт 2018-19-mun-54: ответ 1918; зацепка Москва, Петроград
- видна в 1: 2018-19-reg-8

## 云南 — Юньнань — здесь Каменный лес (Шилинь) под Куньмином

- выдаёт nature/nature-q159: ответ 云南, Юньнань; зацепка Каменный лес, та же строка
- видна в 2: nature/nature-q157, nature/nature-q158

## 云南 — Юньнань — здесь дай живут в бамбуковых домах на сваях чжулоу

- выдаёт ethnos/ethnos-q78: ответ 云南; зацепка дай
- видна в 1: ethnos/ethnos-q84

## 云南 — Юньнань — здесь живут дай, одна из их главных областей — Сишуанбаньна

- выдаёт ethnos/ethnos-q78: ответ 云南; зацепка дай, та же строка
- видна в 1: ethnos/ethnos-q79

## 五月初五 — 5-е число 5-го лунного месяца — праздник Дуаньу

- выдаёт holidays/holidays-q01: ответ праздник Дуаньу; зацепка 五月初五, та же строка
- видна в 5: holidays/holidays-q03, holidays/holidays-q14, holidays/holidays-q35, holidays/holidays-q36, holidays/holidays-q37

## 五月四日 — 4 мая по солнечному календарю — День молодёжи в Китае

- выдаёт holidays/holidays-q39: ответ 五月四日; зацепка День молодёжи, та же строка
- видна в 3: holidays/holidays-q03, holidays/holidays-q21, holidays/holidays-q38

## 亚历山大·涅夫斯基 — Александр Невский — князь, разбил немецких рыцарей на Чудском озере в 1242 году

- выдаёт dynasties/dynasties-q58: ответ 亚历山大·涅夫斯基, Александр Невский; зацепка 1242 год
- видна в 2: modern-history/modern-history-q101, modern-history/modern-history-q98

## 京剧 — Пекинская опера (цзинцзюй) — самый известный вид китайской музыкальной драмы (название ответа)

- выдаёт 2016-17-mun-yar-8: ответ Пекин; зацепка Пекинская опера, 京剧
- видна в 2: landmarks/landmarks-q76, landmarks/landmarks-q89

## 京张铁路 — Железная дорога Пекин — Чжанцзякоу — её строил Чжань Тянью в 1905–1909 гг.

- выдаёт people/people-q14: ответ 京张铁路, железная дорога Пекин — Чжанцзякоу; зацепка Чжань Тянью, та же строка
- видна в 6: people/people-q11, people/people-q12, people/people-q13, people/people-q15, people/people-q16, people/people-q17

## 人民团结日 — День народного единства — 4 ноября, освобождение Москвы ополчением в 1612 году (название ответа)

- выдаёт 2023-24-shk-29: ответ 1612; зацепка Москва
- видна в 6: holidays/holidays-q10, holidays/holidays-q23, holidays/holidays-q24, holidays/holidays-q25, holidays/holidays-q28, holidays/holidays-q52

## 伊万·希施金 — Шишкин — пейзажист XIX века, автор «Утра в сосновом лесу»

- выдаёт painting/painting-q107: ответ 伊万·希施金, Шишкин; зацепка Утро в сосновом лесу, сосна, та же строка
- видна в 6: painting/painting-q106, painting/painting-q80, painting/painting-q82, painting/painting-q83, painting/painting-q85, painting/painting-q89

## 伊万·艾瓦佐夫斯基 — Айвазовский — художник XIX века, автор «Девятого вала»

- выдаёт painting/painting-q106: ответ 伊万·艾瓦佐夫斯基, Айвазовский; зацепка Девятый вал, та же строка
- видна в 5: painting/painting-q107, painting/painting-q80, painting/painting-q82, painting/painting-q85, painting/painting-q89

## 伊利亚·列宾 — Репин — русский реалист XIX века, автор «Бурлаков на Волге»

- выдаёт painting/painting-q86: ответ Бурлаки на Волге; зацепка Илья Репин, 伊利亚·列宾, та же строка
- видна в 7: painting/painting-q106, painting/painting-q107, painting/painting-q80, painting/painting-q82, painting/painting-q83, painting/painting-q85, painting/painting-q89

## 伊萨克·列维坦 — Левитан — пейзажист XIX века, автор «Над вечным покоем»

- выдаёт painting/painting-q85: ответ 伊萨克·列维坦, Левитан; зацепка Над вечным покоем, та же строка
- видна в 6: painting/painting-q106, painting/painting-q107, painting/painting-q80, painting/painting-q82, painting/painting-q83, painting/painting-q89

## 伏尔加河 — Волга — при её слиянии с Окой стоит Нижний Новгород, родина Горького

- выдаёт provinces/provinces-q75: ответ Нижний Новгород; зацепка Волга, та же строка
- видна в 3: provinces/provinces-q104, provinces/provinces-q105, provinces/provinces-q83

## 伏尔加河 — Волга — самая длинная река Европы, впадает в Каспийское море

- выдаёт nature/nature-q160: ответ Каспийское море; зацепка Волга, та же строка
- видна в 9: nature/nature-q05, nature/nature-q101, nature/nature-q102, nature/nature-q103, nature/nature-q104, nature/nature-q105, nature/nature-q106, nature/nature-q127, nature/nature-q128

## 伏尔加河上的纤夫 — «Бурлаки на Волге» — картина Ильи Репина о тяжёлом труде бурлаков

- выдаёт painting/painting-q86: ответ 伏尔加河上的纤夫, Бурлаки на Волге; зацепка Илья Репин
- видна в 1: painting/painting-q105

## 会子 — Хуэйцзы — бумажные деньги Южной Сун, печатались в Линьани (Ханчжоу)

- выдаёт dynasties/dynasties-q08: ответ Линьань; зацепка Ханчжоу, Южная Сун
- видна в 5: money/money-q19, money/money-q21, money/money-q25, money/money-q26, money/money-q27

## 傣族 — Дайцы — народ юга Юньнани, их Новый год — праздник воды

- выдаёт holidays/holidays-q18: ответ Праздник воды; зацепка Новый год, народ дай, 傣族, та же строка
- видна в 3: holidays/holidays-q12, holidays/holidays-q17, holidays/holidays-q40

## 元 — Династия Юань — монгольская, 1271–1368, основал Хубилай

- выдаёт 2015-16-zak-5: ответ монголы; зацепка династия Юань, та же строка
- видна в 6: dynasties/dynasties-q01, dynasties/dynasties-q07, dynasties/dynasties-q107, dynasties/dynasties-q108, dynasties/dynasties-q115, dynasties/dynasties-q22

## 元 — Юань (1271–1368) — при ней в Цзиндэчжэне появился зрелый сине-белый фарфор

- выдаёт crafts/crafts-q01: ответ 元; зацепка Цзиндэчжэнь, сине-белый фарфор, та же строка
- видна в 1: crafts/crafts-q133

## 元代 — Династия Юань — монгольская, 1271–1368, основал Хубилай

- выдаёт 2015-16-zak-5: ответ монголы; зацепка династия Юань
- видна в 2: dynasties/dynasties-q02, dynasties/dynasties-q05

## 元朝 — Династия Юань — монгольская, 1271–1368, основал Хубилай

- выдаёт 2015-16-zak-5: ответ монголы; зацепка династия Юань, 元朝, та же строка
- видна в 9: dynasties/dynasties-q03, dynasties/dynasties-q04, dynasties/dynasties-q06, dynasties/dynasties-q109, dynasties/dynasties-q110, dynasties/dynasties-q111, dynasties/dynasties-q112, dynasties/dynasties-q114, dynasties/dynasties-q13

## 光绪 — Император Гуансюй — правил в 1875–1908, начал реформы 1898 года

- выдаёт dynasties/dynasties-q35: ответ 光绪, император Гуансюй; зацепка 1898 год, та же строка
- видна в 6: dynasties/dynasties-q09, dynasties/dynasties-q10, dynasties/dynasties-q11, dynasties/dynasties-q12, dynasties/dynasties-q32, dynasties/dynasties-q39

## 全国人民代表大会 — ВСНП — высший орган государственной власти КНР

- выдаёт state/state-q01: ответ 全国人民代表大会, ВСНП; зацепка Высший орган государственной власти, та же строка
- видна в 2: state/state-q04, state/state-q16

## 八月十五 — 15-е число 8-го лунного месяца — Праздник середины осени

- выдаёт holidays/holidays-q36: ответ 八月十五; зацепка Праздник середины осени, та же строка
- видна в 4: holidays/holidays-q03, holidays/holidays-q14, holidays/holidays-q35, holidays/holidays-q37

## 兰亭序 — «Предисловие к Ланьтинскому собранию» — знаменитое сочинение Ван Сичжи

- выдаёт painting/painting-q104: ответ 兰亭序, Предисловие к Ланьтинскому собранию; зацепка Ван Сичжи, та же строка
- видна в 1: painting/painting-q22

## 兰州 — Ланьчжоу — административный центр провинции Ганьсу

- выдаёт provinces/provinces-q38: ответ 兰州, Ланьчжоу; зацепка провинция Ганьсу, та же строка
- видна в 10: provinces/provinces-q100, provinces/provinces-q101, provinces/provinces-q33, provinces/provinces-q35, provinces/provinces-q36, provinces/provinces-q37, provinces/provinces-q92, provinces/provinces-q96, provinces/provinces-q97, provinces/provinces-q99

## 兵家 — Школа стратегов — школа Сунь-цзы, автора «Искусства войны»

- выдаёт people/people-q08: ответ 兵家, школа стратегов; зацепка Сунь-цзы, та же строка
- видна в 2: people/people-q06, people/people-q07

## 兵马俑 — Терракотовая армия — глиняные воины у гробницы Цинь Шихуана близ Сианя

- выдаёт 2016-17-shk-4: ответ Сиань; зацепка Цинь Шихуан, терракотовая армия, 兵马俑
- видна в 1: provinces/provinces-q56

## 内蒙古 — Внутренняя Монголия — автономный район на севере Китая, центр — Хух-Хото

- выдаёт provinces/provinces-q34: ответ Внутренняя Монголия; зацепка Хух-Хото, та же строка
- видна в 2: provinces/provinces-q11, provinces/provinces-q44

## 内蒙古自治区 — Внутренняя Монголия — автономный район на севере Китая, центр — Хух-Хото

- выдаёт provinces/provinces-q34: ответ 内蒙古自治区, Внутренняя Монголия; зацепка Хух-Хото, та же строка
- видна в 4: provinces/provinces-q112, provinces/provinces-q123, provinces/provinces-q16, provinces/provinces-q17

## 农村包围城市 — «Окружение городов деревней» — революционный путь, который проложил Мао Цзэдун

- выдаёт modern-history/modern-history-q24: ответ 农村包围城市, окружение городов деревней; зацепка Мао Цзэдун, та же строка
- видна в 4: modern-history/modern-history-q11, modern-history/modern-history-q26, modern-history/modern-history-q27, modern-history/modern-history-q93

## 冰城 — «Город льда» — прозвище Харбина из-за долгой морозной зимы

- выдаёт provinces/provinces-q52: ответ Харбин; зацепка город льда, 冰城, та же строка
- видна в 2: provinces/provinces-q50, provinces/provinces-q58

## 冰湖战役 — Ледовое побоище — 1242 год, победа Александра Невского над немецкими рыцарями

- выдаёт dynasties/dynasties-q58: ответ Александр Невский; зацепка 1242 год, Ледовое побоище
- видна в 1: modern-history/modern-history-q50

## 出使西域 — Посольство в Западный край — миссия Чжан Цяня, начатая в 138 г. до н. э.

- выдаёт people/people-q18: ответ 出使西域, посольство в Западный край; зацепка Чжан Цянь, та же строка
- видна в 2: people/people-q19, people/people-q20

## 列宁格勒保卫战 — Блокада Ленинграда — оборона города с 8 сентября 1941 до 27 января 1944 года

- выдаёт modern-history/modern-history-q86: ответ 27 января; зацепка Блокада Ленинграда, та же строка
- видна в 1: modern-history/modern-history-q50

## 刘禹锡 — Лю Юйси — поэт и мыслитель эпохи Тан, друг Бо Цзюйи

- выдаёт literature/literature-q25: ответ Бо Цзюйи; зацепка эпоха Тан
- видна в 3: literature/literature-q01, literature/literature-q03, literature/literature-q101

## 刘邦 — Лю Бан — основатель династии Хань, победил Сян Юя в 202 г. до н. э.

- выдаёт dynasties/dynasties-q115: ответ династия Хань; зацепка Лю Бан, 刘邦, та же строка
- видна в 9: dynasties/dynasties-q101, dynasties/dynasties-q102, dynasties/dynasties-q116, dynasties/dynasties-q17, dynasties/dynasties-q21, dynasties/dynasties-q23, dynasties/dynasties-q27, dynasties/dynasties-q28, dynasties/dynasties-q29

## 剁椒鱼头 — Рыбья голова под рубленым перцем — знаменитое блюдо хунаньской кухни

- выдаёт cuisine/cuisine-q82: ответ Хунаньская кухня; зацепка 剁椒鱼头
- видна в 1: cuisine/cuisine-q84

## 剪纸动画 — Бумажная перекладка — так снят цикл «Братья-тыквы»

- выдаёт cinema/cinema-q14: ответ 剪纸动画, бумажная перекладка; зацепка Братья-тыквы, та же строка
- видна в 1: cinema/cinema-q13

## 努尔哈赤 — Нурхаци — объединил чжурчжэней и в 1616 году основал Позднюю Цзинь

- выдаёт dynasties/dynasties-q31: ответ 努尔哈赤, Нурхаци; зацепка чжурчжэни, та же строка
- видна в 8: dynasties/dynasties-q09, dynasties/dynasties-q10, dynasties/dynasties-q11, dynasties/dynasties-q12, dynasties/dynasties-q30, dynasties/dynasties-q32, dynasties/dynasties-q35, dynasties/dynasties-q39

## 北京 — Пекин — здесь Запретный город, императорский дворец Мин и Цин

- выдаёт 2016-17-mun-8: ответ Запретный город; зацепка Пекин, 北京
- видна в 2: landmarks/landmarks-q10, landmarks/landmarks-q94

## 北京 — Пекин — столица Китая, где 4 мая 1919 года студенты вышли на демонстрацию

- выдаёт 2016-17-reg-6: ответ 1919; зацепка 4, та же строка
- видна в 3: modern-history/modern-history-q114, modern-history/modern-history-q63, modern-history/modern-history-q69

## 北京 — Пекин — столица Китая; классический сыхэюань — пекинский

- выдаёт ethnos/ethnos-q83: ответ сыхэюань; зацепка Пекин, 北京, та же строка
- видна в 1: ethnos/ethnos-q84

## 北京条约 — Пекинские договоры 1860 г., завершившие Вторую опиумную войну

- выдаёт modern-history/modern-history-q108: ответ 北京条约, Пекинский договор; зацепка 1860
- видна в 1: 2023-24-zak-8

## 北京条约 — Русско-китайский Пекинский договор 1860 года: к России отошёл Уссурийский край

- выдаёт modern-history/modern-history-q108: ответ 北京条约, Пекинский договор; зацепка 1860 год
- видна в 1: modern-history/modern-history-q52

## 北宋 — Северная Сун — 960–1127, столица Бяньцзин (Кайфэн)

- выдаёт dynasties/dynasties-q104: ответ Бяньцзин; зацепка Северная Сун, та же строка
- видна в 5: dynasties/dynasties-q01, dynasties/dynasties-q07, dynasties/dynasties-q107, dynasties/dynasties-q108, dynasties/dynasties-q115

## 北岳 — Северный пик — Хэншань в Шаньси

- выдаёт nature/nature-q49: ответ Хэншань в Шаньси; зацепка Северный пик, 北岳, та же строка
- видна в 1: nature/nature-q48

## 北魏 — Северная Вэй (386–534) — при ней основан монастырь Шаолинь

- выдаёт landmarks/landmarks-q46: ответ 北魏; зацепка Монастырь Шаолинь, та же строка
- видна в 1: landmarks/landmarks-q92

## 十一月四日 — 4 ноября по григорианскому календарю — День народного единства

- выдаёт holidays/holidays-q51: ответ 十一月四日; зацепка День народного единства, та же строка
- видна в 3: holidays/holidays-q26, holidays/holidays-q31, holidays/holidays-q50

## 十月一日 — 1 октября по солнечному календарю — День образования КНР

- выдаёт holidays/holidays-q38: ответ 十月一日; зацепка День образования КНР, та же строка
- видна в 3: holidays/holidays-q03, holidays/holidays-q21, holidays/holidays-q39

## 十月一日 — 1 октября — День образования КНР

- выдаёт holidays/holidays-q38: ответ 十月一日; зацепка День образования КНР
- видна в 1: 2018-19-reg-6

## 千里江山图 — «Тысяча ли рек и гор» — единственная дошедшая работа Ван Симэна

- выдаёт painting/painting-q03: ответ Ван Симэн; зацепка Тысяча ли рек и гор, Тысячи ли рек и гор, 千里江山图, та же строка
- видна в 1: painting/painting-q103

## 华佗 — Хуа То — врач конца Восточной Хань, «основоположник хирургии»

- выдаёт addition-b2-12: ответ 华佗, Хуа То; зацепка Восточная Хань
- видна в 1: people/people-q05

## 华山 — Хуашань — Западный пик пяти священных гор, в Шэньси

- выдаёт nature/nature-q48: ответ Западный пик; зацепка Хуашань, пять священных гор, та же строка
- видна в 7: nature/nature-q10, nature/nature-q144, nature/nature-q156, nature/nature-q46, nature/nature-q47, nature/nature-q49, nature/nature-q51

## 南京 — Нанкин — «столица шести династий», с 1927 года столица Китайской Республики

- выдаёт state/state-q09: ответ 南京, Нанкин; зацепка 1927 год, та же строка
- видна в 3: state/state-q06, state/state-q07, state/state-q08

## 南京 — Нанкин — город на востоке Китая, в провинции Цзянсу

- выдаёт provinces/provinces-q24: ответ 南京, Нанкин; зацепка Цзянси, Цзянсу, та же строка
- видна в 17: provinces/provinces-q115, provinces/provinces-q116, provinces/provinces-q117, provinces/provinces-q119, provinces/provinces-q121, provinces/provinces-q20, provinces/provinces-q21, provinces/provinces-q22, provinces/provinces-q25, provinces/provinces-q26, provinces/provinces-q27, provinces/provinces-q28, provinces/provinces-q29, provinces/provinces-q30, provinces/provinces-q52, provinces/provinces-q53, provinces/provinces-q87

## 南京 — Нанкин — центр провинции Цзянсу

- выдаёт provinces/provinces-q24: ответ 南京, Нанкин; зацепка Цзянси, Цзянсу
- видна в 11: provinces/provinces-q100, provinces/provinces-q101, provinces/provinces-q33, provinces/provinces-q35, provinces/provinces-q36, provinces/provinces-q37, provinces/provinces-q38, provinces/provinces-q92, provinces/provinces-q96, provinces/provinces-q97, provinces/provinces-q99

## 南宋 — Южная Сун — 1127–1279, столица Линьань (Ханчжоу)

- выдаёт dynasties/dynasties-q08: ответ Линьань; зацепка Ханчжоу, Южная Сун, та же строка
- видна в 6: dynasties/dynasties-q01, dynasties/dynasties-q07, dynasties/dynasties-q107, dynasties/dynasties-q108, dynasties/dynasties-q115, dynasties/dynasties-q22

## 南岳 — Южный пик — Хэншань в Хунани

- выдаёт nature/nature-q10: ответ Хэншань в Хунани; зацепка Хунань, Южный пик, 南岳, та же строка
- видна в 1: nature/nature-q48

## 博罗季诺战役 — Бородинское сражение — генеральное сражение Отечественной войны 1812 года

- выдаёт 2024-25-mun-udm-2: ответ 1812; зацепка Бородинское сражение
- видна в 1: modern-history/modern-history-q50

## 卡拉马佐夫兄弟 — «Братья Карамазовы» — последний роман Достоевского, 1879–1880 гг.

- выдаёт literature/literature-q60: ответ Достоевский; зацепка Братья Карамазовы
- видна в 5: literature/literature-q65, literature/literature-q72, literature/literature-q77, literature/literature-q84, literature/literature-q85

## 古拉格群岛 — «Архипелаг ГУЛАГ» — книга Солженицына о лагерях, первый том вышел в 1973 г.

- выдаёт literature/literature-q82: ответ Солженицын; зацепка Архипелаг ГУЛАГ, та же строка
- видна в 5: literature/literature-q65, literature/literature-q72, literature/literature-q77, literature/literature-q84, literature/literature-q85

## 古罗斯第一部成文法 — «Русская правда» — первый свод законов Руси, связан с Ярославом Мудрым

- выдаёт dynasties/dynasties-q53: ответ Ярослав Мудрый; зацепка Русская правда, та же строка
- видна в 5: dynasties/dynasties-q117, dynasties/dynasties-q118, dynasties/dynasties-q119, dynasties/dynasties-q121, dynasties/dynasties-q122

## 史记 — «Исторические записки» — первая всеобщая история Китая, труд Сыма Цяня

- выдаёт literature/literature-q03: ответ Сыма Цянь; зацепка 史记, та же строка
- видна в 6: literature/literature-q10, literature/literature-q88, literature/literature-q89, literature/literature-q90, literature/literature-q91, literature/literature-q92

## 叶利钦 — Борис Ельцин — первый президент Российской Федерации

- выдаёт modern-history/modern-history-q33: ответ президент Российской Федерации; зацепка Борис Ельцин, та же строка
- видна в 2: modern-history/modern-history-q105, modern-history/modern-history-q106

## 叶甫盖尼·奥涅金 — «Евгений Онегин» — роман в стихах Пушкина о «лишнем человеке», начат в 1823 г.

- выдаёт literature/literature-q93: ответ Пушкин; зацепка Евгений Онегин, та же строка
- видна в 6: literature/literature-q65, literature/literature-q67, literature/literature-q72, literature/literature-q77, literature/literature-q84, literature/literature-q85

## 吃月饼 — Есть лунные пряники — обычай Праздника середины осени

- выдаёт holidays/holidays-q07: ответ 月饼, лунные пряники, лунный пряник; зацепка Праздник середины осени
- видна в 2: holidays/holidays-q06, holidays/holidays-q15

## 合肥 — Хэфэй — центр провинции Аньхой

- выдаёт provinces/provinces-q92: ответ 合肥; зацепка провинция Аньхой, та же строка
- видна в 10: provinces/provinces-q100, provinces/provinces-q101, provinces/provinces-q33, provinces/provinces-q35, provinces/provinces-q36, provinces/provinces-q37, provinces/provinces-q38, provinces/provinces-q96, provinces/provinces-q97, provinces/provinces-q99

## 吉林 — Провинция Гирин (Цзилинь), административный центр — Чанчунь

- выдаёт provinces/provinces-q36: ответ Чанчунь; зацепка Провинция Цзилинь
- видна в 1: 2018-19-shk-6

## 吉林 — Цзилинь — здесь Яньбянь, главная область проживания корейцев Китая

- выдаёт ethnos/ethnos-q79: ответ 吉林; зацепка Корея, корейцы Китая, та же строка
- видна в 1: ethnos/ethnos-q78

## 吉林 — Цзилинь — здесь вулкан Чанбайшань с озером Тяньчи в кратере

- выдаёт nature/nature-q46: ответ Чанбайшань; зацепка озеро Тяньчи, та же строка
- видна в 7: nature/nature-q03, nature/nature-q145, nature/nature-q146, nature/nature-q147, nature/nature-q148, nature/nature-q149, nature/nature-q23

## 吉林 — Цзилинь — провинция на Северо-Востоке, центр — Чанчунь

- выдаёт provinces/provinces-q36: ответ Чанчунь; зацепка Провинция Цзилинь, та же строка
- видна в 14: provinces/provinces-q01, provinces/provinces-q02, provinces/provinces-q03, provinces/provinces-q04, provinces/provinces-q05, provinces/provinces-q06, provinces/provinces-q07, provinces/provinces-q08, provinces/provinces-q09, provinces/provinces-q10, provinces/provinces-q110, provinces/provinces-q122, provinces/provinces-q32, provinces/provinces-q42

## 吉林省 — Цзилинь — провинция на Северо-Востоке, центр — Чанчунь

- выдаёт provinces/provinces-q36: ответ Чанчунь; зацепка Провинция Цзилинь, та же строка
- видна в 8: provinces/provinces-q111, provinces/provinces-q112, provinces/provinces-q12, provinces/provinces-q123, provinces/provinces-q13, provinces/provinces-q14, provinces/provinces-q15, provinces/provinces-q16

## 吴承恩 — У Чэнъэнь — по традиции автор романа «Путешествие на Запад»

- выдаёт literature/literature-q40: ответ 吴承恩, У Чэнъэнь; зацепка Путешествие на Запад, та же строка
- видна в 6: literature/literature-q01, literature/literature-q03, literature/literature-q09, literature/literature-q101, literature/literature-q96, literature/literature-q97

## 吴方言 — Диалект у — диалект Шанхая, юга Цзянсу и большей части Чжэцзяна

- выдаёт 2020-21-pri-qac236e: ответ 吴方言, диалект у; зацепка Цзянси, Цзянсу, Чжэцзян, Шанхай, та же строка
- видна в 4: ethnos/ethnos-q86, ethnos/ethnos-q87, ethnos/ethnos-q88, ethnos/ethnos-q92

## 吴道子 — У Даоцзы — танский «святой живописи», мастер буддийских и даосских фигур

- выдаёт painting/painting-q04: ответ 吴道子, У Даоцзы; зацепка святой живописи, та же строка
- видна в 1: painting/painting-q25

## 呐喊 — «Клич» — первый сборник рассказов Лу Синя, 1923 г.

- выдаёт literature/literature-q53: ответ 呐喊; зацепка Лу Синь, та же строка
- видна в 1: literature/literature-q10

## 呼和浩特 — Хух-Хото («Синий город») — центр Внутренней Монголии

- выдаёт provinces/provinces-q34: ответ Внутренняя Монголия; зацепка Хух-Хото, 呼和浩特, та же строка
- видна в 11: provinces/provinces-q100, provinces/provinces-q101, provinces/provinces-q33, provinces/provinces-q35, provinces/provinces-q36, provinces/provinces-q37, provinces/provinces-q38, provinces/provinces-q92, provinces/provinces-q96, provinces/provinces-q97, provinces/provinces-q99

## 和平共处五项原则 — Пять принципов мирного сосуществования — их в 1953 году впервые выдвинул Чжоу Эньлай

- выдаёт modern-history/modern-history-q07: ответ Чжоу Эньлай; зацепка Пять принципов мирного сосуществования, та же строка
- видна в 5: modern-history/modern-history-q11, modern-history/modern-history-q24, modern-history/modern-history-q26, modern-history/modern-history-q27, modern-history/modern-history-q93

## 哈尔滨 — Харбин — город на северо-востоке Китая, в провинции Хэйлунцзян

- выдаёт 2020-21-mun-mosobl-47: ответ 哈尔滨, Харбин; зацепка провинция Хэйлунцзян
- видна в 17: provinces/provinces-q115, provinces/provinces-q116, provinces/provinces-q117, provinces/provinces-q119, provinces/provinces-q121, provinces/provinces-q20, provinces/provinces-q21, provinces/provinces-q22, provinces/provinces-q24, provinces/provinces-q25, provinces/provinces-q26, provinces/provinces-q27, provinces/provinces-q28, provinces/provinces-q29, provinces/provinces-q30, provinces/provinces-q53, provinces/provinces-q87

## 哈尔滨 — Харбин — здесь остров Солнца на северном берегу Сунгари

- выдаёт landmarks/landmarks-q101: ответ 哈尔滨; зацепка Остров Солнца, та же строка
- видна в 1: landmarks/landmarks-q99

## 哈尔滨 — Харбин — центр провинции Хэйлунцзян

- выдаёт 2020-21-mun-mosobl-47: ответ 哈尔滨, Харбин; зацепка провинция Хэйлунцзян
- видна в 11: provinces/provinces-q100, provinces/provinces-q101, provinces/provinces-q33, provinces/provinces-q35, provinces/provinces-q36, provinces/provinces-q37, provinces/provinces-q38, provinces/provinces-q92, provinces/provinces-q96, provinces/provinces-q97, provinces/provinces-q99

## 哈巴罗夫斯克 — Хабаровск — город на купюре 5000 рублей образца 1997 года

- выдаёт money/money-q12: ответ 哈巴罗夫斯克, Хабаровск; зацепка 1997 год, та же строка
- видна в 7: money/money-q09, money/money-q10, money/money-q11, money/money-q13, money/money-q14, money/money-q15, money/money-q37

## 唐 — Династия Тан — 618–907, основал Ли Юань, столица Чанъань

- выдаёт dynasties/dynasties-q103: ответ Чанъань; зацепка династия Тан, та же строка
- видна в 6: dynasties/dynasties-q01, dynasties/dynasties-q07, dynasties/dynasties-q107, dynasties/dynasties-q108, dynasties/dynasties-q115, dynasties/dynasties-q22

## 唐 — Тан (618–907) — при ней построен дворец Дамин, ныне руины в Сиане

- выдаёт state/state-q06: ответ Сиань; зацепка Тан
- видна в 2: landmarks/landmarks-q90, landmarks/landmarks-q91

## 唐代 — Династия Тан — 618–907, основал Ли Юань, столица Чанъань

- выдаёт dynasties/dynasties-q103: ответ Чанъань; зацепка династия Тан, та же строка
- видна в 3: dynasties/dynasties-q02, dynasties/dynasties-q05, dynasties/dynasties-q15

## 唐朝 — Династия Тан — 618–907, основал Ли Юань, столица Чанъань

- выдаёт dynasties/dynasties-q103: ответ Чанъань; зацепка династия Тан, та же строка
- видна в 9: dynasties/dynasties-q03, dynasties/dynasties-q04, dynasties/dynasties-q06, dynasties/dynasties-q109, dynasties/dynasties-q110, dynasties/dynasties-q111, dynasties/dynasties-q112, dynasties/dynasties-q114, dynasties/dynasties-q13

## 喜剧 — Комедия — жанр «Ревизора» Гоголя (1836)

- выдаёт literature/literature-q68: ответ 喜剧; зацепка Гоголь, Ревизор, та же строка
- видна в 1: literature/literature-q69

## 四川 — Сычуань — здесь Сычуаньская котловина, «страна изобилия»

- выдаёт nature/nature-q59: ответ Сычуаньская котловина; зацепка страна изобилия, та же строка
- видна в 1: nature/nature-q150

## 四川 — Сычуань — здесь буддийская гора Эмэйшань

- выдаёт nature/nature-q11: ответ гора Эмэйшань, Эмэйшань; зацепка Сычуань, 四川, та же строка
- видна в 5: nature/nature-q03, nature/nature-q145, nature/nature-q146, nature/nature-q147, nature/nature-q23

## 四川 — Сычуань — здесь долина Цзючжайгоу с горными озёрами и водопадами

- выдаёт provinces/provinces-q01: ответ 四川, Сычуань; зацепка Цзючжайгоу
- видна в 3: nature/nature-q157, nature/nature-q158, nature/nature-q159

## 四月五日 — Около 5 апреля (4–6 апреля) по солнечному календарю — праздник Цинмин

- выдаёт holidays/holidays-q03: ответ 四月五日; зацепка праздник Цинмин, та же строка
- видна в 3: holidays/holidays-q21, holidays/holidays-q38, holidays/holidays-q39

## 四月十二日 — 12 апреля по григорианскому календарю — День космонавтики

- выдаёт holidays/holidays-q24: ответ День космонавтики; зацепка 12, та же строка
- видна в 4: holidays/holidays-q26, holidays/holidays-q31, holidays/holidays-q50, holidays/holidays-q51

## 回族 — Хуэй (хуэйцзу), народ Китая, исповедующий ислам

- выдаёт ethnos/ethnos-q81: ответ 回族, Хуэй; зацепка ислам
- видна в 1: 2015-16-zak-5

## 园林之城 — «Город садов» — прозвище Сучжоу, где сохранилось больше 60 классических садов

- выдаёт provinces/provinces-q58: ответ 园林之城, город садов; зацепка Сучжоу, та же строка
- видна в 1: provinces/provinces-q50

## 国务院总理 — Премьер Госсовета — первым этот пост занял Чжоу Эньлай в 1954 году

- выдаёт 2022-23-mun-orel-3: ответ Чжоу Эньлай; зацепка премьер Госсовета
- видна в 1: modern-history/modern-history-q95

## 国家主席 — Председатель КНР — краткое название должности главы государства

- выдаёт 2016-17-reg-1: ответ 主席, Председатель; зацепка Глава государства, та же строка
- видна в 2: state/state-q02, state/state-q03

## 图画展览会 — Фортепианный цикл «Картинки с выставки» Модеста Мусоргского

- выдаёт people/people-q23: ответ 图画展览会, «Картинки с выставки»; зацепка Модест Мусоргский, та же строка
- видна в 3: people/people-q21, people/people-q22, people/people-q24

## 圣彼得堡 — Санкт-Петербург — город на купюре 50 рублей образца 1997 года

- выдаёт 2024-25-zak-qe3452d: ответ 圣彼得堡, Петербург, Санкт-Петербург; зацепка 1997 год, та же строка
- видна в 8: money/money-q09, money/money-q10, money/money-q11, money/money-q12, money/money-q13, money/money-q14, money/money-q15, money/money-q37

## 圣母升天大教堂 — Успенский собор Московского Кремля

- выдаёт landmarks/landmarks-q114: ответ 圣母升天大教堂, Успенский собор Московского Кремля; зацепка Московский Кремль, та же строка
- видна в 5: landmarks/landmarks-q109, landmarks/landmarks-q113, landmarks/landmarks-q77, landmarks/landmarks-q78, landmarks/landmarks-q79

## 地动仪 — Сейсмоскоп Чжан Хэна (Восточная Хань) — не из четырёх великих изобретений

- выдаёт people/people-q05: ответ Чжан Хэн; зацепка Восточная Хань
- видна в 1: sets/sets-q01

## 塞瓦斯托波尔 — Севастополь — город на купюре 200 рублей образца 2017 года

- выдаёт money/money-q14: ответ 塞瓦斯托波尔, Севастополь; зацепка 2017, та же строка
- видна в 7: money/money-q09, money/money-q10, money/money-q11, money/money-q12, money/money-q13, money/money-q15, money/money-q37

## 墓地上空 — «Над вечным покоем» — пейзаж Исаака Левитана с церковью над разливом реки

- выдаёт painting/painting-q85: ответ Исаак Левитан, Левитан; зацепка Над вечным покоем, 墓地上空
- видна в 1: painting/painting-q105

## 墓地上空 — «Над вечным покоем» — пейзаж Левитана, 1894 год

- выдаёт painting/painting-q85: ответ Левитан; зацепка Над вечным покоем, 墓地上空, та же строка
- видна в 3: painting/painting-q86, painting/painting-q88, painting/painting-q94

## 墨子 — Мо-цзы — основатель школы «всеобщей любви», соперник конфуцианцев

- выдаёт people/people-q04: ответ 墨子, Мо-цзы; зацепка Конфуций, та же строка
- видна в 1: people/people-q01

## 大兴城 — Дасин — столица Суй, при Тан переименована в Чанъань

- выдаёт dynasties/dynasties-q103: ответ Чанъань; зацепка Тан
- видна в 4: dynasties/dynasties-q08, dynasties/dynasties-q104, dynasties/dynasties-q105, dynasties/dynasties-q106

## 大同 — Датун — возле него высечены пещеры Юньган

- выдаёт landmarks/landmarks-q48: ответ 大同; зацепка Пещеры Юньган, та же строка
- видна в 3: landmarks/landmarks-q96, landmarks/landmarks-q97, landmarks/landmarks-q98

## 大唐芙蓉园 — Датан Фужунъюань — парк в Сиани, воссоздающий облик императорского сада эпохи Тан

- выдаёт state/state-q06: ответ Сиань; зацепка Тан
- видна в 1: landmarks/landmarks-q106

## 大唐芙蓉园 — Датан Фужунъюань, современный парк в Сиане в стиле эпохи Тан

- выдаёт state/state-q06: ответ Сиань; зацепка Тан
- видна в 1: 2023-24-reg-4

## 大禹 — Великий Юй — по преданию, основатель династии Ся, усмиритель потопа

- выдаёт dynasties/dynasties-q101: ответ 大禹, Великий Юй; зацепка династия Ся, та же строка
- видна в 8: dynasties/dynasties-q102, dynasties/dynasties-q116, dynasties/dynasties-q17, dynasties/dynasties-q21, dynasties/dynasties-q23, dynasties/dynasties-q27, dynasties/dynasties-q28, dynasties/dynasties-q29

## 大诺夫哥罗德 — Великий Новгород — город на купюре 5 рублей образца 1997 года

- выдаёт money/money-q09: ответ 大诺夫哥罗德, Великий Новгород; зацепка 1997 год, 5, та же строка
- видна в 7: money/money-q10, money/money-q11, money/money-q12, money/money-q13, money/money-q14, money/money-q15, money/money-q37

## 大足石刻 — Скальные рельефы Дацзу — буддийские, даосские и конфуцианские изваяния близ Чунцина

- выдаёт provinces/provinces-q27: ответ Чунцин; зацепка Дацзу, 大足石刻
- видна в 2: landmarks/landmarks-q55, landmarks/landmarks-q59

## 大都 — Даду — столица династии Юань на месте нынешнего Пекина

- выдаёт dynasties/dynasties-q105: ответ 大都; зацепка династия Юань, та же строка
- видна в 4: dynasties/dynasties-q08, dynasties/dynasties-q103, dynasties/dynasties-q104, dynasties/dynasties-q20

## 天使长大教堂 — Архангельский собор Московского Кремля

- выдаёт landmarks/landmarks-q108: ответ 天使长大教堂, Архангельский собор Московского Кремля; зацепка Московский Кремль, та же строка
- видна в 5: landmarks/landmarks-q109, landmarks/landmarks-q113, landmarks/landmarks-q77, landmarks/landmarks-q78, landmarks/landmarks-q79

## 天山 — Тянь-Шань — хребет в центре Синьцзяна длиной около 1760 км в Китае

- выдаёт nature/nature-q145: ответ Синьцзян; зацепка 天山, та же строка
- видна в 6: nature/nature-q144, nature/nature-q42, nature/nature-q44, nature/nature-q45, nature/nature-q46, nature/nature-q51

## 天府之国 — Страна изобилия — так издавна зовут плодородную Сычуаньскую котловину

- выдаёт nature/nature-q59: ответ Сычуаньская котловина; зацепка страна изобилия, 天府之国, та же строка
- видна в 1: nature/nature-q60

## 天方夜谭 — Симфоническая сюита «Шехеразада» Николая Римского-Корсакова

- выдаёт people/people-q22: ответ 天方夜谭, «Шехеразада»; зацепка Николай Римский-Корсаков, та же строка
- видна в 3: people/people-q21, people/people-q23, people/people-q24

## 天津 — Тяньцзинь — город центрального подчинения на севере Китая, на берегу Бохая

- выдаёт 2015-16-reg-1: ответ 天津, Тяньцзинь; зацепка город центрального подчинения, та же строка
- видна в 18: provinces/provinces-q115, provinces/provinces-q116, provinces/provinces-q117, provinces/provinces-q119, provinces/provinces-q121, provinces/provinces-q20, provinces/provinces-q21, provinces/provinces-q22, provinces/provinces-q24, provinces/provinces-q25, provinces/provinces-q26, provinces/provinces-q27, provinces/provinces-q28, provinces/provinces-q29, provinces/provinces-q30, provinces/provinces-q52, provinces/provinces-q53, provinces/provinces-q87

## 天津市 — Тяньцзинь — город центрального подчинения рядом с Пекином

- выдаёт 2015-16-reg-1: ответ 天津, Тяньцзинь; зацепка город центрального подчинения, та же строка
- видна в 3: provinces/provinces-q112, provinces/provinces-q123, provinces/provinces-q16

## 太原 — Тайюань — центр провинции Шаньси

- выдаёт provinces/provinces-q03: ответ провинция Шаньси; зацепка Тайюань, 太原, та же строка
- видна в 11: provinces/provinces-q100, provinces/provinces-q101, provinces/provinces-q33, provinces/provinces-q35, provinces/provinces-q36, provinces/provinces-q37, provinces/provinces-q38, provinces/provinces-q92, provinces/provinces-q96, provinces/provinces-q97, provinces/provinces-q99

## 契丹族 — Кидани — народ, основавший династию Ляо

- выдаёт dynasties/dynasties-q24: ответ 契丹族, кидани; зацепка династия Ляо, та же строка
- видна в 1: dynasties/dynasties-q113

## 契诃夫 — Чехов — автор пьесы «Вишнёвый сад» и рассказов (название ответа)

- выдаёт literature/literature-q85: ответ Вишнёвый сад; зацепка Чехов, та же строка
- видна в 13: literature/literature-q60, literature/literature-q61, literature/literature-q63, literature/literature-q71, literature/literature-q73, literature/literature-q80, literature/literature-q81, literature/literature-q82, literature/literature-q86, literature/literature-q87, literature/literature-q93, literature/literature-q94, literature/literature-q95

## 女神 — «Богини» — первый сборник стихов Го Можо, 1921 г.

- выдаёт literature/literature-q46: ответ Го Можо; зацепка Богини, та же строка
- видна в 5: literature/literature-q88, literature/literature-q89, literature/literature-q90, literature/literature-q91, literature/literature-q92

## 姚明 — Яо Мин — баскетболист, выступал в НБА за «Хьюстон Рокетс»

- выдаёт 2021-22-mun-lenobl-9: ответ 姚明, Яо Мин; зацепка баскетбол, та же строка
- видна в 1: modern-china/modern-china-q16

## 姚明 — Яо Мин — баскетболист, звезда НБА

- выдаёт 2021-22-mun-lenobl-9: ответ 姚明, Яо Мин; зацепка баскетбол
- видна в 1: space/space-q04

## 孟姜女 — Мэн Цзяннюй — по преданию, оплакала мужа у Великой стены

- выдаёт myths/myths-q19: ответ 孟姜女, Мэн Цзяннюй; зацепка Великая стена, та же строка
- видна в 11: myths/myths-q02, myths/myths-q03, myths/myths-q05, myths/myths-q06, myths/myths-q07, myths/myths-q08, myths/myths-q09, myths/myths-q10, myths/myths-q20, myths/myths-q23, myths/myths-q29

## 孟姜女哭长城 — «Мэн Цзяннюй оплакивает стену» — от её плача обрушилась Великая стена

- выдаёт myths/myths-q19: ответ 孟姜女, Мэн Цзяннюй; зацепка Великая стена
- видна в 4: myths/myths-q18, myths/myths-q21, myths/myths-q22, myths/myths-q30

## 宁夏 — Нинся — автономный район на северо-западе Китая, центр — Иньчуань

- выдаёт provinces/provinces-q97: ответ Иньчуань; зацепка автономный район Нинся, та же строка
- видна в 2: provinces/provinces-q11, provinces/provinces-q44

## 宇航节 — День космонавтики — 12 апреля, в память о полёте Юрия Гагарина (1961)

- выдаёт holidays/holidays-q24: ответ 宇航节, День космонавтики; зацепка 12, та же строка
- видна в 5: holidays/holidays-q10, holidays/holidays-q23, holidays/holidays-q25, holidays/holidays-q28, holidays/holidays-q52

## 安娜·卡列尼娜 — «Анна Каренина» — роман Льва Толстого, печатался в 1875–1877 гг.

- выдаёт literature/literature-q95: ответ Толстой; зацепка Анна Каренина, та же строка
- видна в 4: literature/literature-q72, literature/literature-q77, literature/literature-q84, literature/literature-q85

## 安德烈·鲁勃廖夫 — Рублёв — иконописец XV века, автор иконы «Троица»

- выдаёт painting/painting-q105: ответ икона Троица; зацепка Андрей Рублёв, 安德烈·鲁勃廖夫, та же строка
- видна в 7: painting/painting-q106, painting/painting-q107, painting/painting-q80, painting/painting-q82, painting/painting-q83, painting/painting-q85, painting/painting-q89

## 安徽 — Аньхой — здесь буддийская гора Цзюхуашань

- выдаёт nature/nature-q149: ответ 安徽, Аньхой; зацепка Цзюхуашань, та же строка
- видна в 4: nature/nature-q03, nature/nature-q145, nature/nature-q146, nature/nature-q23

## 小说 — Повествовательная проза — жанр «Героя нашего времени» Лермонтова

- выдаёт literature/literature-q84: ответ Герой нашего времени; зацепка Лермонтов, та же строка
- видна в 1: literature/literature-q68

## 少女与桃 — «Девочка с персиками» — портрет Валентина Серова 1887 года

- выдаёт painting/painting-q88: ответ 少女与桃, Девочка с персиками; зацепка Валентин Серов
- видна в 1: painting/painting-q105

## 屈原 — Цюй Юань — главный автор «Чуских строф», сборника поэзии царства Чу

- выдаёт literature/literature-q21: ответ Чуские строфы; зацепка Цюй Юань, та же строка
- видна в 2: literature/literature-q96, literature/literature-q97

## 屠呦呦 — Ту Юю — фармаколог, лауреат Нобелевской премии за артемизинин

- выдаёт people/people-q17: ответ артемизинин; зацепка Ту Юю, 屠呦呦, та же строка
- видна в 1: people/people-q05

## 屠格涅夫 — Тургенев — автор романа «Отцы и дети» и цикла «Записки охотника»

- выдаёт literature/literature-q81: ответ 屠格涅夫, Тургенев; зацепка Отцы и дети, та же строка
- видна в 13: literature/literature-q60, literature/literature-q61, literature/literature-q62, literature/literature-q63, literature/literature-q71, literature/literature-q73, literature/literature-q80, literature/literature-q82, literature/literature-q86, literature/literature-q87, literature/literature-q93, literature/literature-q94, literature/literature-q95

## 山东 — Шаньдун — родина шаньдунской кухни с блюдом свиные кишки «девять оборотов»

- выдаёт cuisine/cuisine-q67: ответ шаньдунская кухня; зацепка провинция Шаньдун, та же строка
- видна в 3: cuisine/cuisine-q68, cuisine/cuisine-q70, cuisine/cuisine-q71

## 山西 — Шаньси — провинция к западу от гор Тайханшань, центр — Тайюань

- выдаёт provinces/provinces-q03: ответ 山西; зацепка Тайюань, та же строка
- видна в 11: provinces/provinces-q01, provinces/provinces-q02, provinces/provinces-q04, provinces/provinces-q05, provinces/provinces-q06, provinces/provinces-q07, provinces/provinces-q08, provinces/provinces-q09, provinces/provinces-q10, provinces/provinces-q110, provinces/provinces-q42

## 岷江 — Миньцзян — приток Янцзы в Сычуани, на нём стоит Дуцзянъянь

- выдаёт nature/nature-q63: ответ 岷江; зацепка Дуцзянъянь, та же строка
- видна в 1: nature/nature-q153

## 峨眉山 — Эмэйшань — буддийская гора в Сычуани, высшая точка — 3099 м

- выдаёт nature/nature-q11: ответ 峨眉山, Эмэйшань; зацепка Сычуань, та же строка
- видна в 3: nature/nature-q144, nature/nature-q46, nature/nature-q51

## 嵩山 — Суншань — Центральный пик пяти священных гор, в Хэнани

- выдаёт nature/nature-q50: ответ Хэнань; зацепка гора Суншань, пять священных гор, 嵩山, та же строка
- видна в 6: nature/nature-q10, nature/nature-q144, nature/nature-q46, nature/nature-q47, nature/nature-q49, nature/nature-q51

## 布币 — Бу-би — бронзовые монеты в форме лопатки, эпоха Чуньцю и Чжаньго

- выдаёт money/money-q26: ответ 布币, бу-би; зацепка бронза, та же строка
- видна в 4: money/money-q19, money/money-q21, money/money-q25, money/money-q27

## 布里亚特人 — Буряты — их героический эпос «Гэсэр»

- выдаёт ethnos/ethnos-q76: ответ 布里亚特人, Буряты; зацепка «Гэсэр», та же строка
- видна в 3: ethnos/ethnos-q68, ethnos/ethnos-q69, ethnos/ethnos-q75

## 师夷长技以制夷 — «Учиться у варваров передовой технике, чтобы одолеть варваров» — идея Вэй Юаня

- выдаёт modern-history/modern-history-q11: ответ 师夷长技以制夷, Учиться у варваров; зацепка Вэй Юань, та же строка
- видна в 4: modern-history/modern-history-q24, modern-history/modern-history-q26, modern-history/modern-history-q27, modern-history/modern-history-q93

## 帕斯捷尔纳克 — Пастернак — автор романа «Доктор Живаго» и сборника «Сестра моя — жизнь»

- выдаёт literature/literature-q77: ответ Доктор Живаго; зацепка Пастернак, та же строка
- видна в 18: literature/literature-q60, literature/literature-q61, literature/literature-q62, literature/literature-q63, literature/literature-q64, literature/literature-q66, literature/literature-q71, literature/literature-q73, literature/literature-q74, literature/literature-q80, literature/literature-q81, literature/literature-q82, literature/literature-q83, literature/literature-q86, literature/literature-q87, literature/literature-q93, literature/literature-q94, literature/literature-q95

## 广东 — Гуандун — провинция на юге материкового Китая, центр — Гуанчжоу

- выдаёт provinces/provinces-q99: ответ Гуанчжоу; зацепка провинция Гуандун, та же строка
- видна в 13: provinces/provinces-q01, provinces/provinces-q02, provinces/provinces-q03, provinces/provinces-q04, provinces/provinces-q05, provinces/provinces-q06, provinces/provinces-q07, provinces/provinces-q08, provinces/provinces-q10, provinces/provinces-q110, provinces/provinces-q122, provinces/provinces-q32, provinces/provinces-q42

## 广东 — Гуандун — родина кантонской кухни с белой нарезанной курицей

- выдаёт ethnos/ethnos-q86: ответ кантонский; зацепка провинция Гуандун, 广东
- видна в 2: cuisine/cuisine-q70, cuisine/cuisine-q71

## 广东 — Провинция Гуандун на юге Китая, центр — Гуанчжоу

- выдаёт provinces/provinces-q99: ответ Гуанчжоу; зацепка провинция Гуандун
- видна в 2: 2015-16-reg-1, 2018-19-shk-6

## 广东省 — Гуандун — южная провинция материкового Китая, центр — Гуанчжоу

- выдаёт provinces/provinces-q99: ответ Гуанчжоу; зацепка провинция Гуандун, та же строка
- видна в 6: provinces/provinces-q111, provinces/provinces-q112, provinces/provinces-q123, provinces/provinces-q13, provinces/provinces-q14, provinces/provinces-q16

## 广东省 — Провинция Гуандун, административный центр — Гуанчжоу

- выдаёт provinces/provinces-q99: ответ Гуанчжоу; зацепка провинция Гуандун
- видна в 1: 2017-18-reg-8

## 广州 — Гуанчжоу (Кантон), столица провинции Гуандун

- выдаёт provinces/provinces-q99: ответ 广州, Гуанчжоу; зацепка провинция Гуандун
- видна в 2: 2015-16-reg-1, modern-china/modern-china-q03

## 广州 — Гуанчжоу — город в Гуандуне; здесь прошли Азиатские игры 2010 года

- выдаёт provinces/provinces-q99: ответ 广州, Гуанчжоу; зацепка Гуандун
- видна в 1: modern-china/modern-china-q06

## 广州 — Гуанчжоу — крупный город на юге Китая, в провинции Гуандун

- выдаёт provinces/provinces-q99: ответ 广州, Гуанчжоу; зацепка провинция Гуандун
- видна в 17: provinces/provinces-q115, provinces/provinces-q116, provinces/provinces-q117, provinces/provinces-q119, provinces/provinces-q121, provinces/provinces-q21, provinces/provinces-q22, provinces/provinces-q24, provinces/provinces-q25, provinces/provinces-q26, provinces/provinces-q27, provinces/provinces-q28, provinces/provinces-q29, provinces/provinces-q30, provinces/provinces-q52, provinces/provinces-q53, provinces/provinces-q87

## 广州 — Гуанчжоу — центр провинции Гуандун

- выдаёт provinces/provinces-q99: ответ 广州, Гуанчжоу; зацепка провинция Гуандун, та же строка
- видна в 10: provinces/provinces-q100, provinces/provinces-q101, provinces/provinces-q33, provinces/provinces-q35, provinces/provinces-q36, provinces/provinces-q37, provinces/provinces-q38, provinces/provinces-q92, provinces/provinces-q96, provinces/provinces-q97

## 广西 — Гуанси — здесь карстовые горы Гуйлиня вдоль реки Лицзян

- выдаёт nature/nature-q158: ответ 广西, Гуанси; зацепка Гуйлинь, та же строка
- видна в 2: nature/nature-q157, nature/nature-q159

## 库利科沃大会战 — Куликовская битва — 1380 год, победа Дмитрия Донского над ордынским войском

- выдаёт dynasties/dynasties-q48: ответ Дмитрий Донской; зацепка Куликовская битва
- видна в 1: modern-history/modern-history-q50

## 庞贝城的末日 — «Последний день Помпеи» — картина Брюллова, 1833 год

- выдаёт painting/painting-q82: ответ Брюллов; зацепка Последний день Помпеи, 庞贝城的末日, та же строка
- видна в 3: painting/painting-q86, painting/painting-q88, painting/painting-q94

## 庞贝城的末日 — «Последний день Помпеи» — картина Карла Брюллова о гибели города под пеплом Везувия

- выдаёт painting/painting-q82: ответ Карл Брюллов, Брюллов; зацепка Последний день Помпеи, 庞贝城的末日
- видна в 1: painting/painting-q105

## 康有为 — Кан Ювэй — вдохновитель «Ста дней реформ» 1898 года

- выдаёт modern-history/modern-history-q60: ответ 康有为, Кан Ювэй; зацепка реформы 1898 года, та же строка
- видна в 4: modern-history/modern-history-q109, modern-history/modern-history-q110, modern-history/modern-history-q111, modern-history/modern-history-q113

## 康有为 — Кан Ювэй — идейный вождь реформ 1898 года, автор «Датун шу»

- выдаёт modern-history/modern-history-q60: ответ 康有为, Кан Ювэй; зацепка реформы 1898 года
- видна в 6: modern-history/modern-history-q04, modern-history/modern-history-q05, modern-history/modern-history-q06, modern-history/modern-history-q12, modern-history/modern-history-q17, modern-history/modern-history-q96

## 康熙 — Император Канси — правил 61 год, заключил с Россией Нерчинский договор

- выдаёт dynasties/dynasties-q32: ответ 康熙, император Канси; зацепка Нерчинский договор, та же строка
- видна в 8: dynasties/dynasties-q09, dynasties/dynasties-q10, dynasties/dynasties-q11, dynasties/dynasties-q12, dynasties/dynasties-q30, dynasties/dynasties-q31, dynasties/dynasties-q35, dynasties/dynasties-q39

## 开封 — Кайфэн — столица Северной Сун, в старину Бяньлян, Бяньцзин, Дунцзин

- выдаёт dynasties/dynasties-q104: ответ Бяньцзин; зацепка Северная Сун
- видна в 4: state/state-q06, state/state-q07, state/state-q09, state/state-q15

## 弗拉基米尔 — Владимир — центр Владимирской области, город «Золотого кольца»

- выдаёт provinces/provinces-q85: ответ 弗拉基米尔; зацепка Золотое кольцо, та же строка
- видна в 15: provinces/provinces-q108, provinces/provinces-q113, provinces/provinces-q114, provinces/provinces-q124, provinces/provinces-q63, provinces/provinces-q64, provinces/provinces-q65, provinces/provinces-q66, provinces/provinces-q67, provinces/provinces-q68, provinces/provinces-q69, provinces/provinces-q70, provinces/provinces-q71, provinces/provinces-q75, provinces/provinces-q77

## 张艺谋 — Чжан Имоу — режиссёр фильма «Красный гаолян» по прозе Мо Яня

- выдаёт cinema/cinema-q01: ответ 张艺谋, Чжан Имоу; зацепка Красный гаолян, та же строка
- видна в 2: cinema/cinema-q32, cinema/cinema-q33

## 当代英雄 — «Герой нашего времени» — роман Лермонтова о Печорине, 1840 г.

- выдаёт literature/literature-q84: ответ 当代英雄, Герой нашего времени; зацепка Лермонтов, та же строка
- видна в 4: literature/literature-q65, literature/literature-q72, literature/literature-q77, literature/literature-q85

## 彝族 — Народ И — живёт в Юньнани, Сычуани и Гуйчжоу; главный праздник — факелов (название ответа)

- выдаёт crafts/crafts-q132: ответ Гуйчжоу; зацепка И
- видна в 2: holidays/holidays-q17, holidays/holidays-q40

## 彼得大帝 — Пётр Великий — царь, одержал победу над шведами под Полтавой в 1709 году

- выдаёт modern-history/modern-history-q101: ответ 彼得大帝, Пётр Великий; зацепка 1709 год, та же строка
- видна в 1: modern-history/modern-history-q98

## 征服喀山汗国 — Взятие Казани в 1552 году войском Ивана IV

- выдаёт dynasties/dynasties-q55: ответ Иван IV; зацепка Казань, та же строка
- видна в 5: dynasties/dynasties-q117, dynasties/dynasties-q118, dynasties/dynasties-q119, dynasties/dynasties-q121, dynasties/dynasties-q122

## 徐悲鸿 — Сюй Бэйхун — художник XX века, прославился изображениями лошадей

- выдаёт painting/painting-q01: ответ 徐悲鸿, Сюй Бэйхун; зацепка XX век, лошадей, лошади, лошадь, та же строка
- видна в 3: painting/painting-q04, painting/painting-q05, painting/painting-q06

## 德米特里·顿斯科伊 — Дмитрий Донской — великий князь, победил Орду на Куликовом поле в 1380 году

- выдаёт dynasties/dynasties-q48: ответ 德米特里·顿斯科伊, Дмитрий Донской; зацепка великий князь
- видна в 2: modern-history/modern-history-q101, modern-history/modern-history-q98

## 恒山 — Хэншань в Шаньси — Северный пик пяти священных гор

- выдаёт nature/nature-q49: ответ 恒山, Хэншань в Шаньси; зацепка Северный пик, пять священных гор, та же строка
- видна в 6: nature/nature-q10, nature/nature-q144, nature/nature-q156, nature/nature-q46, nature/nature-q47, nature/nature-q51

## 恶魔 — «Демон» — романтическая поэма Лермонтова

- выдаёт literature/literature-q63: ответ Лермонтов; зацепка Демон, та же строка
- видна в 1: literature/literature-q67

## 恶魔 — «Демон» — романтическая поэма Лермонтова о падшем духе

- выдаёт literature/literature-q63: ответ Лермонтов; зацепка Демон
- видна в 4: literature/literature-q65, literature/literature-q72, literature/literature-q77, literature/literature-q85

## 戈尔巴乔夫 — Михаил Горбачёв — первый и последний президент СССР

- выдаёт modern-history/modern-history-q104: ответ президент СССР; зацепка Михаил Горбачёв, та же строка
- видна в 2: modern-history/modern-history-q105, modern-history/modern-history-q106

## 成都 — Чэнду — административный центр провинции Сычуань

- выдаёт provinces/provinces-q25: ответ 成都; зацепка провинция Сычуань
- видна в 11: provinces/provinces-q100, provinces/provinces-q101, provinces/provinces-q33, provinces/provinces-q35, provinces/provinces-q36, provinces/provinces-q37, provinces/provinces-q38, provinces/provinces-q92, provinces/provinces-q96, provinces/provinces-q97, provinces/provinces-q99

## 成都 — Чэнду — город на юго-западе Китая, в провинции Сычуань

- выдаёт provinces/provinces-q25: ответ 成都; зацепка провинция Сычуань, та же строка
- видна в 16: provinces/provinces-q115, provinces/provinces-q117, provinces/provinces-q119, provinces/provinces-q121, provinces/provinces-q20, provinces/provinces-q21, provinces/provinces-q22, provinces/provinces-q24, provinces/provinces-q26, provinces/provinces-q27, provinces/provinces-q28, provinces/provinces-q29, provinces/provinces-q30, provinces/provinces-q52, provinces/provinces-q53, provinces/provinces-q87

## 战争与和平 — «Война и мир» — киноэпопея Сергея Бондарчука по роману Льва Толстого

- выдаёт literature/literature-q87: ответ Толстой; зацепка Война и мир
- видна в 2: cinema/cinema-q24, cinema/cinema-q30

## 战争与和平 — «Война и мир» — роман-эпопея Льва Толстого о 1805–1812 гг.

- выдаёт literature/literature-q87: ответ Толстой; зацепка Война и мир
- видна в 1: literature/literature-q67

## 打通黑海出海口 — Выход к Чёрному морю — итог войн с Турцией при Екатерине II

- выдаёт dynasties/dynasties-q121: ответ 打通黑海出海口; зацепка Екатерина II, та же строка
- видна в 4: dynasties/dynasties-q117, dynasties/dynasties-q118, dynasties/dynasties-q119, dynasties/dynasties-q122

## 托尔斯泰 — Лев Толстой — автор романа-эпопеи «Война и мир»

- выдаёт literature/literature-q87: ответ 托尔斯泰, Лев Толстой, Толстой; зацепка Война и мир, та же строка
- видна в 12: literature/literature-q60, literature/literature-q61, literature/literature-q62, literature/literature-q63, literature/literature-q71, literature/literature-q73, literature/literature-q80, literature/literature-q81, literature/literature-q82, literature/literature-q86, literature/literature-q93, literature/literature-q94

## 扫墓 — Уборка могил предков — главный обычай праздника Цинмин

- выдаёт holidays/holidays-q46: ответ праздник Цинмин; зацепка 扫墓, та же строка
- видна в 2: holidays/holidays-q06, holidays/holidays-q15

## 拉萨 — Лхаса — административный центр Тибетского автономного района

- выдаёт 2021-22-mun-qd67aaa: ответ 拉萨; зацепка Тибетский автономный район, та же строка
- видна в 11: provinces/provinces-q100, provinces/provinces-q101, provinces/provinces-q33, provinces/provinces-q35, provinces/provinces-q36, provinces/provinces-q37, provinces/provinces-q38, provinces/provinces-q92, provinces/provinces-q96, provinces/provinces-q97, provinces/provinces-q99

## 拉萨 — Лхаса — город в Тибетском автономном районе на юго-западе Китая

- выдаёт 2021-22-mun-qd67aaa: ответ 拉萨; зацепка Тибетский автономный район
- видна в 17: provinces/provinces-q115, provinces/provinces-q116, provinces/provinces-q117, provinces/provinces-q119, provinces/provinces-q121, provinces/provinces-q20, provinces/provinces-q21, provinces/provinces-q24, provinces/provinces-q25, provinces/provinces-q26, provinces/provinces-q27, provinces/provinces-q28, provinces/provinces-q29, provinces/provinces-q30, provinces/provinces-q52, provinces/provinces-q53, provinces/provinces-q87

## 拉萨 — Лхаса — здесь дворец Потала из Белого и Красного дворцов

- выдаёт landmarks/landmarks-q94: ответ 拉萨; зацепка дворец Потала, та же строка
- видна в 1: landmarks/landmarks-q10

## 拙政园 — Сад скромного чиновника — классический сад Сучжоу, в Списке всемирного наследия

- выдаёт landmarks/landmarks-q23: ответ 拙政园, Сад скромного чиновника; зацепка Сучжоу
- видна в 1: provinces/provinces-q56

## 捷列什科娃 — Валентина Терешкова — первая женщина в космосе, полёт 1963 года

- выдаёт space/space-q15: ответ 捷列什科娃, Валентина Терешкова, Терешкова; зацепка 1963 год, та же строка
- видна в 3: space/space-q16, space/space-q17, space/space-q19

## 摆脱金帐汗国统治 — Конец ордынского ига: стояние на Угре 1480 года при Иване III

- выдаёт dynasties/dynasties-q122: ответ 摆脱金帐汗国统治; зацепка Иван III, та же строка
- видна в 4: dynasties/dynasties-q117, dynasties/dynasties-q118, dynasties/dynasties-q119, dynasties/dynasties-q121

## 改唐为周 — Замена Тан на Чжоу — в 690 году У Цзэтянь стала императором

- выдаёт dynasties/dynasties-q37: ответ У Цзэтянь; зацепка Тан, та же строка
- видна в 3: dynasties/dynasties-q90, dynasties/dynasties-q91, dynasties/dynasties-q92

## 改国号为元 — Название Юань — принято Хубилаем для своего государства в 1271 году

- выдаёт dynasties/dynasties-q29: ответ Хубилай; зацепка Название Юань
- видна в 3: dynasties/dynasties-q90, dynasties/dynasties-q91, dynasties/dynasties-q92

## 教师节 — День учителя — 10 сентября, учреждён в 1985 году

- выдаёт holidays/holidays-q02: ответ 教师节, День учителя; зацепка 10, та же строка
- видна в 1: holidays/holidays-q32

## 敦煌 — Дуньхуан — возле него пещеры Могао со статуями и росписями

- выдаёт landmarks/landmarks-q97: ответ 敦煌; зацепка Пещеры Могао, та же строка
- видна в 3: landmarks/landmarks-q48, landmarks/landmarks-q96, landmarks/landmarks-q98

## 斯大林 — Иосиф Сталин — генеральный секретарь ЦК партии с 1922 года

- выдаёт modern-history/modern-history-q103: ответ генеральный секретарь ЦК; зацепка Иосиф Сталин, та же строка
- видна в 2: modern-history/modern-history-q105, modern-history/modern-history-q106

## 新疆 — Синьцзян — автономный район на северо-западе Китая, центр — Урумчи (название ответа)

- выдаёт provinces/provinces-q96: ответ Урумчи; зацепка Синьцзян, та же строка
- видна в 3: nature/nature-q150, provinces/provinces-q11, provinces/provinces-q44

## 新疆 — Синьцзян — здесь кяризы, подземная оросительная система Турфана

- выдаёт nature/nature-q155: ответ 新疆, Синьцзян; зацепка кяризы, та же строка
- видна в 2: nature/nature-q154, nature/nature-q67

## 新疆维吾尔自治区 — Синьцзян-Уйгурский автономный район — на северо-западе, центр — Урумчи

- выдаёт provinces/provinces-q96: ответ Урумчи; зацепка Синьцзян, та же строка
- видна в 4: provinces/provinces-q112, provinces/provinces-q123, provinces/provinces-q16, provinces/provinces-q34

## 施耐庵 — Ши Найань — по традиции автор романа «Речные заводи»

- выдаёт literature/literature-q09: ответ 施耐庵, Ши Найань; зацепка Речные заводи, Речных заводей, та же строка
- видна в 5: literature/literature-q01, literature/literature-q03, literature/literature-q101, literature/literature-q96, literature/literature-q97

## 无线电 — Изобретение радио — Александр Попов (1895)

- выдаёт people/people-q27: ответ 无线电; зацепка Александр Попов, та же строка
- видна в 3: people/people-q25, people/people-q26, people/people-q28

## 日本海 — Японское море — омывает Приморье и Сахалин, на его берегу стоит Владивосток

- выдаёт nature/nature-q130: ответ 日本海, Японское море; зацепка Владивосток, та же строка
- видна в 2: nature/nature-q08, nature/nature-q112

## 日本海 — Японское море — сюда впадает Туманная (Тумэньцзян)

- выдаёт nature/nature-q106: ответ Тумэньцзян; зацепка Японское море, та же строка
- видна в 2: nature/nature-q06, nature/nature-q141

## 日瓦戈医生 — «Доктор Живаго» — роман Пастернака о враче и поэте, впервые издан в Италии

- выдаёт literature/literature-q77: ответ 日瓦戈医生, Доктор Живаго; зацепка Пастернак, та же строка
- видна в 4: literature/literature-q65, literature/literature-q72, literature/literature-q84, literature/literature-q85

## 日瓦戈医生 — «Доктор Живаго» — роман Пастернака, впервые изданный в Италии

- выдаёт literature/literature-q77: ответ 日瓦戈医生, Доктор Живаго; зацепка Пастернак
- видна в 1: literature/literature-q67

## 明 — Мин (1368–1644) — при ней построен Храм Неба

- выдаёт landmarks/landmarks-q92: ответ 明; зацепка Храм Неба, та же строка
- видна в 1: landmarks/landmarks-q46

## 春城 — «Город весны» — прозвище Куньмина с климатом вечной весны

- выдаёт provinces/provinces-q50: ответ 春城, город весны; зацепка Куньмин, та же строка
- видна в 1: provinces/provinces-q58

## 春望 — «Весенний пейзаж» — одно из главных стихотворений Ду Фу

- выдаёт literature/literature-q89: ответ 春望, Весенний пейзаж; зацепка Ду Фу, та же строка
- видна в 4: literature/literature-q88, literature/literature-q90, literature/literature-q91, literature/literature-q92

## 春节 — Праздник весны — Новый год по лунному календарю, лепят цзяоцзы

- выдаёт holidays/holidays-q53: ответ 春节, Праздник весны; зацепка Новый год
- видна в 3: holidays/holidays-q16, holidays/holidays-q46, holidays/holidays-q47

## 普希金 — Пушкин — автор романа в стихах «Евгений Онегин»

- выдаёт literature/literature-q93: ответ 普希金, Пушкин; зацепка Евгений Онегин, та же строка
- видна в 13: literature/literature-q60, literature/literature-q61, literature/literature-q62, literature/literature-q63, literature/literature-q71, literature/literature-q73, literature/literature-q80, literature/literature-q81, literature/literature-q82, literature/literature-q86, literature/literature-q87, literature/literature-q94, literature/literature-q95

## 曲阜 — Цюйфу — здесь усадьба рода Кун, потомков Конфуция

- выдаёт 2022-23-mun-7: ответ 曲阜; зацепка Конфуций
- видна в 2: landmarks/landmarks-q10, landmarks/landmarks-q94

## 曲阜 — Цюйфу — здесь храм Конфуция, основанный в 478 году до н. э.

- выдаёт 2022-23-mun-7: ответ 曲阜; зацепка Конфуций
- видна в 4: landmarks/landmarks-q48, landmarks/landmarks-q96, landmarks/landmarks-q97, landmarks/landmarks-q98

## 曾联松 — Цзэн Ляньсун — шанхайский служащий, автор эскиза флага КНР

- выдаёт state/state-q11: ответ 曾联松, Цзэн Ляньсун; зацепка Автор эскиза, Флаг КНР, та же строка
- видна в 2: state/state-q10, state/state-q12

## 本草纲目 — «Бэньцао ганму» — свод Ли Шичжэня о лекарственных средствах, 1892 вида

- выдаёт 2025-26-reg-2: ответ 本草纲目, «Бэньцао ганму», Бэньцао ганму; зацепка Ли Шичжэнь, та же строка
- видна в 7: people/people-q11, people/people-q12, people/people-q13, people/people-q14, people/people-q15, people/people-q16, people/people-q17

## 本草纲目 — «Бэньцао ганму», лечебник Ли Шичжэня, 1578

- выдаёт 2025-26-reg-2: ответ 本草纲目, «Бэньцао ганму», Бэньцао ганму; зацепка Ли Шичжэнь
- видна в 1: 2017-18-shk-4

## 杂交水稻 — Гибридный рис — сорта Юань Лунпина, с 1976 г. их сеют по всему Китаю

- выдаёт people/people-q16: ответ 杂交水稻, гибридный рис; зацепка Юань Лунпин, та же строка
- видна в 6: people/people-q11, people/people-q12, people/people-q13, people/people-q14, people/people-q15, people/people-q17

## 李时珍 — Ли Шичжэнь — врач и фармаколог династии Мин, автор «Бэньцао ганму»

- выдаёт 2025-26-reg-2: ответ «Бэньцао ганму», Бэньцао ганму; зацепка Ли Шичжэнь, та же строка
- видна в 1: people/people-q05

## 李昪 — Ли Бянь — основатель Южной Тан (937), столица Цзиньлин (Нанкин)

- выдаёт state/state-q14: ответ Цзиньлин; зацепка Нанкин
- видна в 3: dynasties/dynasties-q09, dynasties/dynasties-q10, dynasties/dynasties-q39

## 条件反射 — Учение об условных рефлексах — Иван Павлов

- выдаёт people/people-q28: ответ 条件反射, Условный рефлекс; зацепка Иван Павлов, та же строка
- видна в 3: people/people-q25, people/people-q26, people/people-q27

## 杭州 — Ханчжоу — город на востоке Китая, в провинции Чжэцзян

- выдаёт provinces/provinces-q101: ответ 杭州, Ханчжоу; зацепка провинция Чжэцзян
- видна в 17: provinces/provinces-q115, provinces/provinces-q116, provinces/provinces-q117, provinces/provinces-q119, provinces/provinces-q121, provinces/provinces-q20, provinces/provinces-q21, provinces/provinces-q22, provinces/provinces-q24, provinces/provinces-q25, provinces/provinces-q26, provinces/provinces-q27, provinces/provinces-q28, provinces/provinces-q29, provinces/provinces-q30, provinces/provinces-q52, provinces/provinces-q53

## 杭州 — Ханчжоу — здесь монастырь Линъиньсы у озера Сиху

- выдаёт provinces/provinces-q87: ответ 杭州, Ханчжоу; зацепка озеро Сиху
- видна в 4: landmarks/landmarks-q48, landmarks/landmarks-q96, landmarks/landmarks-q97, landmarks/landmarks-q98

## 杭州 — Ханчжоу — столица Южной Сун под названием Линьань

- выдаёт dynasties/dynasties-q08: ответ Линьань; зацепка Ханчжоу, Южная Сун
- видна в 4: state/state-q06, state/state-q07, state/state-q09, state/state-q15

## 杭州 — Ханчжоу — центр провинции Чжэцзян

- выдаёт provinces/provinces-q101: ответ 杭州, Ханчжоу; зацепка провинция Чжэцзян, та же строка
- видна в 10: provinces/provinces-q100, provinces/provinces-q33, provinces/provinces-q35, provinces/provinces-q36, provinces/provinces-q37, provinces/provinces-q38, provinces/provinces-q92, provinces/provinces-q96, provinces/provinces-q97, provinces/provinces-q99

## 松林里的早晨 — «Утро в сосновом лесу» — картина Ивана Шишкина 1889 года с медвежатами

- выдаёт painting/painting-q107: ответ Иван Шишкин, Шишкин; зацепка Утро в сосновом лесу, сосна, 松林里的早晨
- видна в 1: painting/painting-q105

## 松林里的早晨 — «Утро в сосновом лесу» — пейзаж Шишкина и Савицкого, 1889 год

- выдаёт painting/painting-q107: ответ Шишкин; зацепка Утро в сосновом лесу, сосна, 松林里的早晨, та же строка
- видна в 3: painting/painting-q86, painting/painting-q88, painting/painting-q94

## 松鼠鳜鱼 — Мандариновый окунь в форме белки — традиционное блюдо Сучжоу, цзянсуская кухня

- выдаёт cuisine/cuisine-q77: ответ Цзянсуская кухня; зацепка 松鼠鳜鱼
- видна в 1: cuisine/cuisine-q84

## 果戈理 — Гоголь — автор поэмы «Мёртвые души» и комедии «Ревизор»

- выдаёт literature/literature-q67: ответ Мёртвые души; зацепка Гоголь, та же строка
- видна в 14: literature/literature-q60, literature/literature-q61, literature/literature-q62, literature/literature-q63, literature/literature-q71, literature/literature-q73, literature/literature-q80, literature/literature-q81, literature/literature-q82, literature/literature-q86, literature/literature-q87, literature/literature-q93, literature/literature-q94, literature/literature-q95

## 桂 — Сокращение Гуанси — Гуй; край славится коричными деревьями и зовётся «Багуй»

- выдаёт provinces/provinces-q44: ответ Гуанси; зацепка 桂, та же строка
- видна в 9: provinces/provinces-q102, provinces/provinces-q19, provinces/provinces-q31, provinces/provinces-q41, provinces/provinces-q43, provinces/provinces-q45, provinces/provinces-q93, provinces/provinces-q94, provinces/provinces-q95

## 桂林 — Гуйлинь, город в Гуанси-Чжуанском автономном районе, известный карстовыми пейзажами

- выдаёт nature/nature-q158: ответ Гуанси; зацепка Гуйлинь, 桂林
- видна в 1: 2015-16-reg-1

## 桃花源记 — «Записки о Персиковом источнике» Тао Юаньмина — образ идеального края

- выдаёт literature/literature-q22: ответ Тао Юаньмин; зацепка Персиковый источник, 桃花源记, та же строка
- видна в 5: literature/literature-q88, literature/literature-q89, literature/literature-q90, literature/literature-q91, literature/literature-q92

## 梁启超 — Лян Цичао — мыслитель, один из вождей реформ 1898 года, автор «О юном Китае»

- выдаёт modern-history/modern-history-q17: ответ 梁启超, Лян Цичао; зацепка О юном Китае, та же строка
- видна в 5: modern-history/modern-history-q04, modern-history/modern-history-q05, modern-history/modern-history-q06, modern-history/modern-history-q12, modern-history/modern-history-q96

## 梁思成 — Лян Сычэн — архитектор, возглавил группу Цинхуа по проекту герба КНР

- выдаёт state/state-q12: ответ 梁思成, Лян Сычэн; зацепка Герб КНР, та же строка
- видна в 2: state/state-q10, state/state-q11

## 梅兰芳 — Мэй Ланьфан — артист пекинской оперы, исполнитель женских ролей дань (название ответа)

- выдаёт 2016-17-mun-yar-8: ответ Пекин; зацепка Пекинская опера
- видна в 1: 2016-17-reg-3

## 梅兰芳 — Мэй Ланьфан — звезда пекинской оперы, в 1935 году гастролировал в СССР (название ответа)

- выдаёт 2016-17-mun-yar-8: ответ Пекин; зацепка Пекинская опера
- видна в 1: 2020-21-pri-q26db53

## 楚汉战争 — Война Чу и Хань — кончилась победой Лю Бана над Сян Юем в 202 г. до н. э.

- выдаёт dynasties/dynasties-q92: ответ 楚汉战争, война Чу и Хань; зацепка Лю Бан, та же строка
- видна в 2: dynasties/dynasties-q90, dynasties/dynasties-q91

## 楚辞 — «Чуские строфы» — сборник поэзии царства Чу, главный автор — Цюй Юань

- выдаёт literature/literature-q21: ответ 楚辞, Чуские строфы; зацепка Цюй Юань, та же строка
- видна в 4: literature/literature-q10, literature/literature-q12, literature/literature-q57, literature/literature-q59

## 正月初一 — 1-е число 1-го лунного месяца — Праздник весны, Новый год

- выдаёт holidays/holidays-q53: ответ Праздник весны; зацепка Новый год, та же строка
- видна в 5: holidays/holidays-q03, holidays/holidays-q14, holidays/holidays-q35, holidays/holidays-q36, holidays/holidays-q37

## 正月十五 — 15-е число 1-го лунного месяца — Праздник фонарей

- выдаёт holidays/holidays-q35: ответ 正月十五; зацепка Праздник фонарей, та же строка
- видна в 4: holidays/holidays-q03, holidays/holidays-q14, holidays/holidays-q36, holidays/holidays-q37

## 武昌 — Учан — город, где 10 октября 1911 года началось Учанское восстание

- выдаёт modern-history/modern-history-q63: ответ 武昌, Учанское восстание; зацепка 10, та же строка
- видна в 2: modern-history/modern-history-q114, modern-history/modern-history-q69

## 武昌 — Учан, ныне район города Ухань в провинции Хубэй

- выдаёт provinces/provinces-q100: ответ город Ухань; зацепка провинция Хубэй
- видна в 1: addition-b1-08

## 武汉 — Ухань — город в центре Китая, в провинции Хубэй

- выдаёт provinces/provinces-q100: ответ 武汉; зацепка провинция Хубэй
- видна в 18: provinces/provinces-q115, provinces/provinces-q116, provinces/provinces-q117, provinces/provinces-q119, provinces/provinces-q121, provinces/provinces-q20, provinces/provinces-q21, provinces/provinces-q22, provinces/provinces-q24, provinces/provinces-q25, provinces/provinces-q26, provinces/provinces-q27, provinces/provinces-q28, provinces/provinces-q29, provinces/provinces-q30, provinces/provinces-q52, provinces/provinces-q53, provinces/provinces-q87

## 武汉 — Ухань — здесь башня Жёлтого журавля на горе Шэшань над Янцзы

- выдаёт provinces/provinces-q56: ответ башня Жёлтого журавля; зацепка Ухань
- видна в 3: landmarks/landmarks-q100, landmarks/landmarks-q101, landmarks/landmarks-q99

## 武汉 — Ухань — центр провинции Хубэй

- выдаёт provinces/provinces-q100: ответ 武汉; зацепка провинция Хубэй, та же строка
- видна в 10: provinces/provinces-q101, provinces/provinces-q33, provinces/provinces-q35, provinces/provinces-q36, provinces/provinces-q37, provinces/provinces-q38, provinces/provinces-q92, provinces/provinces-q96, provinces/provinces-q97, provinces/provinces-q99

## 死魂灵 — «Мёртвые души» — роман-поэма Гоголя о Чичикове, 1842 г.

- выдаёт literature/literature-q67: ответ 死魂灵, Мёртвые души; зацепка Гоголь
- видна в 5: literature/literature-q65, literature/literature-q72, literature/literature-q77, literature/literature-q84, literature/literature-q85

## 毕昇 — Би Шэн — изобретатель эпохи Северной Сун, создатель печати подвижными литерами

- выдаёт dynasties/dynasties-q22: ответ Северная Сун; зацепка Би Шэн
- видна в 1: people/people-q05

## 毛泽东 — Мао Цзэдун — председатель ЦК КПК, руководил партией до своей смерти в 1976 году (название ответа)

- выдаёт 2024-25-mun-spb-8: ответ 1976 год, 1976; зацепка Мао Цзэдун
- видна в 11: modern-history/modern-history-q01, modern-history/modern-history-q02, modern-history/modern-history-q03, modern-history/modern-history-q04, modern-history/modern-history-q05, modern-history/modern-history-q06, modern-history/modern-history-q07, modern-history/modern-history-q17, modern-history/modern-history-q25, modern-history/modern-history-q28, modern-history/modern-history-q96

## 民主与科学 — «Демократия и наука» — лозунг Движения за новую культуру

- выдаёт modern-history/modern-history-q64: ответ 民主与科学, Демократия и наука; зацепка Движение за новую культуру, та же строка
- видна в 1: modern-history/modern-history-q61

## 水墨动画 — Анимация водяной тушью — так снят мультфильм «Головастики ищут маму» (1960)

- выдаёт cinema/cinema-q13: ответ 水墨动画, анимация водяной тушью; зацепка Головастики ищут маму, та же строка
- видна в 1: cinema/cinema-q14

## 水浒传 — «Речные заводи» — роман о героях Ляншаня, по традиции его автор Ши Найань

- выдаёт literature/literature-q09: ответ Ши Найань; зацепка Речные заводи, Речных заводей, та же строка
- видна в 5: literature/literature-q88, literature/literature-q89, literature/literature-q90, literature/literature-q91, literature/literature-q92

## 水浒传 — «Речные заводи», классический роман XIV века

- выдаёт literature/literature-q13: ответ 水浒传, Речные заводи; зацепка XIV век
- видна в 1: 2017-18-shk-4

## 汉 — Династия Хань — 202 г. до н. э. — 220 г. н. э., основал Лю Бан

- выдаёт dynasties/dynasties-q115: ответ 汉, династия Хань; зацепка Лю Бан, та же строка
- видна в 5: dynasties/dynasties-q01, dynasties/dynasties-q07, dynasties/dynasties-q107, dynasties/dynasties-q108, dynasties/dynasties-q22

## 汉代 — Династия Хань — 202 г. до н. э. — 220 г. н. э., основал Лю Бан

- выдаёт dynasties/dynasties-q115: ответ 汉, династия Хань; зацепка Лю Бан, та же строка
- видна в 3: dynasties/dynasties-q02, dynasties/dynasties-q05, dynasties/dynasties-q15

## 汉朝 — Династия Хань — 202 г. до н. э. — 220 г. н. э., основал Лю Бан

- выдаёт dynasties/dynasties-q115: ответ 汉, династия Хань; зацепка Лю Бан, та же строка
- видна в 8: dynasties/dynasties-q03, dynasties/dynasties-q04, dynasties/dynasties-q06, dynasties/dynasties-q109, dynasties/dynasties-q110, dynasties/dynasties-q111, dynasties/dynasties-q112, dynasties/dynasties-q114

## 汉语水平考试 — HSK — экзамен по китайскому языку для тех, кому он не родной

- выдаёт 2016-17-shk-9: ответ HSK; зацепка Китайский язык, 汉语水平考试
- видна в 1: 2022-23-reg-2

## 江苏 — Цзянсу — здесь двухъярусный Нанкинский мост через Янцзы

- выдаёт provinces/provinces-q24: ответ Нанкин; зацепка Цзянси, Цзянсу
- видна в 3: nature/nature-q154, nature/nature-q155, nature/nature-q67

## 江苏 — Цзянсу — приморская провинция в низовьях Янцзы, центр — Нанкин

- выдаёт provinces/provinces-q24: ответ Нанкин; зацепка Цзянси, Цзянсу
- видна в 14: provinces/provinces-q01, provinces/provinces-q02, provinces/provinces-q03, provinces/provinces-q04, provinces/provinces-q05, provinces/provinces-q06, provinces/provinces-q07, provinces/provinces-q08, provinces/provinces-q09, provinces/provinces-q10, provinces/provinces-q110, provinces/provinces-q122, provinces/provinces-q32, provinces/provinces-q42

## 江苏 — Цзянсу — провинция, где лежит основная часть озера Тайху

- выдаёт nature/nature-q31: ответ 江苏; зацепка озеро Тайху, та же строка
- видна в 1: nature/nature-q142

## 江苏 — Цзянсу — родина зелёного чая Билочунь с озера Тайху

- выдаёт nature/nature-q31: ответ 江苏; зацепка озеро Тайху
- видна в 6: cuisine/cuisine-q90, cuisine/cuisine-q91, cuisine/cuisine-q93, cuisine/cuisine-q94, cuisine/cuisine-q95, cuisine/cuisine-q96

## 江苏省 — Цзянсу — провинция в низовьях Янцзы с центром в Нанкине

- выдаёт provinces/provinces-q24: ответ Нанкин; зацепка Цзянси, Цзянсу
- видна в 8: provinces/provinces-q111, provinces/provinces-q112, provinces/provinces-q12, provinces/provinces-q123, provinces/provinces-q13, provinces/provinces-q14, provinces/provinces-q15, provinces/provinces-q16

## 汴京 — Бяньцзин (ныне Кайфэн) — столица Северной Сун

- выдаёт dynasties/dynasties-q104: ответ 汴京, Бяньцзин; зацепка Северная Сун, та же строка
- видна в 5: dynasties/dynasties-q08, dynasties/dynasties-q103, dynasties/dynasties-q105, dynasties/dynasties-q106, dynasties/dynasties-q20

## 沈阳 — Шэньян (Мукден) — город, у которого 18 сентября 1931 года японцы взорвали железную дорогу

- выдаёт modern-history/modern-history-q69: ответ 沈阳, Шэньян, Мукден; зацепка 1931 год, та же строка
- видна в 2: modern-history/modern-history-q114, modern-history/modern-history-q63

## 沈阳 — Шэньян — центр провинции Ляонин

- выдаёт provinces/provinces-q35: ответ 沈阳, Шэньян; зацепка провинция Ляонин, та же строка
- видна в 10: provinces/provinces-q100, provinces/provinces-q101, provinces/provinces-q33, provinces/provinces-q36, provinces/provinces-q37, provinces/provinces-q38, provinces/provinces-q92, provinces/provinces-q96, provinces/provinces-q97, provinces/provinces-q99

## 沪 — Сокращение Шанхая — от старого названия низовьев реки Сунцзян, «Худу»

- выдаёт provinces/provinces-q19: ответ 沪; зацепка Шанхай, та же строка
- видна в 8: provinces/provinces-q102, provinces/provinces-q31, provinces/provinces-q41, provinces/provinces-q43, provinces/provinces-q45, provinces/provinces-q93, provinces/provinces-q94, provinces/provinces-q95

## 河北 — Хэбэй — здесь каменный арочный мост Чжаочжоу эпохи Суй

- выдаёт nature/nature-q67: ответ 河北; зацепка мост Чжаочжоу, та же строка
- видна в 2: nature/nature-q154, nature/nature-q155

## 河北 — Хэбэй — провинция вокруг Пекина и Тяньцзиня, центр — Шицзячжуан

- выдаёт provinces/provinces-q33: ответ Шицзячжуан; зацепка провинция Хэбэй, та же строка
- видна в 14: provinces/provinces-q01, provinces/provinces-q02, provinces/provinces-q03, provinces/provinces-q04, provinces/provinces-q05, provinces/provinces-q06, provinces/provinces-q07, provinces/provinces-q08, provinces/provinces-q09, provinces/provinces-q10, provinces/provinces-q110, provinces/provinces-q122, provinces/provinces-q32, provinces/provinces-q42

## 河北省 — Хэбэй — провинция вокруг Пекина и Тяньцзиня, центр — Шицзячжуан

- выдаёт provinces/provinces-q33: ответ Шицзячжуан; зацепка провинция Хэбэй, та же строка
- видна в 8: provinces/provinces-q111, provinces/provinces-q112, provinces/provinces-q12, provinces/provinces-q123, provinces/provinces-q13, provinces/provinces-q14, provinces/provinces-q15, provinces/provinces-q16

## 河南 — Хэнань — здесь Суншань, Центральный пик пяти священных гор

- выдаёт nature/nature-q50: ответ 河南, Хэнань; зацепка пять священных гор, та же строка
- видна в 7: nature/nature-q03, nature/nature-q145, nature/nature-q146, nature/nature-q147, nature/nature-q148, nature/nature-q149, nature/nature-q23

## 河南 — Хэнань — провинция в центре Китая, в бассейне Хуанхэ, центр — Чжэнчжоу

- выдаёт provinces/provinces-q89: ответ Хуанхэ; зацепка провинция Хэнань, та же строка
- видна в 11: provinces/provinces-q01, provinces/provinces-q02, provinces/provinces-q04, provinces/provinces-q05, provinces/provinces-q06, provinces/provinces-q07, provinces/provinces-q08, provinces/provinces-q09, provinces/provinces-q10, provinces/provinces-q110, provinces/provinces-q32

## 河南省 — Хэнань — провинция в центре Китая, на Хуанхэ, центр — Чжэнчжоу

- выдаёт provinces/provinces-q89: ответ Хуанхэ; зацепка провинция Хэнань, та же строка
- видна в 8: provinces/provinces-q111, provinces/provinces-q112, provinces/provinces-q12, provinces/provinces-q123, provinces/provinces-q13, provinces/provinces-q14, provinces/provinces-q15, provinces/provinces-q16

## 泉城 — «Город родников» — прозвище Цзинаня из-за множества источников

- выдаёт provinces/provinces-q21: ответ Цзинань; зацепка 泉城, та же строка
- видна в 2: provinces/provinces-q50, provinces/provinces-q58

## 泰山 — Тайшань — Восточный пик пяти священных гор, в Шаньдуне

- выдаёт nature/nature-q47: ответ 泰山, Тайшань; зацепка пять священных гор, та же строка
- видна в 5: nature/nature-q10, nature/nature-q144, nature/nature-q46, nature/nature-q49, nature/nature-q51

## 泼水节 — Праздник воды — Новый год дайцев: обливают друг друга водой на счастье

- выдаёт holidays/holidays-q18: ответ 泼水节, Праздник воды; зацепка Новый год, та же строка
- видна в 2: holidays/holidays-q02, holidays/holidays-q32

## 洛神赋图 — «Нимфа реки Ло» — свиток, оригинал которого приписывают Гу Кайчжи

- выдаёт painting/painting-q25: ответ Гу Кайчжи; зацепка Нимфа реки Ло, 洛神赋图, та же строка
- видна в 1: painting/painting-q103

## 洛阳 — Лоян — на его южной окраине пещерные храмы Лунмэнь

- выдаёт landmarks/landmarks-q98: ответ 洛阳; зацепка Лунмэнь, та же строка
- видна в 3: landmarks/landmarks-q48, landmarks/landmarks-q96, landmarks/landmarks-q97

## 洛阳 — Лоян — столица 13 династий, в т. ч. Вэй, Западной Цзинь, Северной Вэй

- выдаёт 2024-25-zak-qfce692: ответ 洛阳, Лоян; зацепка Северная Вэй
- видна в 3: state/state-q07, state/state-q08, state/state-q09

## 洞庭湖 — Дунтинху в Хунани: по нему названы провинции Хубэй и Хунань

- выдаёт provinces/provinces-q90: ответ 洞庭湖, Дунтинху; зацепка Хунань, провинция Хубэй
- видна в 1: 2017-18-zak-10

## 洨河 — Сяохэ — река в уезде Чжаосянь провинции Хэбэй, над ней стоит мост Чжаочжоу

- выдаёт nature/nature-q67: ответ провинция Хэбэй; зацепка мост Чжаочжоу, та же строка
- видна в 2: nature/nature-q153, nature/nature-q63

## 洪秀全 — Хун Сюцюань — вождь Тайпинского восстания, основатель Небесного государства

- выдаёт modern-history/modern-history-q110: ответ 洪秀全, Хун Сюцюань; зацепка Тайпинское восстание
- видна в 6: modern-history/modern-history-q04, modern-history/modern-history-q05, modern-history/modern-history-q06, modern-history/modern-history-q12, modern-history/modern-history-q17, modern-history/modern-history-q96

## 洪秀全 — Хун Сюцюань — предводитель Тайпинского восстания 1851–1864 годов

- выдаёт modern-history/modern-history-q110: ответ 洪秀全, Хун Сюцюань; зацепка Тайпинское восстание, та же строка
- видна в 4: modern-history/modern-history-q109, modern-history/modern-history-q111, modern-history/modern-history-q113, modern-history/modern-history-q60

## 活字印刷术 — Печать подвижными литерами — изобретение Би Шэна, глиняные литеры 1041–1048 гг.

- выдаёт people/people-q12: ответ 活字印刷术; зацепка Би Шэн, та же строка
- видна в 6: people/people-q11, people/people-q13, people/people-q14, people/people-q15, people/people-q16, people/people-q17

## 活着 — «Жить» — роман Юй Хуа о судьбе крестьянина Фугуя

- выдаёт literature/literature-q51: ответ Юй Хуа; зацепка Жить, 活着, та же строка
- видна в 11: literature/literature-q10, literature/literature-q11, literature/literature-q13, literature/literature-q16, literature/literature-q17, literature/literature-q18, literature/literature-q88, literature/literature-q89, literature/literature-q90, literature/literature-q91, literature/literature-q92

## 浙江 — Чжэцзян — провинция на юге дельты Янцзы, центр — Ханчжоу

- выдаёт provinces/provinces-q101: ответ Ханчжоу; зацепка провинция Чжэцзян, та же строка
- видна в 14: provinces/provinces-q01, provinces/provinces-q02, provinces/provinces-q03, provinces/provinces-q04, provinces/provinces-q05, provinces/provinces-q06, provinces/provinces-q07, provinces/provinces-q08, provinces/provinces-q09, provinces/provinces-q10, provinces/provinces-q110, provinces/provinces-q122, provinces/provinces-q32, provinces/provinces-q42

## 浙江省 — Провинция Чжэцзян, административный центр — Ханчжоу

- выдаёт provinces/provinces-q101: ответ Ханчжоу; зацепка провинция Чжэцзян
- видна в 1: 2017-18-reg-8

## 浙江省 — Чжэцзян — приморская провинция на юго-востоке Китая, центр — Ханчжоу

- выдаёт provinces/provinces-q101: ответ Ханчжоу; зацепка провинция Чжэцзян, та же строка
- видна в 8: provinces/provinces-q111, provinces/provinces-q112, provinces/provinces-q12, provinces/provinces-q123, provinces/provinces-q13, provinces/provinces-q14, provinces/provinces-q15, provinces/provinces-q16

## 涅瓦河 — Нева — река, в устье которой основан Санкт-Петербург

- выдаёт provinces/provinces-q105: ответ 涅瓦河; зацепка Санкт-Петербург, та же строка
- видна в 2: provinces/provinces-q104, provinces/provinces-q83

## 深圳 — Шэньчжэнь (Гуандун), с 1980 года одна из четырёх первых особых экономических зон КНР

- выдаёт modern-china/modern-china-q09: ответ 深圳, Шэньчжэнь; зацепка 1980 год, особая экономическая зона
- видна в 20: modern-china/modern-china-q01, modern-china/modern-china-q02, provinces/provinces-q115, provinces/provinces-q116, provinces/provinces-q117, provinces/provinces-q119, provinces/provinces-q121, provinces/provinces-q20, provinces/provinces-q21, provinces/provinces-q22, provinces/provinces-q24, provinces/provinces-q25, provinces/provinces-q26, provinces/provinces-q27, provinces/provinces-q28, provinces/provinces-q29, provinces/provinces-q30, provinces/provinces-q52, provinces/provinces-q53, provinces/provinces-q87

## 清 — Династия Цин — маньчжурская, правила Китаем с 1644 по 1912 год

- выдаёт dynasties/dynasties-q113: ответ маньчжуры; зацепка династия Цинь, та же строка
- видна в 6: dynasties/dynasties-q01, dynasties/dynasties-q07, dynasties/dynasties-q107, dynasties/dynasties-q108, dynasties/dynasties-q115, dynasties/dynasties-q22

## 清代 — Династия Цин — маньчжурская, правила Китаем с 1644 по 1912 год

- выдаёт dynasties/dynasties-q113: ответ маньчжуры; зацепка династия Цинь, та же строка
- видна в 2: dynasties/dynasties-q02, dynasties/dynasties-q15

## 清明上河图 — «Праздник Цинмин на реке» — панорама столицы Бяньцзин кисти Чжан Цзэдуаня

- выдаёт painting/painting-q09: ответ Чжан Цзэдуань; зацепка 清明上河图, та же строка
- видна в 1: painting/painting-q103

## 清朝 — Династия Цин — маньчжурская, правила Китаем с 1644 по 1912 год

- выдаёт dynasties/dynasties-q113: ответ маньчжуры; зацепка династия Цинь, та же строка
- видна в 7: dynasties/dynasties-q04, dynasties/dynasties-q06, dynasties/dynasties-q109, dynasties/dynasties-q110, dynasties/dynasties-q111, dynasties/dynasties-q114, dynasties/dynasties-q13

## 渝 — Сокращение Чунцина — от древнего названия реки Цзялинцзян, Юйшуй

- выдаёт provinces/provinces-q31: ответ 渝; зацепка Чунцин, та же строка
- видна в 7: provinces/provinces-q102, provinces/provinces-q19, provinces/provinces-q41, provinces/provinces-q45, provinces/provinces-q93, provinces/provinces-q94, provinces/provinces-q95

## 渤海 — Бохай — внутреннее море Китая, сюда впадают Хуанхэ и Хайхэ

- выдаёт nature/nature-q06: ответ 渤海; зацепка Хуанхэ, та же строка
- видна в 1: nature/nature-q141

## 湖南 — Хунань — здесь Улинюань с каменными столбами Чжанцзяцзе

- выдаёт nature/nature-q157: ответ 湖南; зацепка Чжанцзяцзе, та же строка
- видна в 2: nature/nature-q158, nature/nature-q159

## 湖南 — Хунань — здесь гора 衡山 (Хэншань), Южный пик пяти священных гор

- выдаёт nature/nature-q10: ответ 衡山; зацепка Южный пик, провинция Хунань, пять священных гор, та же строка
- видна в 7: nature/nature-q03, nature/nature-q145, nature/nature-q146, nature/nature-q147, nature/nature-q148, nature/nature-q149, nature/nature-q50

## 湘 — Сокращение Хунани — по главной реке провинции Сянцзян

- выдаёт provinces/provinces-q43: ответ 湘; зацепка Хунань, та же строка
- видна в 7: provinces/provinces-q102, provinces/provinces-q19, provinces/provinces-q41, provinces/provinces-q45, provinces/provinces-q93, provinces/provinces-q94, provinces/provinces-q95

## 湘方言 — Сянский диалект — диалект большей части Хунани

- выдаёт 2021-22-mun-qa05d78: ответ 湘方言, сянский диалект; зацепка Хунань, та же строка
- видна в 4: ethnos/ethnos-q86, ethnos/ethnos-q87, ethnos/ethnos-q88, ethnos/ethnos-q92

## 满族 — Маньчжуры — народ, основавший династию Цин

- выдаёт dynasties/dynasties-q113: ответ 满族, маньчжуры; зацепка династия Цинь, та же строка
- видна в 1: dynasties/dynasties-q24

## 满族 — Маньчжуры, основатели династии Цин

- выдаёт dynasties/dynasties-q113: ответ 满族, маньчжуры; зацепка династия Цинь
- видна в 1: 2015-16-zak-5

## 澳门特别行政区 — Аомэнь (Макао) — особый административный район Китая, с 1999 года

- выдаёт 2016-17-shk-3: ответ 澳门, Аомэнь; зацепка 1999 год, та же строка
- видна в 3: provinces/provinces-q112, provinces/provinces-q123, provinces/provinces-q16

## 父与子 — «Отцы и дети» — роман Тургенева о «нигилисте» Базарове, 1862 г.

- выдаёт literature/literature-q81: ответ Тургенев; зацепка Отцы и дети
- видна в 1: literature/literature-q67

## 父与子 — «Отцы и дети» — роман Тургенева о конфликте поколений, 1862 г.

- выдаёт literature/literature-q81: ответ Тургенев; зацепка Отцы и дети, та же строка
- видна в 5: literature/literature-q65, literature/literature-q72, literature/literature-q77, literature/literature-q84, literature/literature-q85

## 狂人日记 — «Дневник сумасшедшего» — первый рассказ Лу Синя на байхуа, 1918 г.

- выдаёт literature/literature-q19: ответ 狂人日记, Дневник сумасшедшего; зацепка 1918, Лу Синь, та же строка
- видна в 2: literature/literature-q10, literature/literature-q53

## 猫城记 — «Записки о кошачьем городе» — роман Лао Шэ о Марсе, 1932 г.

- выдаёт literature/literature-q05: ответ Лао Шэ; зацепка Записки о кошачьем городе
- видна в 7: literature/literature-q10, literature/literature-q11, literature/literature-q13, literature/literature-q16, literature/literature-q17, literature/literature-q18, literature/literature-q19

## 玉兔 — Нефритовый заяц — в его честь назван первый китайский луноход «Юйту» (2013)

- выдаёт space/space-q08: ответ 玉兔, нефритовый заяц; зацепка 2013, та же строка
- видна в 2: space/space-q05, space/space-q09

## 王希孟 — Ван Симэн — северосунский юный мастер, автор «Тысячи ли рек и гор»

- выдаёт painting/painting-q03: ответ 王希孟, Ван Симэн; зацепка Тысяча ли рек и гор, Тысячи ли рек и гор, та же строка
- видна в 2: painting/painting-q04, painting/painting-q09

## 珠海 — Чжухай (Гуандун), с 1980 года одна из четырёх первых особых экономических зон КНР

- выдаёт addition-b2-01: ответ 珠海, Чжухай; зацепка Гуандун
- видна в 3: modern-china/modern-china-q01, modern-china/modern-china-q02, modern-china/modern-china-q09

## 琵琶行 — «Песнь о лютнистке» — длинная повествовательная поэма Бо Цзюйи

- выдаёт literature/literature-q25: ответ Бо Цзюйи; зацепка Песнь о лютнистке, 琵琶行, та же строка
- видна в 6: literature/literature-q20, literature/literature-q88, literature/literature-q89, literature/literature-q90, literature/literature-q91, literature/literature-q92

## 瓦连京·谢罗夫 — Серов — портретист рубежа XIX и XX веков, автор «Девочки с персиками»

- выдаёт painting/painting-q88: ответ Девочка с персиками; зацепка Валентин Серов, 瓦连京·谢罗夫, та же строка
- видна в 8: painting/painting-q106, painting/painting-q107, painting/painting-q80, painting/painting-q82, painting/painting-q83, painting/painting-q85, painting/painting-q89, painting/painting-q92

## 瓷都 — «Фарфоровая столица» — прозвище Цзиндэчжэня

- выдаёт 2017-18-mun-10: ответ 瓷都, фарфоровая столица; зацепка Цзиндэчжэнь, та же строка
- видна в 2: provinces/provinces-q50, provinces/provinces-q58

## 甘肃 — Ганьсу — провинция на северо-западе Китая, центр — Ланьчжоу

- выдаёт provinces/provinces-q38: ответ Ланьчжоу; зацепка провинция Ганьсу, та же строка
- видна в 14: provinces/provinces-q01, provinces/provinces-q02, provinces/provinces-q03, provinces/provinces-q04, provinces/provinces-q05, provinces/provinces-q06, provinces/provinces-q07, provinces/provinces-q08, provinces/provinces-q09, provinces/provinces-q10, provinces/provinces-q110, provinces/provinces-q122, provinces/provinces-q32, provinces/provinces-q42

## 甘肃省 — Ганьсу — провинция на северо-западе Китая, её центр — Ланьчжоу

- выдаёт provinces/provinces-q38: ответ Ланьчжоу; зацепка провинция Ганьсу, та же строка
- видна в 7: provinces/provinces-q111, provinces/provinces-q112, provinces/provinces-q12, provinces/provinces-q13, provinces/provinces-q14, provinces/provinces-q15, provinces/provinces-q16

## 甲午中日战争 — Японо-китайская война 1894–1895 годов — её завершил Симоносекский договор

- выдаёт modern-history/modern-history-q78: ответ 1895 год; зацепка Симоносекский договор, та же строка
- видна в 1: modern-history/modern-history-q79

## 白切鸡 — Белая нарезанная курица — отварная курица в собственном вкусе, кантонская кухня

- выдаёт cuisine/cuisine-q83: ответ Кантонская кухня; зацепка 白切鸡
- видна в 1: cuisine/cuisine-q84

## 白嘴鸦飞来了 — «Грачи прилетели» — весенний пейзаж Алексея Саврасова 1871 года

- выдаёт painting/painting-q89: ответ Алексей Саврасов, Саврасов; зацепка Весенний пейзаж, Грачи прилетели, 白嘴鸦飞来了
- видна в 1: painting/painting-q105

## 白嘴鸦飞来了 — «Грачи прилетели» — весенний пейзаж Саврасова, 1871 год

- выдаёт painting/painting-q89: ответ Саврасов; зацепка Весенний пейзаж, Грачи прилетели, 白嘴鸦飞来了, та же строка
- видна в 3: painting/painting-q86, painting/painting-q88, painting/painting-q94

## 白居易 — Бо Цзюйи — поэт эпохи Тан, автор «Песни о лютнистке»

- выдаёт literature/literature-q25: ответ 白居易, Бо Цзюйи; зацепка Песнь о лютнистке, эпоха Тан, та же строка
- видна в 3: literature/literature-q01, literature/literature-q03, literature/literature-q101

## 皖 — Сокращение Аньхоя — по горе Ваньшань, реке Ваньхэ и царству Вань

- выдаёт provinces/provinces-q07: ответ Аньхой; зацепка 皖, та же строка
- видна в 9: provinces/provinces-q102, provinces/provinces-q19, provinces/provinces-q31, provinces/provinces-q41, provinces/provinces-q43, provinces/provinces-q45, provinces/provinces-q93, provinces/provinces-q94, provinces/provinces-q95

## 省 — Провинция — такой статус у Хэбэя, центр — Шицзячжуан

- выдаёт provinces/provinces-q33: ответ Шицзячжуан; зацепка Провинция, та же строка
- видна в 3: provinces/provinces-q109, provinces/provinces-q88, provinces/provinces-q98

## 短篇小说 — Рассказ — жанр «Дневника сумасшедшего» Лу Синя (1918)

- выдаёт literature/literature-q19: ответ Дневник сумасшедшего; зацепка 1918, Лу Синь, Рассказ, та же строка
- видна в 1: literature/literature-q69

## 石家庄 — Шицзячжуан — центр провинции Хэбэй

- выдаёт provinces/provinces-q33: ответ 石家庄, Шицзячжуан; зацепка провинция Хэбэй, та же строка
- видна в 10: provinces/provinces-q100, provinces/provinces-q101, provinces/provinces-q35, provinces/provinces-q36, provinces/provinces-q37, provinces/provinces-q38, provinces/provinces-q92, provinces/provinces-q96, provinces/provinces-q97, provinces/provinces-q99

## 祭侄文稿 — «Черновик надгробного слова племяннику» — синшу Янь Чжэньцина, 758 г.

- выдаёт painting/painting-q22: ответ 祭侄文稿, Черновик надгробного слова племяннику; зацепка Янь Чжэньцин, та же строка
- видна в 2: painting/painting-q104, painting/painting-q17

## 福州 — Фучжоу — город на юго-востоке Китая, в провинции Фуцзянь

- выдаёт 2022-23-shk-mosobl-2: ответ Фуцзянь, провинция Фуцзянь; зацепка Фучжоу
- видна в 18: provinces/provinces-q115, provinces/provinces-q116, provinces/provinces-q117, provinces/provinces-q119, provinces/provinces-q121, provinces/provinces-q20, provinces/provinces-q21, provinces/provinces-q22, provinces/provinces-q24, provinces/provinces-q25, provinces/provinces-q26, provinces/provinces-q27, provinces/provinces-q28, provinces/provinces-q29, provinces/provinces-q30, provinces/provinces-q52, provinces/provinces-q53, provinces/provinces-q87

## 福州 — Фучжоу — центр провинции Фуцзянь

- выдаёт 2022-23-shk-mosobl-2: ответ Фуцзянь, провинция Фуцзянь; зацепка Фучжоу
- видна в 11: provinces/provinces-q100, provinces/provinces-q101, provinces/provinces-q33, provinces/provinces-q35, provinces/provinces-q36, provinces/provinces-q37, provinces/provinces-q38, provinces/provinces-q92, provinces/provinces-q96, provinces/provinces-q97, provinces/provinces-q99

## 福建 — Фуцзянь — здесь земляные дома-крепости тулоу, в списке ЮНЕСКО с 2008 года

- выдаёт 2021-22-reg-q814d54: ответ земляной дом-крепость, тулоу; зацепка провинция Фуцзянь, та же строка
- видна в 1: ethnos/ethnos-q84

## 福建 — Фуцзянь — прибрежная провинция на юго-востоке, напротив Тайваня, центр — Фучжоу

- выдаёт 2022-23-shk-mosobl-2: ответ 福建, Фуцзянь; зацепка Фучжоу
- видна в 14: provinces/provinces-q01, provinces/provinces-q02, provinces/provinces-q03, provinces/provinces-q04, provinces/provinces-q05, provinces/provinces-q06, provinces/provinces-q07, provinces/provinces-q08, provinces/provinces-q09, provinces/provinces-q10, provinces/provinces-q110, provinces/provinces-q122, provinces/provinces-q32, provinces/provinces-q42

## 福建 — Фуцзянь — родина улуна Тегуаньинь из уезда Аньси

- выдаёт addition-b2-05: ответ Тегуаньинь; зацепка провинция Фуцзянь
- видна в 5: cuisine/cuisine-q90, cuisine/cuisine-q92, cuisine/cuisine-q94, cuisine/cuisine-q95, cuisine/cuisine-q96

## 福建省 — Фуцзянь — провинция на юго-востоке Китая у Тайваньского пролива, центр — Фучжоу

- выдаёт 2022-23-shk-mosobl-2: ответ 福建, Фуцзянь; зацепка Фучжоу
- видна в 8: provinces/provinces-q111, provinces/provinces-q112, provinces/provinces-q12, provinces/provinces-q123, provinces/provinces-q13, provinces/provinces-q14, provinces/provinces-q15, provinces/provinces-q16

## 科学发展观 — «Научная концепция развития» — понятие, выдвинутое Ху Цзиньтао в 2003 году

- выдаёт modern-history/modern-history-q27: ответ 科学发展观, научная концепция развития; зацепка 2003 год, Ху Цзиньтао, та же строка
- видна в 4: modern-history/modern-history-q11, modern-history/modern-history-q24, modern-history/modern-history-q26, modern-history/modern-history-q93

## 秦岭 — Циньлин — хребет в Шэньси, граница Севера и Юга Китая

- выдаёт nature/nature-q44: ответ 秦岭; зацепка граница Севера и Юга Китая, та же строка
- видна в 6: nature/nature-q144, nature/nature-q156, nature/nature-q42, nature/nature-q45, nature/nature-q46, nature/nature-q51

## 窑洞 — Яодун — традиционное жильё-пещера лёссового плато

- выдаёт ethnos/ethnos-q84: ответ Лёссовое плато; зацепка пещерное жилище, 窑洞, та же строка
- видна в 1: ethnos/ethnos-q83

## 端午节 — Дуаньу — 5-е число 5-го лунного месяца: лодки-драконы и цзунцзы

- выдаёт holidays/holidays-q47: ответ 端午节; зацепка цзунцзы, та же строка
- видна в 12: holidays/holidays-q02, holidays/holidays-q05, holidays/holidays-q08, holidays/holidays-q09, holidays/holidays-q13, holidays/holidays-q16, holidays/holidays-q42, holidays/holidays-q43, holidays/holidays-q44, holidays/holidays-q45, holidays/holidays-q46, holidays/holidays-q53

## 端午节 — Дуаньу — по преданию, отмечают в память поэта Цюй Юаня, бросившегося в реку Мило

- выдаёт holidays/holidays-q04: ответ 端午节; зацепка Цюй Юань
- видна в 2: holidays/holidays-q33, holidays/holidays-q34

## 符拉迪沃斯托克 — Владивосток — центр Приморского края, портовый город на Японском море

- выдаёт nature/nature-q130: ответ Японское море; зацепка Владивосток
- видна в 13: provinces/provinces-q113, provinces/provinces-q114, provinces/provinces-q63, provinces/provinces-q64, provinces/provinces-q65, provinces/provinces-q66, provinces/provinces-q67, provinces/provinces-q68, provinces/provinces-q69, provinces/provinces-q70, provinces/provinces-q71, provinces/provinces-q75, provinces/provinces-q77

## 第一次鸦片战争 — Первая опиумная война — её завершил Нанкинский договор 1842 года

- выдаёт 2023-24-zak-8: ответ Нанкинский договор; зацепка Первая опиумная война, та же строка
- видна в 1: modern-history/modern-history-q79

## 第三首都 — «Третья столица» — прозвище Казани, зарегистрированный бренд города

- выдаёт provinces/provinces-q107: ответ 第三首都, третья столица; зацепка Казань, та же строка
- видна в 1: provinces/provinces-q106

## 第二钢琴协奏曲 — Второй фортепианный концерт Сергея Рахманинова

- выдаёт people/people-q24: ответ 第二钢琴协奏曲, Второй фортепианный концерт; зацепка Сергей Рахманинов, та же строка
- видна в 3: people/people-q21, people/people-q22, people/people-q23

## 篮球 — Баскетбол — вид спорта Яо Мина, игрока «Хьюстон Рокетс» в НБА

- выдаёт 2021-22-mun-lenobl-9: ответ Яо Мин; зацепка баскетбол, та же строка
- видна в 2: modern-china/modern-china-q17, modern-china/modern-china-q18

## 粤 — Сокращение Гуандуна — от древнего названия южных земель «Юэ»

- выдаёт provinces/provinces-q93: ответ 粤; зацепка Гуандун, та же строка
- видна в 8: provinces/provinces-q102, provinces/provinces-q19, provinces/provinces-q31, provinces/provinces-q41, provinces/provinces-q43, provinces/provinces-q45, provinces/provinces-q94, provinces/provinces-q95

## 粤剧 — Юэцзюй — кантонская опера Гуандуна и Гуанси

- выдаёт ethnos/ethnos-q86: ответ кантонский; зацепка Гуандун
- видна в 2: landmarks/landmarks-q76, landmarks/landmarks-q89

## 粤方言 — Юэский (кантонский) диалект — диалект Гуандуна, Гонконга и Макао

- выдаёт ethnos/ethnos-q86: ответ 粤方言, кантонский; зацепка Гуандун, та же строка
- видна в 3: ethnos/ethnos-q87, ethnos/ethnos-q88, ethnos/ethnos-q92

## 粤菜 — Кантонская (гуандунская) кухня — одна из восьми великих кухонь Китая (название ответа)

- выдаёт ethnos/ethnos-q86: ответ кантонский; зацепка Гуандун
- видна в 2: cuisine/cuisine-q67, cuisine/cuisine-q97

## 粽子 — Цзунцзы — клейкий рис в листьях, еда праздника Дуаньу

- выдаёт holidays/holidays-q47: ответ праздник Дуаньу; зацепка цзунцзы, 粽子
- видна в 1: holidays/holidays-q07

## 索尔仁尼琴 — Солженицын — автор «Архипелага ГУЛАГ» и повести «Один день Ивана Денисовича»

- выдаёт literature/literature-q82: ответ 索尔仁尼琴, Солженицын; зацепка Архипелаг ГУЛАГ, та же строка
- видна в 17: literature/literature-q60, literature/literature-q61, literature/literature-q62, literature/literature-q63, literature/literature-q64, literature/literature-q71, literature/literature-q73, literature/literature-q74, literature/literature-q76, literature/literature-q80, literature/literature-q81, literature/literature-q83, literature/literature-q86, literature/literature-q87, literature/literature-q93, literature/literature-q94, literature/literature-q95

## 红高粱 — «Красный гаолян» — фильм Чжан Имоу по произведениям Мо Яня

- выдаёт cinema/cinema-q01: ответ Чжан Имоу; зацепка Красный гаолян, та же строка
- видна в 5: cinema/cinema-q02, cinema/cinema-q03, cinema/cinema-q09, cinema/cinema-q31, cinema/cinema-q34

## 统一文字 — Единая письменность — её ввёл Цинь Шихуан после объединения Китая в 221 г. до н. э.

- выдаёт dynasties/dynasties-q10: ответ Цинь Шихуан; зацепка 统一文字, та же строка
- видна в 3: dynasties/dynasties-q90, dynasties/dynasties-q91, dynasties/dynasties-q92

## 维克托·瓦斯涅佐夫 — Виктор Васнецов — автор «Богатырей», мастер былинных сюжетов

- выдаёт painting/painting-q80: ответ 维克托·瓦斯涅佐夫, Виктор Васнецов; зацепка Богатыри
- видна в 5: painting/painting-q106, painting/painting-q107, painting/painting-q82, painting/painting-q85, painting/painting-q89

## 缅绍夫 — Владимир Меньшов — режиссёр «Москвы слезам не верит»

- выдаёт cinema/cinema-q30: ответ Москва слезам не верит; зацепка Владимир Меньшов, та же строка
- видна в 1: cinema/cinema-q22

## 羊城 — «Город баранов» — прозвище Гуанчжоу, по легенде о пяти баранах

- выдаёт provinces/provinces-q20: ответ Гуанчжоу; зацепка город баранов, 羊城, та же строка
- видна в 2: provinces/provinces-q50, provinces/provinces-q58

## 翟志刚 — Чжай Чжиган — первый китаец, вышедший в открытый космос (2008)

- выдаёт space/space-q12: ответ 翟志刚, Чжай Чжиган; зацепка 2008, та же строка
- видна в 2: space/space-q04, space/space-q13

## 老子 — Лао-цзы — мыслитель конца эпохи Чуньцю, основатель даосизма

- выдаёт people/people-q01: ответ 老子, Лао-цзы; зацепка эпоха Чуньцю, та же строка
- видна в 4: people/people-q02, people/people-q03, people/people-q04, people/people-q29

## 聚宝盆 — «Чаша сокровищ» — так зовут Цайдамскую котловину за богатство недр

- выдаёт nature/nature-q58: ответ Цайдамская котловина; зацепка чаша сокровищ, 聚宝盆, та же строка
- видна в 1: nature/nature-q60

## 肖像画 — Портрет — жанр Валентина Серова, автора «Девочки с персиками»

- выдаёт painting/painting-q88: ответ Девочка с персиками; зацепка Валентин Серов
- видна в 1: painting/painting-q81

## 肖洛霍夫 — Шолохов — автор романа-эпопеи «Тихий Дон»

- выдаёт literature/literature-q73: ответ 肖洛霍夫, Шолохов; зацепка Тихий Дон, та же строка
- видна в 17: literature/literature-q60, literature/literature-q61, literature/literature-q62, literature/literature-q63, literature/literature-q64, literature/literature-q71, literature/literature-q74, literature/literature-q76, literature/literature-q80, literature/literature-q81, literature/literature-q82, literature/literature-q83, literature/literature-q86, literature/literature-q87, literature/literature-q93, literature/literature-q94, literature/literature-q95

## 胜利日 — День Победы — 9 мая, люди идут в «Бессмертном полку» с портретами ветеранов

- выдаёт holidays/holidays-q27: ответ 胜利日, День Победы; зацепка Бессмертного полка, Бессмертный полк, та же строка
- видна в 3: holidays/holidays-q29, holidays/holidays-q48, holidays/holidays-q49

## 胡锦涛 — Ху Цзиньтао — председатель КНР в 2003–2013 гг.

- выдаёт 2023-24-mun-30: ответ 2013; зацепка председатель КНР
- видна в 9: modern-history/modern-history-q01, modern-history/modern-history-q03, modern-history/modern-history-q04, modern-history/modern-history-q05, modern-history/modern-history-q07, modern-history/modern-history-q17, modern-history/modern-history-q25, modern-history/modern-history-q28, modern-history/modern-history-q96

## 自治区 — Автономный район — статус Внутренней Монголии, первого такого района (1947)

- выдаёт provinces/provinces-q34: ответ Внутренняя Монголия; зацепка Автономный район, та же строка
- видна в 3: provinces/provinces-q109, provinces/provinces-q88, provinces/provinces-q98

## 臭鳜鱼 — «Вонючий» мандариновый окунь — визитная карточка аньхойской кухни

- выдаёт cuisine/cuisine-q78: ответ Аньхойская кухня; зацепка 臭鳜鱼
- видна в 1: cuisine/cuisine-q84

## 苏共中央第一书记 — Первый секретарь ЦК КПСС — пост Никиты Хрущёва с сентября 1953 года

- выдаёт modern-history/modern-history-q31: ответ 苏共中央第一书记, первый секретарь ЦК КПСС; зацепка Никита Хрущёв, та же строка
- видна в 4: modern-history/modern-history-q103, modern-history/modern-history-q104, modern-history/modern-history-q29, modern-history/modern-history-q33

## 苏州 — Сучжоу — здесь Сад скромного чиновника, основанный в 1509 году

- выдаёт landmarks/landmarks-q23: ответ Сад скромного чиновника; зацепка Сучжоу, та же строка
- видна в 1: landmarks/landmarks-q95

## 苏州河 — Сучжоухэ (Усунцзян) — приток Хуанпу, течёт через центр Шанхая

- выдаёт 2016-17-shk-7: ответ Хуанпу; зацепка Шанхай
- видна в 12: nature/nature-q01, nature/nature-q04, nature/nature-q05, nature/nature-q104, nature/nature-q105, nature/nature-q106, nature/nature-q137, nature/nature-q14, nature/nature-q140, nature/nature-q18, nature/nature-q22, nature/nature-q27

## 苏沃洛夫 — Александр Суворов — полководец XVIII века, не знал поражений

- выдаёт modern-history/modern-history-q106: ответ 苏沃洛夫, Александр Суворов, Суворов; зацепка XV век, XVI век, XVIII век, та же строка
- видна в 3: modern-history/modern-history-q08, modern-history/modern-history-q09, modern-history/modern-history-q105

## 苏联总统 — Президент СССР — этот пост в 1990–1991 годах занимал только Михаил Горбачёв

- выдаёт modern-history/modern-history-q104: ответ 苏联总统, президент СССР; зацепка Михаил Горбачёв, та же строка
- видна в 4: modern-history/modern-history-q103, modern-history/modern-history-q29, modern-history/modern-history-q31, modern-history/modern-history-q33

## 茶馆 — «Чайная» — трёхактная пьеса Лао Шэ, поставлена в 1958 г.

- выдаёт literature/literature-q02: ответ Лао Шэ; зацепка Чайная, 茶馆
- видна в 2: literature/literature-q10, literature/literature-q19

## 莫斯科不相信眼泪 — «Москва слезам не верит» — фильм Владимира Меньшова

- выдаёт cinema/cinema-q30: ответ 莫斯科不相信眼泪, Москва слезам не верит; зацепка Владимир Меньшов, та же строка
- видна в 1: cinema/cinema-q24

## 莱蒙托夫 — Лермонтов — автор поэм «Демон» и «Мцыри» и романа «Герой нашего времени» (название ответа)

- выдаёт literature/literature-q84: ответ Герой нашего времени; зацепка Лермонтов
- видна в 15: literature/literature-q60, literature/literature-q61, literature/literature-q62, literature/literature-q63, literature/literature-q66, literature/literature-q71, literature/literature-q73, literature/literature-q80, literature/literature-q81, literature/literature-q82, literature/literature-q86, literature/literature-q87, literature/literature-q93, literature/literature-q94, literature/literature-q95

## 萨哈族 — Саха (якуты) — их героический эпос олонхо

- выдаёт ethnos/ethnos-q75: ответ 萨哈族, Саха (якуты); зацепка олонхо, та же строка
- видна в 1: ethnos/ethnos-q76

## 蒋介石 — Чан Кайши — главнокомандующий Национально-революционной армии в Северном походе

- выдаёт modern-history/modern-history-q66: ответ 蒋介石, Чан Кайши; зацепка Северный поход, та же строка
- видна в 4: modern-history/modern-history-q109, modern-history/modern-history-q110, modern-history/modern-history-q111, modern-history/modern-history-q113

## 蒙古族 — Монголы — их летний праздник надом с борьбой, скачками и стрельбой из лука

- выдаёт holidays/holidays-q40: ответ 蒙古族, монголы; зацепка скачки, стрельба, та же строка
- видна в 2: holidays/holidays-q12, holidays/holidays-q17

## 蒙古族 — Монголы — народ, основавший династию Юань

- выдаёт 2015-16-zak-5: ответ 蒙古族, монголы; зацепка династия Юань, та же строка
- видна в 2: dynasties/dynasties-q113, dynasties/dynasties-q24

## 蔡伦 — Цай Лунь — придворный евнух эпохи Восточной Хань, усовершенствовал изготовление бумаги

- выдаёт people/people-q11: ответ изготовление бумаги; зацепка Цай Лунь, 蔡伦, та же строка
- видна в 1: people/people-q05

## 衡山 — Хэншань в Хунани — Южный пик пяти священных гор

- выдаёт nature/nature-q10: ответ 衡山, Хэншань в Хунани; зацепка Хунань, Южный пик, пять священных гор, та же строка
- видна в 6: nature/nature-q144, nature/nature-q156, nature/nature-q46, nature/nature-q47, nature/nature-q49, nature/nature-q51

## 袁隆平 — Юань Лунпин — агроном, «отец гибридного риса»

- выдаёт people/people-q16: ответ гибридный рис; зацепка Юань Лунпин, 袁隆平, та же строка
- видна в 1: people/people-q05

## 西安 — Сиань — административный центр провинции Шэньси

- выдаёт provinces/provinces-q37: ответ 西安; зацепка провинция Шэньси, та же строка
- видна в 10: provinces/provinces-q100, provinces/provinces-q101, provinces/provinces-q33, provinces/provinces-q35, provinces/provinces-q36, provinces/provinces-q38, provinces/provinces-q92, provinces/provinces-q96, provinces/provinces-q97, provinces/provinces-q99

## 西安 — Сиань — город в Шэньси, где в декабре 1936 года арестовали Чан Кайши

- выдаёт provinces/provinces-q37: ответ 西安; зацепка Шэньси
- видна в 3: modern-history/modern-history-q114, modern-history/modern-history-q63, modern-history/modern-history-q69

## 西安 — Сиань — город на северо-западе Китая, в провинции Шэньси

- выдаёт provinces/provinces-q37: ответ 西安; зацепка провинция Шэньси
- видна в 17: provinces/provinces-q115, provinces/provinces-q117, provinces/provinces-q119, provinces/provinces-q121, provinces/provinces-q20, provinces/provinces-q21, provinces/provinces-q22, provinces/provinces-q24, provinces/provinces-q25, provinces/provinces-q26, provinces/provinces-q27, provinces/provinces-q28, provinces/provinces-q29, provinces/provinces-q30, provinces/provinces-q52, provinces/provinces-q53, provinces/provinces-q87

## 西安 — Сиань — здесь Терракотовая армия у гробницы Цинь Шихуана

- выдаёт 2016-17-shk-4: ответ 西安, Сиань; зацепка Цинь Шихуан, терракотовая армия
- видна в 3: landmarks/landmarks-q100, landmarks/landmarks-q101, landmarks/landmarks-q99

## 西游记 — «Путешествие на Запад» — роман о паломничестве монаха Сюаньцзана (название ответа)

- выдаёт 2018-19-mun-vrn-4: ответ Сюаньцзан; зацепка Путешествие на Запад, 西游记
- видна в 13: literature/literature-q10, literature/literature-q100, literature/literature-q102, literature/literature-q103, literature/literature-q11, literature/literature-q13, literature/literature-q14, literature/literature-q15, literature/literature-q16, literature/literature-q17, literature/literature-q18, literature/literature-q98, literature/literature-q99

## 西游记 — «Путешествие на Запад» — роман, по традиции приписываемый У Чэнъэню

- выдаёт literature/literature-q40: ответ У Чэнъэнь; зацепка Путешествие на Запад, та же строка
- видна в 5: literature/literature-q88, literature/literature-q89, literature/literature-q90, literature/literature-q91, literature/literature-q92

## 西游记 — «Путешествие на Запад», роман XVI века, приписываемый У Чэнъэню

- выдаёт literature/literature-q40: ответ У Чэнъэнь; зацепка Путешествие на Запад
- видна в 1: 2017-18-shk-4

## 西湖 — Сиху в Ханчжоу, объект Всемирного наследия ЮНЕСКО с 2011 г.

- выдаёт provinces/provinces-q87: ответ Ханчжоу; зацепка озеро Сиху, 西湖
- видна в 1: 2017-18-zak-10

## 西湖 — Сиху — озеро в Ханчжоу, объект Всемирного наследия ЮНЕСКО с 2011 г.

- выдаёт provinces/provinces-q87: ответ Ханчжоу; зацепка озеро Сиху, 西湖
- видна в 3: nature/nature-q107, nature/nature-q143, nature/nature-q30

## 西行取经 — Поход за сутрами в Индию — путь монаха Сюаньцзана, 629–645 гг.

- выдаёт people/people-q20: ответ 西行取经; зацепка Сюаньцзан, та же строка
- видна в 2: people/people-q18, people/people-q19

## 解放者 — «Освободитель» — прозвище Александра II, отменившего крепостное право

- выдаёт 2020-21-mun-lenobl-3: ответ Александр II; зацепка Отмена крепостного права
- видна в 2: dynasties/dynasties-q120, dynasties/dynasties-q54

## 许幸之 — Сюй Синчжи — режиссёр фильма «Дети грозных лет» с «Маршем добровольцев»

- выдаёт cinema/cinema-q34: ответ Дети грозных лет; зацепка Марш добровольцев, та же строка
- видна в 3: cinema/cinema-q01, cinema/cinema-q32, cinema/cinema-q33

## 谢肉节 — Масленица — народный праздник проводов зимы, древнее христианства: блины, чучело

- выдаёт holidays/holidays-q48: ответ 谢肉节, Масленица; зацепка Блины
- видна в 5: holidays/holidays-q10, holidays/holidays-q23, holidays/holidays-q24, holidays/holidays-q25, holidays/holidays-q52

## 谢肉节 — Масленица — неделя перед Великим постом: проводы зимы, блины, сжигание чучела

- выдаёт holidays/holidays-q48: ответ 谢肉节, Масленица; зацепка Блины, та же строка
- видна в 3: holidays/holidays-q27, holidays/holidays-q29, holidays/holidays-q49

## 豫 — Сокращение Хэнани — от древней области Юйчжоу

- выдаёт provinces/provinces-q42: ответ Хэнань; зацепка 豫, та же строка
- видна в 9: provinces/provinces-q102, provinces/provinces-q19, provinces/provinces-q31, provinces/provinces-q41, provinces/provinces-q43, provinces/provinces-q45, provinces/provinces-q93, provinces/provinces-q94, provinces/provinces-q95

## 贞观之治 — Правление Чжэньгуань — расцвет Тан при Тай-цзуне (Ли Шимине), 626–649

- выдаёт dynasties/dynasties-q90: ответ 贞观之治, правление Чжэньгуань; зацепка Тай-цзун, Тан, та же строка
- видна в 2: dynasties/dynasties-q91, dynasties/dynasties-q92

## 贵州 — Гуйчжоу — здесь радиотелескоп FAST, «Небесное око»

- выдаёт nature/nature-q154: ответ 贵州, Гуйчжоу; зацепка Небесное око, та же строка
- видна в 2: nature/nature-q155, nature/nature-q67

## 赛马 — Скачки — одно из «трёх мужских состязаний» монгольского праздника Надом

- выдаёт holidays/holidays-q40: ответ монголы; зацепка скачки
- видна в 2: holidays/holidays-q06, holidays/holidays-q15

## 赣方言 — Ганьский диалект — диалект большей части Цзянси

- выдаёт ethnos/ethnos-q88: ответ 赣方言, ганьский диалект; зацепка Цзянси, Цзянсу, та же строка
- видна в 3: ethnos/ethnos-q86, ethnos/ethnos-q87, ethnos/ethnos-q92

## 赫鲁晓夫 — Никита Хрущёв — первый секретарь ЦК КПСС с 1953 года

- выдаёт modern-history/modern-history-q31: ответ первый секретарь ЦК КПСС; зацепка Никита Хрущёв, та же строка
- видна в 2: modern-history/modern-history-q105, modern-history/modern-history-q106

## 越剧 — Юэцзюй — чжэцзянская опера, которую исполняют женщины

- выдаёт 2022-23-mun-8: ответ 越剧, Юэцзюй (чжэцзянская); зацепка Чжэцзян
- видна в 3: landmarks/landmarks-q107, landmarks/landmarks-q76, landmarks/landmarks-q89

## 辛丑条约 — Синьчоуский договор 1901 года — итог войны восьми держав, контрибуция 450 млн лян

- выдаёт modern-history/modern-history-q79: ответ Война восьми держав; зацепка Заключительный протокол, та же строка
- видна в 1: modern-history/modern-history-q108

## 辽 — Династия Ляо — киданьская, 916–1125, основал Елюй Абаоцзи

- выдаёт dynasties/dynasties-q24: ответ кидани; зацепка династия Ляо, та же строка
- видна в 6: dynasties/dynasties-q01, dynasties/dynasties-q07, dynasties/dynasties-q107, dynasties/dynasties-q108, dynasties/dynasties-q115, dynasties/dynasties-q22

## 辽宁 — Ляонин — одна из основных областей расселения маньчжуров

- выдаёт 2018-19-shk-6: ответ 辽宁, Ляонин; зацепка маньчжуры, та же строка
- видна в 3: ethnos/ethnos-q04, ethnos/ethnos-q78, ethnos/ethnos-q79

## 辽宁 — Ляонин — приморская провинция на юге Северо-Востока, центр — Шэньян

- выдаёт provinces/provinces-q35: ответ Шэньян; зацепка провинция Ляонин, та же строка
- видна в 14: provinces/provinces-q01, provinces/provinces-q02, provinces/provinces-q03, provinces/provinces-q04, provinces/provinces-q05, provinces/provinces-q06, provinces/provinces-q07, provinces/provinces-q08, provinces/provinces-q09, provinces/provinces-q10, provinces/provinces-q110, provinces/provinces-q122, provinces/provinces-q32, provinces/provinces-q42

## 辽宁 — Ляонин, провинция на северо-востоке Китая, центр — Шэньян

- выдаёт provinces/provinces-q35: ответ Шэньян; зацепка провинция Ляонин
- видна в 1: 2015-16-reg-1

## 辽宁省 — Ляонин — приморская провинция на юге Северо-Востока, центр — Шэньян

- выдаёт provinces/provinces-q35: ответ Шэньян; зацепка Ляонин, та же строка
- видна в 8: provinces/provinces-q111, provinces/provinces-q112, provinces/provinces-q12, provinces/provinces-q123, provinces/provinces-q13, provinces/provinces-q14, provinces/provinces-q15, provinces/provinces-q16

## 辽朝 — Династия Ляо — киданьская, 916–1125, основал Елюй Абаоцзи

- выдаёт dynasties/dynasties-q24: ответ кидани; зацепка династия Ляо, та же строка
- видна в 9: dynasties/dynasties-q03, dynasties/dynasties-q04, dynasties/dynasties-q06, dynasties/dynasties-q109, dynasties/dynasties-q110, dynasties/dynasties-q111, dynasties/dynasties-q112, dynasties/dynasties-q114, dynasties/dynasties-q13

## 近卫军临刑的早晨 — «Утро стрелецкой казни» — картина Василия Сурикова 1881 года

- выдаёт painting/painting-q94: ответ 近卫军临刑的早晨, Утро стрелецкой казни; зацепка Василий Суриков
- видна в 1: painting/painting-q105

## 近卫军临刑的早晨 — «Утро стрелецкой казни» — картина Сурикова, 1881 год

- выдаёт painting/painting-q94: ответ 近卫军临刑的早晨, Утро стрелецкой казни; зацепка Суриков, та же строка
- видна в 2: painting/painting-q86, painting/painting-q88

## 迷雾中的小刺猬 — «Ёжик в тумане» — мультфильм Юрия Норштейна 1975 года

- выдаёт cinema/cinema-q28: ответ 迷雾中的小刺猬, Ёжик в тумане; зацепка 1975 год, Юрий Норштейн, та же строка
- видна в 3: cinema/cinema-q27, cinema/cinema-q29, cinema/cinema-q30

## 造纸术 — Изготовление бумаги — одно из четырёх великих изобретений, Цай Лунь его усовершенствовал

- выдаёт people/people-q11: ответ 造纸术, изготовление бумаги; зацепка Цай Лунь, та же строка
- видна в 6: people/people-q12, people/people-q13, people/people-q14, people/people-q15, people/people-q16, people/people-q17

## 邓小平 — Дэн Сяопин — «главный архитектор» реформ и открытости Китая

- выдаёт modern-history/modern-history-q01: ответ 邓小平, Дэн Сяопин; зацепка Реформы и открытость
- видна в 5: modern-history/modern-history-q109, modern-history/modern-history-q110, modern-history/modern-history-q111, modern-history/modern-history-q113, modern-history/modern-history-q66

## 那达慕 — Надом — праздник монголов: борьба, скачки и стрельба из лука

- выдаёт holidays/holidays-q40: ответ монголы; зацепка скачки, стрельба, 那达慕, та же строка
- видна в 9: holidays/holidays-q02, holidays/holidays-q16, holidays/holidays-q18, holidays/holidays-q42, holidays/holidays-q43, holidays/holidays-q44, holidays/holidays-q45, holidays/holidays-q46, holidays/holidays-q47

## 郭帆 — Го Фань — режиссёр фантастического фильма «Блуждающая Земля» (2019)

- выдаёт cinema/cinema-q31: ответ Блуждающая Земля; зацепка 2019, та же строка
- видна в 3: cinema/cinema-q01, cinema/cinema-q32, cinema/cinema-q33

## 都江堰 — Дуцзянъянь — древняя оросительная система на реке Миньцзян в Сычуани

- выдаёт nature/nature-q63: ответ река Миньцзян; зацепка Дуцзянъянь, та же строка
- видна в 1: nature/nature-q70

## 鄂毕河 — Обь — на ней стоит Новосибирск, третий по числу жителей город России

- выдаёт nature/nature-q128: ответ 鄂毕河; зацепка Новосибирск
- видна в 3: provinces/provinces-q104, provinces/provinces-q105, provinces/provinces-q83

## 鄱阳湖 — Поянху в Цзянси — крупнейшее пресноводное озеро Китая

- выдаёт 2017-18-zak-10: ответ 鄱阳湖, Поянху; зацепка крупнейшее пресноводное озеро Китая, та же строка
- видна в 3: nature/nature-q107, nature/nature-q143, nature/nature-q30

## 重庆 — Чунцин — в его районе Дацзу скальные рельефы IX–XIII веков

- выдаёт provinces/provinces-q27: ответ 重庆, Чунцин; зацепка Дацзу
- видна в 4: landmarks/landmarks-q48, landmarks/landmarks-q96, landmarks/landmarks-q97, landmarks/landmarks-q98

## 重庆 — Чунцин — временная столица Китайской Республики в войну с Японией (с 1937 года)

- выдаёт state/state-q15: ответ 重庆, Чунцин; зацепка Япония, та же строка
- видна в 1: state/state-q06

## 重庆 — Чунцин — город центрального подчинения на юго-западе Китая

- выдаёт provinces/provinces-q26: ответ 重庆, Чунцин; зацепка город центрального подчинения, та же строка
- видна в 16: provinces/provinces-q115, provinces/provinces-q117, provinces/provinces-q119, provinces/provinces-q121, provinces/provinces-q20, provinces/provinces-q21, provinces/provinces-q22, provinces/provinces-q24, provinces/provinces-q25, provinces/provinces-q28, provinces/provinces-q29, provinces/provinces-q30, provinces/provinces-q52, provinces/provinces-q53, provinces/provinces-q87, provinces/provinces-q91

## 重庆 — Чунцин, временная столица Китайской Республики в годы войны с Японией

- выдаёт state/state-q15: ответ 重庆, Чунцин; зацепка Япония
- видна в 1: modern-china/modern-china-q03

## 重庆市 — Чунцин — город центрального подчинения в верховьях Янцзы

- выдаёт provinces/provinces-q26: ответ 重庆, Чунцин; зацепка город центрального подчинения
- видна в 3: provinces/provinces-q112, provinces/provinces-q123, provinces/provinces-q16

## 金陵 — Цзиньлин — старое название Нанкина, столица царства Южная Тан (937–975)

- выдаёт state/state-q14: ответ 金陵, Цзиньлин; зацепка Нанкин
- видна в 6: dynasties/dynasties-q08, dynasties/dynasties-q103, dynasties/dynasties-q104, dynasties/dynasties-q105, dynasties/dynasties-q106, dynasties/dynasties-q20

## 钱学森 — Цянь Сюэсэнь — учёный-ракетчик, «отец китайской космонавтики»

- выдаёт people/people-q15: ответ китайская космонавтика; зацепка Цянь Сюэсэнь, 钱学森, та же строка
- видна в 1: people/people-q05

## 镇压十二月党人起义 — Восстание декабристов 14 декабря 1825 года подавлено Николаем I

- выдаёт modern-history/modern-history-q80: ответ 1825 год; зацепка Восстание декабристов
- видна в 5: dynasties/dynasties-q117, dynasties/dynasties-q118, dynasties/dynasties-q119, dynasties/dynasties-q121, dynasties/dynasties-q122

## 长春 — Чанчунь — центр провинции Цзилинь

- выдаёт provinces/provinces-q36: ответ 长春, Чанчунь; зацепка Провинция Цзилинь, та же строка
- видна в 10: provinces/provinces-q100, provinces/provinces-q101, provinces/provinces-q33, provinces/provinces-q35, provinces/provinces-q37, provinces/provinces-q38, provinces/provinces-q92, provinces/provinces-q96, provinces/provinces-q97, provinces/provinces-q99

## 长江 — Янцзы — на ней стоит ГЭС «Три ущелья» (Санься), крупнейшая в мире

- выдаёт nature/nature-q153: ответ 长江; зацепка Три ущелья, та же строка
- видна в 1: nature/nature-q63

## 长江三峡 — Три ущелья Янцзы — на обороте купюры 10 юаней

- выдаёт money/money-q05: ответ 长江三峡, Три ущелья; зацепка 10, та же строка
- видна в 4: money/money-q06, money/money-q07, money/money-q39, money/money-q40

## 长篇小说 — Роман — так в Китае числят «Мёртвые души»; сам Гоголь назвал их поэмой

- выдаёт literature/literature-q67: ответ Мёртвые души; зацепка Гоголь
- видна в 1: literature/literature-q68

## 长诗 — Поэма — жанр «Демона» Лермонтова (1829–1839)

- выдаёт literature/literature-q63: ответ Лермонтов; зацепка Поэма
- видна в 1: literature/literature-q68

## 闽 — Сокращение Фуцзяни — от древнего названия края Минь, известного со времён Чжоу

- выдаёт provinces/provinces-q41: ответ 闽; зацепка Фуцзянь, та же строка
- видна в 8: provinces/provinces-q102, provinces/provinces-q19, provinces/provinces-q31, provinces/provinces-q43, provinces/provinces-q45, provinces/provinces-q93, provinces/provinces-q94, provinces/provinces-q95

## 闽方言 — Миньский диалект — диалект Фуцзяни и соседних земель

- выдаёт ethnos/ethnos-q87: ответ 闽方言, миньский диалект; зацепка Фуцзянь, та же строка
- видна в 2: ethnos/ethnos-q88, ethnos/ethnos-q92

## 阿列克谢·萨夫拉索夫 — Саврасов — пейзажист XIX века, автор «Грачей прилетели»

- выдаёт painting/painting-q89: ответ 阿列克谢·萨夫拉索夫, Саврасов; зацепка Грачи прилетели, та же строка
- видна в 6: painting/painting-q106, painting/painting-q107, painting/painting-q80, painting/painting-q82, painting/painting-q83, painting/painting-q85

## 阿尔汉格尔斯克 — Архангельск — город на купюре 500 рублей образца 1997 года

- выдаёт money/money-q37: ответ 阿尔汉格尔斯克, Архангельск; зацепка 1997 год, та же строка
- видна в 7: money/money-q09, money/money-q10, money/money-q11, money/money-q12, money/money-q13, money/money-q14, money/money-q15

## 阿尔泰山 — Алтай — горы на стыке России, Казахстана, Китая и Монголии; высшая точка 4506 м

- выдаёт nature/nature-q115: ответ 阿尔泰山; зацепка монголы, та же строка
- видна в 6: nature/nature-q116, nature/nature-q133, nature/nature-q161, nature/nature-q162, nature/nature-q42, nature/nature-q45

## 陈凯歌 — Чэнь Кайгэ — режиссёр «Прощай, моя наложница» (1993)

- выдаёт cinema/cinema-q32: ответ 陈凯歌, Чэнь Кайгэ; зацепка Прощай, моя наложница, та же строка
- видна в 2: cinema/cinema-q01, cinema/cinema-q33

## 陕西 — Шэньси — здесь Хуашань, Западный пик пяти священных гор

- выдаёт nature/nature-q48: ответ Западный пик; зацепка пять священных гор, та же строка
- видна в 1: nature/nature-q50

## 除夕 — Чуси — канун Праздника весны, последний вечер года: семейный ужин и бдение

- выдаёт 2019-20-mun-kgd-7: ответ 除夕, канун Праздника весны, последний вечер года; зацепка Праздник весны
- видна в 10: holidays/holidays-q01, holidays/holidays-q02, holidays/holidays-q04, holidays/holidays-q05, holidays/holidays-q08, holidays/holidays-q09, holidays/holidays-q13, holidays/holidays-q16, holidays/holidays-q47, holidays/holidays-q53

## 雅罗斯拉夫尔 — Ярославль — город на купюре 1000 рублей образца 1997 года

- выдаёт money/money-q10: ответ 雅罗斯拉夫尔, Ярославль; зацепка 1997 год, та же строка
- видна в 7: money/money-q09, money/money-q11, money/money-q12, money/money-q13, money/money-q14, money/money-q15, money/money-q37

## 雷帝 — «Грозный» — прозвище Ивана IV, первого русского царя

- выдаёт dynasties/dynasties-q120: ответ 雷帝; зацепка Иван IV, та же строка
- видна в 1: dynasties/dynasties-q54

## 青年节 — День молодёжи — 4 мая, в память «Движения 4 мая» 1919 года

- выдаёт 2016-17-reg-6: ответ 1919; зацепка Движение 4 мая
- видна в 2: holidays/holidays-q02, holidays/holidays-q32

## 青海湖 — Кукунор (Цинхай), крупнейшее солёное озеро Китая

- выдаёт nature/nature-q143: ответ 青海湖; зацепка крупнейшее солёное озеро Китая
- видна в 1: 2017-18-zak-10

## 青海湖 — Озеро Цинхай — крупнейшее солёное озеро Китая, дало имя провинции Цинхай

- выдаёт nature/nature-q143: ответ 青海湖, озеро Цинхай; зацепка крупнейшее солёное озеро Китая
- видна в 2: provinces/provinces-q89, provinces/provinces-q90

## 青海湖 — Цинхай (Кукунор) — крупнейшее солёное озеро Китая, дало имя провинции Цинхай

- выдаёт nature/nature-q143: ответ 青海湖; зацепка крупнейшее солёное озеро Китая, та же строка
- видна в 1: nature/nature-q30

## 青花瓷 — Сине-белый фарфор — им славится Цзиндэчжэнь, «фарфоровая столица»

- выдаёт 2017-18-mun-10: ответ фарфоровая столица; зацепка Цзиндэчжэнь, та же строка
- видна в 1: provinces/provinces-q56

## 青茶 — Улун (цинча) — к нему относится Тегуаньинь из Фуцзяни

- выдаёт addition-b2-05: ответ Тегуаньинь; зацепка Фуцзянь
- видна в 3: cuisine/cuisine-q87, cuisine/cuisine-q88, cuisine/cuisine-q89

## 青蒿素 — Артемизинин — средство от малярии, за его открытие Ту Юю получила Нобелевскую премию

- выдаёт people/people-q17: ответ 青蒿素, артемизинин; зацепка Ту Юю, та же строка
- видна в 6: people/people-q11, people/people-q12, people/people-q13, people/people-q14, people/people-q15, people/people-q16

## 静夜思 — «Думы тихой ночью» — четверостишие Ли Бо о тоске по дому

- выдаёт literature/literature-q88: ответ 静夜思, Думы тихой ночью; зацепка Ли Бо, та же строка
- видна в 4: literature/literature-q89, literature/literature-q90, literature/literature-q91, literature/literature-q92

## 静静的顿河 — «Тихий Дон» — роман-эпопея Шолохова о донских казаках

- выдаёт literature/literature-q73: ответ Шолохов; зацепка Тихий Дон
- видна в 1: literature/literature-q67

## 静静的顿河 — «Тихий Дон» — роман-эпопея Шолохова о донских казаках, 1928–1940 гг.

- выдаёт literature/literature-q73: ответ Шолохов; зацепка Тихий Дон, та же строка
- видна в 5: literature/literature-q65, literature/literature-q72, literature/literature-q77, literature/literature-q84, literature/literature-q85

## 非欧几何 — Неевклидова геометрия — создал Николай Лобачевский

- выдаёт people/people-q26: ответ 非欧几何, Неевклидова геометрия; зацепка Николай Лобачевский, та же строка
- видна в 3: people/people-q25, people/people-q27, people/people-q28

## 额尔齐斯河 — Иртыш — главный приток Оби, берёт начало в Китае, в Синьцзяне

- выдаёт nature/nature-q102: ответ 额尔齐斯河; зацепка Синьцзян, та же строка
- видна в 9: nature/nature-q05, nature/nature-q100, nature/nature-q101, nature/nature-q103, nature/nature-q104, nature/nature-q105, nature/nature-q106, nature/nature-q127, nature/nature-q128

## 风云儿女 — «Дети грозных лет» — фильм 1935 года, для которого написан «Марш добровольцев»

- выдаёт cinema/cinema-q34: ответ 风云儿女, Дети грозных лет; зацепка Марш добровольцев, та же строка
- видна в 4: cinema/cinema-q02, cinema/cinema-q03, cinema/cinema-q09, cinema/cinema-q31

## 风景画 — Пейзаж — жанр Шишкина, певца русского леса, автора «Утра в сосновом лесу»

- выдаёт painting/painting-q107: ответ Шишкин; зацепка Утро в сосновом лесу, сосна
- видна в 1: painting/painting-q81

## 香港岛 — Остров Гонконг отошёл Англии по Нанкинскому договору 1842 года

- выдаёт modern-history/modern-history-q115: ответ 香港岛, остров Гонконг; зацепка 1842 год, Англия, та же строка
- видна в 1: modern-history/modern-history-q116

## 香港特别行政区 — Сянган (Гонконг) — особый административный район на юге Китая, с 1997 года

- выдаёт 2016-17-mun-4: ответ 1997; зацепка Гонконг
- видна в 3: provinces/provinces-q112, provinces/provinces-q123, provinces/provinces-q16

## 鱼香肉丝 — Юйсян жоусы — обычное блюдо сычуаньской кухни, не праздничное

- выдаёт cuisine/cuisine-q01: ответ Сычуаньская кухня; зацепка юйсян жоусы, 鱼香肉丝
- видна в 1: holidays/holidays-q07

## 鹊桥 — Цюэцяо — спутник-ретранслятор у точки L2 для связи с «Чанъэ-4», 2018

- выдаёт space/space-q09: ответ 鹊桥; зацепка 2018, та же строка
- видна в 1: space/space-q20

## 黄浦江 — Хуанпу — главная река Шанхая, впадает в Янцзы у Усункоу

- выдаёт 2016-17-shk-7: ответ 黄浦江, Хуанпу; зацепка Шанхай, та же строка
- видна в 12: nature/nature-q01, nature/nature-q04, nature/nature-q05, nature/nature-q104, nature/nature-q105, nature/nature-q106, nature/nature-q137, nature/nature-q14, nature/nature-q140, nature/nature-q18, nature/nature-q22, nature/nature-q27

## 黄袍加身 — «Жёлтый халат на плечи» — переворот 960 года, приведший Чжао Куанъиня на трон

- выдаёт dynasties/dynasties-q91: ответ 黄袍加身; зацепка Чжао Куанъинь, та же строка
- видна в 2: dynasties/dynasties-q90, dynasties/dynasties-q92

## 黑海 — Чёрное море — на его берегу лежат Краснодарский край и курорт Сочи

- выдаёт nature/nature-q112: ответ 黑海, Чёрное море; зацепка Краснодарский край
- видна в 2: nature/nature-q08, nature/nature-q130

## 黑茶 — Тёмный чай (не «чёрный») — к нему относится юньнаньский пуэр

- выдаёт 2020-21-mun-yak-9: ответ 黑茶, тёмный чай; зацепка Пуэр
- видна в 5: cuisine/cuisine-q85, cuisine/cuisine-q86, cuisine/cuisine-q87, cuisine/cuisine-q88, cuisine/cuisine-q89

## 黑龙江 — Провинция Хэйлунцзян на границе с Россией, центр — Харбин

- выдаёт 2020-21-mun-mosobl-47: ответ Харбин; зацепка провинция Хэйлунцзян, 黑龙江
- видна в 2: 2015-16-reg-4, 2018-19-shk-6

## 黑龙江 — Хэйлунцзян — самая северная провинция Китая, центр — Харбин (название ответа)

- выдаёт 2020-21-mun-mosobl-47: ответ Харбин; зацепка провинция Хэйлунцзян, 黑龙江
- видна в 14: provinces/provinces-q01, provinces/provinces-q02, provinces/provinces-q03, provinces/provinces-q04, provinces/provinces-q05, provinces/provinces-q06, provinces/provinces-q07, provinces/provinces-q08, provinces/provinces-q09, provinces/provinces-q10, provinces/provinces-q110, provinces/provinces-q122, provinces/provinces-q32, provinces/provinces-q42

## 黑龙江省 — Хэйлунцзян — самая северная провинция Китая, центр — Харбин

- выдаёт 2020-21-mun-mosobl-47: ответ Харбин; зацепка Провинция Хэйлунцзян, 黑龙江省
- видна в 8: provinces/provinces-q111, provinces/provinces-q112, provinces/provinces-q12, provinces/provinces-q123, provinces/provinces-q13, provinces/provinces-q14, provinces/provinces-q15, provinces/provinces-q16

## 黔 — Сокращение Гуйчжоу — Цянь; второе её сокращение — 贵

- выдаёт provinces/provinces-q45: ответ 黔; зацепка Гуйчжоу, та же строка
- видна в 9: provinces/provinces-q102, provinces/provinces-q103, provinces/provinces-q19, provinces/provinces-q31, provinces/provinces-q41, provinces/provinces-q43, provinces/provinces-q93, provinces/provinces-q94, provinces/provinces-q95

## 鼠 — Крыса — одно из двенадцати животных китайского зодиака

- выдаёт sets/sets-q12: ответ 鼠, крыса; зацепка китайский зодиак, та же строка
- видна в 2: sets/sets-q03, sets/sets-q04

## 齐白石 — Ци Байши — художник XX века, мастер креветок и цветов-птиц

- выдаёт painting/painting-q05: ответ 齐白石, Ци Байши; зацепка XX век, креветок, та же строка
- видна в 4: painting/painting-q01, painting/painting-q02, painting/painting-q04, painting/painting-q06

## 龙 — Дракон — одно из двенадцати животных китайского зодиака

- выдаёт 2025-26-mun-vlad-7: ответ 龙, дракон; зацепка китайский зодиак, та же строка
- видна в 4: sets/sets-q03, sets/sets-q04, sets/sets-q05, sets/sets-q12

## 龙泉青瓷 — Лунцюаньский селадон — зеленоватый фарфор из Чжэцзяна, расцвет при Южной Сун

- выдаёт crafts/crafts-q03: ответ 龙泉青瓷, лунцюаньский селадон; зацепка фарфор, та же строка
- видна в 1: crafts/crafts-q131
