# Книга для чтения «中国文化故事»: план

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** инструменты, которые проверяют и собирают книжку уроков в PDF и EPUB, три принятых
пробных урока в итоговом формате и первый блок «Мифы о начале мира» (13 уроков) на чтение автору.
Остальные семь блоков пишутся по тому же порядку после отзыва автора (задача 8).

**Architecture:** уроки — Markdown-файлы в `book/src/<блок>/`. Четыре модуля в `scripts/`:
`book_lesson.py` (разбор и проверка формата урока), `book_level.py` (разбор текста на слова
через jieba, уровень HSK, решение, над каким словом ставить пиньинь), `book_render.py` (HTML,
PDF через Chrome, EPUB через `zipfile`) и `book.py` (командная строка). Списки HSK лежат в
репозитории (`book/hsk/`), чтобы проверка шла и в CI.

**Tech Stack:** Python 3.12+ (стандартная библиотека + `jieba==0.42.1`), Google Chrome без окна
для PDF, `unittest`.

**Spec:** `docs/superpowers/specs/2026-10-16-culture-reader-design.md`. Образцы урока —
`book/samples/src/*.md` (проба, после задачи 6 удаляются).

## Global Constraints

- Уровень: знакомыми считаются слова HSK 2.0 уровней 1–4; у каждого слова выше HSK 4 и у каждого имени при первом появлении в уроке — пиньинь, повторно — без него.
- Любое слово вне HSK 1–4 без пиньиня останавливает проверку (`book.py check` → код 1).
- Длина основного текста в иероглифах (без знаков препинания, латиницы, цифр, «原文», «生词», заданий и «注»): мифы и сказания 700–1500, чэнъюй 300–600, праздники 600–1000, символы 400–700, люди 600–1000, культура 600–1000, литература 1100–2500.
- «生词»: 15–25 слов, у чэнъюй 10–20; «判断正误» — 4–5 пунктов (ответ 对/错); «回答问题» — 3–5.
- Факты: опорные (имена, даты, числа, авторство, ядро сюжета) — официальный или академический источник с цитатой; живые подробности — хотя бы один изданный пересказ; без источника не пишется.
- Цитаты: древние первоисточники дословно; писатели XX века — не длиннее двух предложений, не больше двух на урок.
- В книжку идут только уроки со `status: accepted`; `--drafts` собирает всё с пометкой «черновик».
- `sources/` не трогать; `data/` книжка не меняет.
- Агентов (писатели, проверяющие, ревьюер) запускать только с согласия автора на каждый запуск, не больше трёх одновременно.
- Каждое заметное изменение — запись в `CHANGELOG.md`; перед слиянием в `master` — спросить автора, нужно ли ревью.
- Готовые PDF/EPUB (`book/out/`) не коммитить.

## Review Focus

1. Многозначный иероглиф уровня HSK 5–6, стоящий отдельным словом (朝, 重, 藏…), не должен получать пиньинь из списка вслепую — проверка требует ручной пометки. Тест в задаче 3.
2. Слово с ручной пометкой `{слово|pinyin}`, которое уже встречалось раньше без пометки, — первое появление осталось без пиньиня; это ошибка. Тест в задаче 3.
3. Слово из «生词», которое в тексте стоит только внутри более длинного слова (蟠桃 внутри 蟠桃园), не считается «лишним» в «生词». Тест в задаче 2.
4. Урок без файла иллюстрации собирается с рамкой-заглушкой, сборка не падает. Тест в задаче 5.
5. Символы `& < >`, кавычки «“”», 《》 и многоточие «……» в тексте и названиях дают корректный XHTML в EPUB. Тест в задаче 5.

---

### Задача 1: ветка, зависимость, списки HSK

**Files:**
- Create: `requirements.txt` (`jieba==0.42.1`)
- Create: `book/hsk/hsk20.tsv`, `book/hsk/extra.tsv`
- Create: `scripts/book_hsk.py`
- Create: `test/test_book_hsk.py`
- Modify: `.github/workflows/pages.yml` — шаг `python3 -m pip install -r requirements.txt` перед «Python-тесты»
- Modify: `.gitignore` — `book/out/`

**Interfaces:**
- Produces: `book_hsk.import_anki(anki_dir: Path) -> list[tuple[str, str, int]]` — (слово, пиньинь, наименьший уровень), по словам без повторов; `book_hsk.write_tsv(rows, path)`.
- Produces: формат `book/hsk/hsk20.tsv` — `слово\tпиньинь\tуровень`, отсортировано по уровню, затем по слову. `book/hsk/extra.tsv` — `слово\tпиньинь\tуровень\tпричина`.

