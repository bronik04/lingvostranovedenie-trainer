# Ревью первой партии — 2026-11-07

Это первоначальное ревью20 до авторского просмотра. Текущий выпуск сокращён до15 после четырёх снятий, двух правок формулировок и исключения одного смыслового дубля; итоговые решения — в `2026-11-07-regional-batch-1-dedup-review.md` и `2026-11-07-regional-batch-1-author-decisions.json`.

Отдельный проверяющий изучил текущие 20 вопросов и все 80 кандидатов по подписям, не отмеченных как повтор той же строки. Блокирующих замечаний нет; содержательные правки не требуются. Ниже сохранён полный отчёт проверяющего.

# Read-only review — regional release batch 1

Verdict: the selected 20 can be released with their existing question texts, answers, option pools, explanations, glossary cells, factRow and factGroup unchanged. No necessary content correction or replacement found. This verdict concerns consistency/readiness of these conserved questions, not a new source audit.

## Blocking findings

None. No selected ID needs correction before release on the evidence reviewed. Existing author acceptance was checked against the current bank and current option pools, not used as the sole justification.

## Checked constraints

- All 20 exist in the canonical bank, have verified answers, accepted embed definitions with reviewer notes dated 2026-10-25, answer glosses, and glosses for every incorrect option. All option texts within each selected pool are unique; pools have 5–34 choices.
- 2016-17-mun-spb-3: current pool is Guangzhou plus precisely Beijing/Tianjin/Shanghai/Chongqing. The negative premise remains unambiguous; the necessary excludes survive. Do not remove those excludes when returning it.
- 2024-25-shk-mosobl-8: Chengdu and Xi’an remain excluded, as the original check specifically required; no newly introduced competing financial-centre answer found in the pool.
- 2025-26-mun-ryaz-4: the river-only filter and exclusions of Ussuri and Tumen survive; canal distractors are absent.
- 2018-19-mun-vrn-6: accepted correction “вторая по длине” and 中国第二长河 is present. The previously reported “вторая по величине” ambiguity is already resolved.
- 2025-26-shk-mosobl-4 / 2025-26-shk-mosobl-14: 华山/恒山, 陕西/山西 and the distinct 衡山/湖南 distractor remain distinguishable; no second answer found in the actual current pools.
- The Russian city pools retain only one fitting answer for Moscow, Yakutsk and Blagoveshchensk. The Olympic host-city pool does not introduce Zhangjiakou. The Suzhou item retains its accepted city pool; nothing in the conserved data establishes a second correct answer.
- Existing fact groups remain present where required by the accepted earlier review (Olympics, Suzhou/Hangzhou, river/province names, Blagoveshchensk border etc.). The scoped scan reports zero cross-text errors.

## Triage of 174 glossary candidates

The 94 row-marked cases are permitted same-row repetition. I read the 80 non-row records against the actual target wording. They do not justify edits or blanket fact-group merging:

- Original option IDs o1–o4 obscure the table-row identity from the automatic scan. Hengshan/Hunan, Hengshan/Shanxi, Taishan/Shandong, Irtysh/Xinjiang, capital/province pairs, St Petersburg’s nickname and Vladimir’s Golden Ring membership are the same table facts already allowed by CLAUDE.md.
- The linked-table/olympiad repetitions remain legitimate: province and city capitals (including Nanjing/Chengdu), municipality status, Vladivostok/Sea of Japan, Hong Kong/1997, Luoyang/Henan, Shenzhen/1980 SEZ. These should retain their useful gloss facts. Linking every question whose distractor mentions a city into a giant geography group would suppress unrelated learning facts.
- nature-q03/q23 → nature-q47: “Тайшань, Восточный пик пяти священных гор” does not supply the requested title “глава пяти гор”. The common phrase “пять священных гор” is an overbroad clue match. Keep the gloss.
- nature-q05/q18/q22 → 2016-17-shk-7: Suzhou Creek’s being a tributary of Huangpu in Shanghai does not state Pudong’s position east of Huangpu or explain the name Pudong. “Шанхай” alone is an overbroad clue. Keep the Suzhou Creek gloss.
- provinces-q92 → provinces-q03: Taiyuan being Shanxi’s administrative centre is the same province/city association and does not establish the target’s Yellow River boundary, coal industry or launch-centre facts; no new leak requiring a group.
- provinces-q110 → nature-q142/provinces-q90: the Hunan/Dongting relationship is the same geographic fact in the linked province/lake material; its explanatory relationship is precisely the kind of informative glossary content the project preserves. No deletion of “к югу от Дунтинху” is warranted.
- Other partial clue matches (city’s province vs detailed ancient-capital history; Shenzhen’s foundation year vs border with Hong Kong) are either permitted repetition of that city fact or do not actually state the target’s discriminating fact.

## Scope / not judged

Read CLAUDE.md, the selected bank records, their accepted dossier definitions/check notes, relevant original decisions in data/review/regions-dossier-check.md, and all 80 non-row entries in the supplied scoped glossary report. Checked only these conserved 20 and the directly referenced neighbour records; did not re-audit the 103 variants/1032 raw source tasks, re-research sources, or inspect the other 283 conserved regional questions. No product edits. Browser rendering, visibility-filter implementation, deployment and runtime round scheduling were not exercised; the release implementer should run the existing scoped/build checks after the visibility change.
