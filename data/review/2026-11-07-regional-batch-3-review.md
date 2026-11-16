# Independent content review — regional batch 3

Reviewed 2026-11-07. Scope: the 20 selected draft items and their 80 captions in `data/review/2026-11-07-regional-batch-3-proposals.json`, against `CLAUDE.md`, `docs/superpowers/plans/2026-11-07-regional-batch-3-review.md`, `/tmp/lingvo-batch3-active.json` (998), and `/tmp/lingvo-batch3-pending.json` (263). This is a read-only content review for author approval, not release approval. Original 103 variants/PDFs and all 263 candidate meanings were not re-audited.

## Verdict

**Ready for AUTHOR REVIEW, with minor draft corrections below. Not approved for release or publication.** No P0/P1/P2 learner-facing factual error, wrong key, unmarked Chinese option change, or direct/reverse semantic duplicate was found in the selected twenty. All 80 captions were read individually; all correct-answer captions add information beyond the question plus answer. The four stem changes, currency option correction, and three explanation changes remain proposals requiring the author's decision.

## Findings

### P3 — stale currency warning contradicts the actual preview

Path: `data/review/2026-11-07-regional-batch-3-proposals.json`, item `2021-22-mun-omsk-9`, `warnings[0]`, option `o4`.

The warning says the Chinese preview is preserved verbatim, but the preview correctly contains the separately proposed `元（人民币）`, replacing original `元人民币`. The original remains in the snapshot and proposal. This is not a key/content defect; it can mislead the author about which text is being accepted. Replace the warning with: «В предпросмотре предложена редактура 元（人民币）; исходное 元人民币 сохранено отдельно. До публикации требуется решение автора». The parent has acknowledged this correction.

### P3 — align the eastern-region caption with its statistical source

Path: the same JSON, item `2019-20-mun-lip-1`, option `o4`, `ru`.