- [ ] **Шаг 1: ветка и коммит описания и плана**

```bash
git switch -c feat/culture-reader
git add docs/superpowers/specs/2026-10-16-culture-reader-design.md docs/superpowers/plans/2026-10-16-culture-reader.md
git commit -m "Книга для чтения: описание и план"
```

- [ ] **Шаг 2: тест импорта.** `test_import_takes_lowest_level`: во временной папке файлы `HSK1.txt` (`爱\tài\tлюбить\t\tHSK1`) и `HSK4F.txt` (`爱\tài\t…\t\tHSK4` и `阿姨\tàyí\tтётя\t\tHSK4`, первая строка с BOM). `import_anki` возвращает `[("爱","ài",1), ("阿姨","àyí",4)]`. `test_variants_split`: строка `是|是不是\tshì\t…` даёт два слова. Файлы ищутся по именам `HSK1.txt, HSK2.txt, HSK3F.txt, HSK4F.txt, HSK5F.txt, HSK6F.txt` (уровни 1–6, списки накопительные).

- [ ] **Шаг 3:** `python3 -m unittest test.test_book_hsk -v` → FAIL (нет модуля).

- [ ] **Шаг 4: реализовать `scripts/book_hsk.py`.** Разбор как в пробном скрипте: `utf-8-sig`, табуляция, варианты через `|｜/／`, скобки `（…)` отбрасываются. Запуск `python3 scripts/book_hsk.py <папка Anki>` пишет `book/hsk/hsk20.tsv`.

- [ ] **Шаг 5:** тест → PASS. Сгенерировать список:

```bash
python3 scripts/book_hsk.py "$HOME/Yandex.Disk.localized/Китайский язык/02-Навыки/Лексика/Anki"
wc -l book/hsk/hsk20.tsv
```

Ожидается около 5000 строк. `extra.tsv` пока только с заголовком (наполняется в задаче 3).

- [ ] **Шаг 6: зависимость.** `python3 -m pip install -r requirements.txt`; шаг в `pages.yml`; `book/out/` в `.gitignore`.

- [ ] **Шаг 7: коммит.** `git commit -m "Книга: списки HSK 2.0 в репозитории, jieba"`

### Задача 2: формат урока и его проверка

**Files:**
- Create: `book/blocks.json`
- Create: `scripts/book_lesson.py`
- Create: `test/test_book_lesson.py`

**Interfaces:**
- Produces (`book_lesson.py`):
  - `@dataclass Gloss(word: str, pinyin: str, ru: str)`
  - `@dataclass Item(text: str, answer: str)` — для «判断正误» `answer` ∈ {`对`, `错`}
  - `@dataclass Source(kind: str, title: str, url: str, quote: str, checked_at: str)` — `kind` ∈ {`official`, `academic`, `retelling`}
  - `@dataclass Lesson(id: str, block: str, title: str, image: str, status: str, body: str, gloss: list[Gloss], tf: list[Item], qa: list[Item], note: str, sources: list[Source], path: Path)`
  - `class LessonError(Exception)`; `parse_lesson(path: Path) -> Lesson` (бросает `LessonError` с путём в тексте)
  - `load_blocks(path: Path = BOOK / "blocks.json") -> list[dict]`
  - `load_lessons(src: Path = BOOK / "src") -> list[Lesson]` — в порядке блоков из `blocks.json`, внутри блока — по имени файла
  - `body_text(lesson) -> str` — основной текст без пометок `{|}`, без «原文»
  - `count_han(text: str) -> int`
  - `validate_lesson(lesson: Lesson, blocks: list[dict]) -> list[str]`
  - `BOOK = Path(__file__).resolve().parents[1] / "book"`

Формат файла — как у пробных уроков, с изменениями: в заголовке `block:` — слаг блока, добавлено
`status:` (`draft` | `checked` | `accepted`); новый раздел `## 来源` со строками
`- kind | название | ссылка | цитата | ГГГГ-ММ-ДД`. Имя файла — `NN-<id>.md`.

`book/blocks.json` (названия — решение исполнителя, автор может поменять):

```json
[
  {"slug": "myths", "zh": "开天辟地", "ru": "Мифы о начале мира", "min": 700, "max": 1500, "gloss": [15, 25]},
  {"slug": "folk", "zh": "民间传说", "ru": "Народные сказания", "min": 700, "max": 1500, "gloss": [15, 25]},
  {"slug": "chengyu", "zh": "成语故事", "ru": "Истории чэнъюй", "min": 300, "max": 600, "gloss": [10, 20]},
  {"slug": "festivals", "zh": "节日传说", "ru": "Праздники и их легенды", "min": 600, "max": 1000, "gloss": [15, 25]},
  {"slug": "symbols", "zh": "吉祥象征", "ru": "Символы", "min": 400, "max": 700, "gloss": [15, 25]},
  {"slug": "people", "zh": "历史人物", "ru": "Люди", "min": 600, "max": 1000, "gloss": [15, 25]},
  {"slug": "culture", "zh": "文化艺术", "ru": "Культура и искусство", "min": 600, "max": 1000, "gloss": [15, 25]},
  {"slug": "literature", "zh": "文学经典", "ru": "Классическая литература", "min": 1100, "max": 2500, "gloss": [15, 25]}
]
```

- [ ] **Шаг 1: тесты.** В `test/test_book_lesson.py` хороший урок-фикстура (строкой, пишется во временную папку) и:
  - `test_parses_sample`: у разобранного урока `id`, `block == "myths"`, 4 пункта «判断正误», `tf[1].answer == "错"`, `sources[0].kind == "official"`.
  - `test_good_lesson_has_no_errors`: `validate_lesson(...) == []`.
  - `test_errors`: по одной ошибке на каждую поломку, сообщение содержит ключевое слово — блок не из `blocks.json` → «блок»; `status: done` → «status»; ответ `是` в «判断正误» → «对/错»; 6 пунктов «判断正误» → «判断正误»; 2 вопроса → «回答问题»; 9 слов «生词» → «生词»; текст на 200 иероглифов в `myths` → «длина»; `status: accepted` и все источники `retelling` → «источник»; дата `16.10.2026` → «дата»; имя файла `01-other.md` при `id: myth-x` → «id».
  - `test_gloss_word_inside_longer_word_is_used` (Review Focus 3): «生词» содержит `蟠桃`, в тексте только `{蟠桃园|pántáoyuán}` → ошибки «нет в тексте» нет; `test_gloss_pattern_with_ellipsis_skipped`: `拜……为师` не проверяется на присутствие.
  - `test_count_han_excludes_quote_and_marks`: `count_han(body_text(...))` не считает строку `> 原文：…`, пиньинь из пометок и цифры.

- [ ] **Шаг 2:** `python3 -m unittest test.test_book_lesson -v` → FAIL.

- [ ] **Шаг 3: реализовать `scripts/book_lesson.py`.** Заголовок между строками `---` (`ключ: значение`), основной текст до первого `## `, разделы `## 生词`, `## 判断正误`, `## 回答问题`, `## 来源` — строки `- поле | поле | …`, `## 注` — свободный текст. Длина — по `body_text`. «Лишнее слово в 生词» — слово не встречается подстрокой ни в `body_text`, ни в названии.

- [ ] **Шаг 4:** тест → PASS.

- [ ] **Шаг 5: коммит.** `git commit -m "Книга: формат урока и проверка"`

### Задача 3: уровень языка и расстановка пиньиня

**Files:**
- Create: `scripts/book_level.py`
- Create: `test/test_book_level.py`
- Modify: `book/hsk/extra.tsv`

**Interfaces:**
- Consumes: `Lesson`, `body_text` из задачи 2; `book/hsk/*.tsv` из задачи 1.
- Produces (`book_level.py`):
  - `@dataclass Vocab(level: dict[str, int], pinyin: dict[str, str])`; `load_vocab(hsk_dir: Path = BOOK / "hsk") -> Vocab` (hsk20 + extra)
  - `@dataclass Run(text: str, pinyin: str | None)`
  - `@dataclass Block(kind: str, runs: list[Run] | None = None, items: list[list[Run]] | None = None, text: str = "")` — `kind` ∈ {`p`, `h3`, `quote`, `label`, `examples`}; у `quote` только `text` (без пиньиня)
  - `@dataclass Annotated(lesson: Lesson, blocks: list[Block], errors: list[str], hsk5: list[str], hsk6: list[str])`
  - `annotate(lesson: Lesson, vocab: Vocab) -> Annotated`
  - `POLYPHONES: frozenset[str]` = `frozenset("长行重还得了着调传好干种便藏几朝都为相觉没地乐少只数难教分当应假空背")`