The caption says «в статистике входят в Восточный Китай». Its NBS source describes `东部地区`, the eastern economic/statistical region, rather than the conventional macroregion `华东` often translated as «Восточный Китай». All three provinces are in both groups, so the answer is unaffected. Still, the distinction matters educationally: the NBS region additionally includes Beijing, Tianjin, Hebei, Guangdong and Hainan. Suggested caption: «Шаньдун, Цзянсу, Чжэцзян — входят в восточный экономический регион Китая». Supported by the already retained [NBS list](https://www.stats.gov.cn/hd/lyzx/zxgk/202302/t20230215_1905339.html).

### P3 — distinguish accepted media reuse from primary government provenance

Affected JSON paths:

- `2024-25-mun-kem-4/options[o1]/source`: Guizhou location and Guiyang capital, `about.china.com.cn`.
- `2025-26-shk-mosobl-13/options[o2]/source`: Guangzhou as capital, `ydyl.china.com.cn`.
- `2025-26-shk-mosobl-13/supportingCaptionSources/o1`, `/o3`, `/o4`: Guiyang, Lanzhou, Xi'an respectively, again China.org.cn pages.

These are accurately disclosed as reuse of previously accepted dossier quotes, with old dates retained. The factual captions are sound. However, `authority: official` must not be described in the author-facing methodology as proof of primary provincial/municipal authorship: China.org.cn is a media publication, and the inspected Guizhou article identifies its source as China.org.cn itself. This is provenance precision, not grounds to reject the questions. Either explicitly label the reused source as accepted state-media material, or replace/supplement it with government originals. Parent has elected to strengthen the sources.

Fresh indexed primary replacements verified during this review:

- Guangzhou planning authority, [城市性质](https://ghzyj.gz.gov.cn/hdjl/ywzsk/gtkjgh/content/post_9902845.html), 2024-09-30, source 总体规划处; quote: «广州市是广东省省会».
- Guizhou territorial spatial plan, [国家投资项目在线审批监管平台](https://new.tzxm.gov.cn/zckd/fzgh/202408/t20240815_1392396.shtml), 2024-08-15; quote: «交汇于省会贵阳，显著提升了贵州省西南内陆交通枢纽地位».
- Lanzhou municipal historical gazetteer, [兰州市建置区划志](https://www.gsdfszw.org.cn/gssz_58/dyl_69/lzs_224/dyjjzqhz/201707/P020170705359528515080.pdf); indexed quote: «兰州市是甘肃省省会». This was an indexed-passage verification, not a full PDF inspection.

Broader provenance spot checks did not blindly equate hosting domains with authorship. The Guangzhou subway piece is authored by Li Yan, a researcher at the Guangzhou Academy of Social Sciences, and hosted in that institution's research output section; the academic label is reasonable. RUC's Jiaozhou Bay article is a historical-geographical study drawing on maps/treaties, not merely an unrelated newspaper repost. The Lermontov caption is transparently reused from a literary article in 文艺报 on the Chinese Writers Association site. Institutional religious education pages are institutional explanatory references, not peer-reviewed research; no stronger claim of scholarly peer review should be added.

## Content and semantic assessment

All twenty tested relations were compared with their cited active neighbors, plus targeted searches of the active snapshot for corresponding entities, answers, direct relations, and reversals. The twenty selected relations were also compared against one another. No unresolved near-duplicate remains among the selected twenty. Similar answer/entity alone was not treated as a duplicate.

The four geography items pass substantively:

- `2019-20-mun-lip-1`: the three northeastern provinces are Heilongjiang, Liaoning and Jilin. Capital cities in `o2` are correctly ordered Harbin, Shenyang, Changchun; supporting sources cover all three. Existing provincial-capital questions are different tested relations. Their answers in the caption create future hint-group work, not a duplicate.
- `2024-25-mun-kem-4`: Guizhou is uniquely landlocked among Guizhou, Liaoning, Fujian and Shandong. All captions are accurate; correct `o1` adds region and capital. Active Guizhou questions about batik, abbreviation, Miao population and FAST location test distinct facts.
- `2025-26-shk-mosobl-13`: Guangdong is the sole non-neighbor of Sichuan among these four. The fresh Sichuan water-plan quote supports Guizhou, Gansu and Shaanxi adjacency. The complete Guangdong list independently excludes Sichuan. The flawed 2004 embassy quote is explicitly excluded and is not being reused for boundary claims. Correct caption adds Guangdong's location and capital; current questions about Guangdong cuisine, economic zones and abbreviation are distinct.
- `2023-24-mun-spb-8`: the proposed cross-language toponym wording preserves Port Arthur → 旅顺 and avoids implying a present independent city or recent renaming. The district/location caption is accurate, with official district education material. The active Russo-Japanese War question tests the war's dates, not this name equivalence.

Other notable distinctions checked: Ming wall sections versus Qin unification of early walls; Guangdong embroidery versus Suzhou technique and Chengdu's Shu embroidery; modern currency versus central bank and banknote images; 紫 in 紫禁城 versus present palace name; specific Li Bai poem authorship versus his other poems and nickname; war initiator versus Nanjing Treaty/cession/year; 三教 membership versus individual schools and 五大宗教 membership; Gao Xingjian 2000 versus Mo Yan 2012.

The Opium War item's existing treaty question already names Britain, and its new correct caption names the treaty. This is a hint relationship, not the same tested relation. Similarly, captions about capital cities, poems/authors, festival dates, Mao-era space milestones and Mo Yan can reveal answers elsewhere. Such links need the later fact-group/hint review if the author accepts the cards. This draft does not need those operational groups implemented.

All four stem proposals improve precision without changing the intended answer. Ziwei as a celestial region, five main religions without a blanket legal-recognition claim, and the 2002 maglev ceremony distinction are appropriate explanation proposals. The maglev stem appropriately retains no year. The `省` option in the RF subject-types item is the actual tested word and must remain. Wrong lists in the Three Teachings and northeastern-province questions are translated as lists and are not falsely certified as correct groupings.

## Mechanical verification and scope boundaries

An independent Python comparison against the pending snapshot confirmed 20 existing question IDs, preserved full original stems and answer keys, four existing option IDs each, one marked correct each, and no displayed Chinese changes other than the explicit currency `o4` proposal. Maximum caption length: 84 characters. No city/province suffixes were added.

All 45 files in `/tmp/lingvo-batch3-protected.json` matched their SHA-256 snapshots during this review. No product, repository, index or HEAD mutations were made by this reviewer. The only written artifact is this report. Full application regression tests were deliberately not run for this separate data draft.

## Declined to judge

Empty. The judgment covers all selected twenty items and eighty captions. This does not imply a fresh web re-fetch of every reused accepted dossier citation, a full semantic audit of the 263 unselected candidates, a re-audit of original exam PDFs, or release authorization.

## Поправки координатора после вычитки

- Оговорка №4 теперь прямо сообщает о предложении 元（人民币） в предпросмотре и сохранённом исходнике 元人民币.
- В №1 подпись D уточнена до «восточного экономического региона Китая», соответствующего источнику NBS 东部地区.
- Для Гуйяна, Гуанчжоу и Сианя добавлены проверенные первичные правительственные источники. Принятая справка о Ланьчжоу из 中国网 явно названа переизданием официального информационного портала, а не новым первоисточником правительства. Студенческий факт о столице не менялся.
- Действующие файлы банка/сайта/досье не менялись; все исправления относятся только к материалам просмотра.