Правила `annotate` — по токенам jieba в порядке чтения; перед разбором в словарь jieba
добавляются (`jieba.add_word`) слова из пометок и из «生词» урока:

```
пометка {w|py}: w уже встречался без пиньиня → ошибка «w: первое появление без пиньиня»;
                первая встреча → Run(w, py); дальше → Run(w, None)
токен = слово «生词»: первая встреча → пиньинь из «生词»; дальше — без
не иероглифы, или уровень ≤ 4, или уже показан → без пиньиня
токен целиком делится (жадно, слева, до 6 знаков) на слова уровня ≤ 4 и уже показанные слова → без пиньиня
уровень 5–6: одиночный иероглиф из POLYPHONES → ошибка «w: многозначный иероглиф, поставьте {w|…}»;
             иначе первая встреча → пиньинь из списка, слово попадает в отчёт hsk5/hsk6
иначе → ошибка «w: нет пиньиня (слово вне HSK)»
```

- [ ] **Шаг 1: тесты** (свой маленький `Vocab` в тесте, без файлов):
  - `test_hsk5_word_gets_pinyin_once`: «温暖…温暖» → первый `Run("温暖","wēnnuǎn")`, второй без пиньиня; `"温暖" in a.hsk5`.
  - `test_unknown_word_is_error`: `心术不正` без пометки → ошибка с «心术不正».
  - `test_inline_mark_after_plain_is_error` (Review Focus 2): «逢蒙来了。{逢蒙|Féng Méng}…» → ошибка «первое появление».
  - `test_polyphone_needs_mark` (Review Focus 1): `朝` уровня 5 отдельным словом → ошибка «многозначный»; `{朝|cháo}` → ошибки нет.
  - `test_decomposable_compound_is_known`: «打不过» при `打`, `不`, `过` уровня 1 → без ошибок и без пиньиня.
  - `test_gloss_word_gets_gloss_pinyin`: слово из «生词» вне HSK получает пиньинь из «生词».
  - `test_quote_is_not_checked`: блок `> 原文：宋人有耕者` → `Block("quote")`, ошибок нет.
  - `test_samples_pass`: три урока `book/src/` (после задачи 6) — `annotate(...).errors == []`; до задачи 6 тест ссылается на `book/samples/src/` и переводится на `book/src/` в задаче 6.

- [ ] **Шаг 2:** `python3 -m unittest test.test_book_level -v` → FAIL.

- [ ] **Шаг 3: реализовать `scripts/book_level.py`.** `jieba.setLogLevel(logging.WARNING)`; `jieba.add_word` между уроками накапливается — для независимости уроков завести `jieba.Tokenizer()` на каждый вызов `annotate`.

- [ ] **Шаг 4:** тесты из шага 1, кроме `test_samples_pass`, → PASS.

- [ ] **Шаг 5: наполнить `extra.tsv`.** Прогнать `annotate` на трёх пробных уроках. Каждую ошибку на слове, которое на самом деле входит в HSK 1–4 (в колодах Anki нет отдельных 说, 们 — только 说话, 我们), внести в `extra.tsv` с причиной («морфема из 我们, HSK 1»). Настоящие пропуски пиньиня в образцах — исправить пометкой в самом уроке. `test_samples_pass` → PASS.

- [ ] **Шаг 6: коммит.** `git commit -m "Книга: уровень HSK и пиньинь по словам (jieba)"`

### Задача 4: команда `book.py check`

**Files:**
- Create: `scripts/book.py`
- Test: `test/test_book_cli.py`

**Interfaces:**
- Consumes: `load_lessons`, `validate_lesson`, `load_blocks` (задача 2); `load_vocab`, `annotate` (задача 3).
- Produces: `book.check(src: Path, hsk_dir: Path) -> tuple[list[str], int]` — строки отчёта и число ошибок; `main(argv)`: `check` → печать отчёта, код 1 при ошибках, иначе 0. Повтор `id` между уроками — ошибка.

Строка отчёта по уроку: `myths/01-myth-change-benyue · draft · 762 (700–1500) · HSK5: 21 · HSK6: 2`,
под ней — ошибки с отступом.

- [ ] **Шаг 1: тесты.** `test_check_reports_errors_and_exit_code`: временная папка `src/myths/` с хорошим и сломанным уроком → `errors == 1`, `main(["check", ...]) == 1`; `test_duplicate_id`: два файла с одним `id` → ошибка «повтор id».
- [ ] **Шаг 2:** → FAIL. **Шаг 3:** реализовать. **Шаг 4:** → PASS.
- [ ] **Шаг 5: коммит.** `git commit -m "Книга: команда проверки"`

### Задача 5: сборка HTML, PDF и EPUB

**Files:**
- Create: `scripts/book_render.py`, `book/style.css`
- Modify: `scripts/book.py` — команда `build [--drafts]`
- Test: `test/test_book_render.py`

**Interfaces:**
- Consumes: `Annotated`, `Block`, `Run` (задача 3); `load_blocks` (задача 2).
- Produces (`book_render.py`):
  - `lesson_xhtml(a: Annotated, block: dict, img_dir: Path, draft_mark: bool) -> str` — фрагмент `<section>`, корректный XML
  - `front_xhtml(blocks, lessons_by_block) -> str` — обложка (`book/img/cover.png`, если есть), оглавление, «как читать» по-русски (что значит пиньинь над словом, где «生词», ключи в конце)
  - `key_xhtml(annotated: list[Annotated]) -> str` — ключи по урокам
  - `book_html(annotated, blocks, drafts: bool) -> str` — целая страница для PDF
  - `write_pdf(html_path: Path, pdf_path: Path) -> None` — Chrome `--headless=new --no-pdf-header-footer --user-data-dir=<tempfile.mkdtemp()>`; путь к Chrome — `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`, иначе `google-chrome` из `PATH`
  - `write_epub(annotated, blocks, out: Path, drafts: bool) -> None` — EPUB 3: `mimetype` первым и без сжатия, `META-INF/container.xml`, `content.opf`, `nav.xhtml`, `front.xhtml`, по файлу на урок, `key.xhtml`, `style.css`, картинки из `book/img/`, если есть
- `book.py build` пишет `book/out/中国文化故事.pdf` и `.epub`; без `--drafts` берёт только `accepted`, с `--drafts` — все, у не принятых на странице пометка «черновик». Перед сборкой — `check`; при ошибках сборка не идёт (код 1).

Вёрстка — как в принятом `book/samples/samples.pdf` (CSS пробного скрипта переносится в
`book/style.css`; `@page` 170 × 227 мм только для PDF). Каждый блок открывается страницей с
названием по-китайски и по-русски. Пиньинь — `<ruby>слово<rt>pīnyīn</rt></ruby>`.

- [ ] **Шаг 1: тесты.**
  - `test_lesson_xhtml_is_wellformed` (Review Focus 5): урок с `&`, `<`, «“”», 《》, «……» в тексте и названии → `xml.etree.ElementTree.fromstring(lesson_xhtml(...))` не падает, текст сохранён.
  - `test_missing_image_gives_placeholder` (Review Focus 4): нет `img/<id>.png` → в выводе класс `img-placeholder` и имя файла; есть файл → `<img src="img/<id>.png"`.
  - `test_ruby_rendered`: `Run("温暖","wēnnuǎn")` → `<ruby>温暖<rt>wēnnuǎn</rt></ruby>`.
  - `test_epub_structure`: `write_epub` на двух уроках → первый элемент архива `mimetype` со `ZIP_STORED` и содержимым `application/epub+zip`; в `content.opf` оба урока в `spine`; каждый `.xhtml` разбирается как XML.
  - `test_build_skips_drafts`: урок `draft` без `--drafts` в книжку не попадает, с `--drafts` попадает с пометкой «черновик».
  - `test_pdf_smoke` (`skipUnless` Chrome найден): PDF создан, начинается с `%PDF`.
- [ ] **Шаг 2:** → FAIL. **Шаг 3:** реализовать. **Шаг 4:** → PASS; полный прогон `python3 -m unittest discover -s test -t .` и `node --test test/*.test.mjs` — зелёные.
- [ ] **Шаг 5: коммит.** `git commit -m "Книга: сборка в PDF и EPUB"`

### Задача 6: пробные уроки — в итоговый формат, правила проекта

**Files:**
- Create: `book/src/myths/09-myth-change-benyue.md`, `book/src/chengyu/01-chengyu-shouzhudaitu.md`, `book/src/literature/01-lit-xiyouji.md` (перенос из `book/samples/src/`)
- Delete: `book/samples/`
- Create: `book/README.md` — как устроен урок, команды `check`/`build`, порядок «писатель → проверка уровня → проверяющий → автор»
- Modify: `CLAUDE.md` — пункт о книжке; `CHANGELOG.md`

Номера файлов в блоке — по порядку содержания из описания (嫦娥奔月 — девятый в «Мифах»).

- [ ] **Шаг 1: перенос.** `block:` → слаг, `status: draft`, раздел `## 来源`: у 嫦娥奔月 — источники строк `fig-change`, `story-change-benyue` из `data/dossiers/myths.json` (как есть, `kind` по полю `authority`) плюс пересказ с Фэн Мэном (`retelling`); у 守株待兔 и 西游记 — найти и записать источники (официальные/академические на опорные факты: «韩非子·五蠹», 吴承恩 и первое издание 1592 г., 一百回, 十四年). В уроке о Чанъэ упомянуть У Гана и нефритового зайца в «注» (олимпиадные вопросы, «по возможности»).
- [ ] **Шаг 2:** `test_samples_pass` переведён на `book/src/`; `python3 scripts/book.py check` → код 0.
- [ ] **Шаг 3:** `python3 scripts/book.py build --drafts` → открыть `book/out/中国文化故事.pdf`, сверить вид с принятым пробным PDF.
- [ ] **Шаг 4: правила.** В `CLAUDE.md` — пункт: «Книга для чтения — `book/`, спецификация `docs/superpowers/specs/2026-10-16-culture-reader-design.md`; уроки правятся в `book/src/`, проверка `python3 scripts/book.py check`; в книжку идут только `status: accepted`, принятые автором после проверки отдельным агентом». Запись в `CHANGELOG.md`.
- [ ] **Шаг 5: коммит.** `git commit -m "Книга: пробные уроки в итоговом формате, правила"`

### Задача 7: блок «Мифы о начале мира»

**Files:**
- Create: `book/src/myths/01-myth-pangu-kaitian.md` … `13-myth-cangjie-zaozi.md` (12 новых, 嫦娥奔月 уже есть)

Порядок и id: 01 `myth-pangu-kaitian` 盘古开天, 02 `myth-nuwa-zaoren` 女娲造人, 03 `myth-nuwa-butian` 女娲补天,
04 `myth-fuxi` 伏羲, 05 `myth-shennong` 神农尝百草, 06 `myth-huangdi-chiyou` 黄帝战蚩尤,
07 `myth-gonggong` 共工怒触不周山, 08 `myth-houyi-sheri` 后羿射日, 09 `myth-change-benyue` 嫦娥奔月,
10 `myth-kuafu-zhuri` 夸父逐日, 11 `myth-jingwei-tianhai` 精卫填海, 12 `myth-dayu-zhishui` 大禹治水,
13 `myth-cangjie-zaozi` 仓颉造字.

- [ ] **Шаг 1: спросить автора** о запуске: три агента-писателя по 4 урока, потом проверяющие (не больше трёх одновременно). Без согласия — писать самому.
- [ ] **Шаг 2: писатели.** Каждому — описание, `book/README.md`, образец 嫦娥奔月, строки досье `data/dossiers/myths.json` по его урокам, олимпиадные вопросы банка по теме (`grep` по `data/bank.json`), требование: `python3 scripts/book.py check` без ошибок по своим файлам, `status: draft`, все источники в `## 来源`. Пересечения: 后羿射日 подробно о солнцах, 嫦娥奔月 — только напоминание; 女娲造人 и 女娲补天 — разные эпизоды.
- [ ] **Шаг 3: проверяющие** (отдельные агенты, не писавшие эти уроки): каждый опорный факт сверен с источником урока; подробности есть хотя бы в одном пересказе; язык — HSK 4+ с грамматикой HSK 4–5; задания по тексту, ключи верны; текст не пересказывает близко вырезку «Легенты, идиомы, люди.pdf» или чужие сайты; цитаты — по правилу описания. Отчёт — список правок по урокам.
- [ ] **Шаг 4:** правки внесены, `status: checked`, `book.py check` → 0; `book.py build --drafts`; запись в `CHANGELOG.md`; коммит `Книга: блок «Мифы о начале мира» (черновик)`.
- [ ] **Шаг 5: автор читает блок.** Отправить PDF. Принятые автором уроки → `status: accepted`, коммит. Отзыв автора о языке и длине — в `book/README.md`, чтобы следующие блоки его учитывали.

### Задача 8: остальные блоки — тем же порядком

Не входит в этот план как отдельные шаги: после отзыва автора на «Мифы» каждый следующий блок
(сказания → чэнъюй → праздники → символы → люди → культура → литература) идёт по шагам
задачи 7, с теми же правилами и согласием автора на запуск агентов. Перед слиянием
`feat/culture-reader` в `master` — спросить автора, нужно ли ревью.
