# JP-Bench roadmap (1000 items)

Each item is one commit-sized task. `[x]` means it is on `main`; `[ ]` means planned.

## P1. Schema and loader (1–100)
1. [x] task: skip files prefixed with underscore as templates
2. [x] task: surface YAML parse errors with file name and line number
3. [x] schema: require task ids to be lowercase kebab-case
4. [x] schema: require file name to equal task id (already enforced; add test for mismatch message)
5. [x] schema: reject unknown top-level keys with a clear list
6. [x] schema: reject unknown keys inside `safety`
7. [x] schema: reject unknown keys inside `portal`
8. [ ] schema: require `portal.url` host to end in `.go.jp` or `.or.jp` for official portals
9. [x] schema: require `gold_source` to be non-empty
10. [x] schema: require `title_ja` to contain at least one Japanese character
11. [x] schema: require `instructions_ja` to contain at least one Japanese character
12. [x] schema: require `instructions_en` to contain no Japanese characters
13. [ ] schema: reject empty `inputs` for tasks whose category is `lookup`
14. [x] schema: require `success.fields` to be unique
15. [x] schema: reject `min_overlap` outside 0–1
16. [x] schema: reject negative `tolerance`
17. [x] schema: require `tolerance` only for `numeric_tolerance`
18. [x] schema: require `state` only for `reached_state`
19. [ ] schema: require `fields` to reference keys that exist in gold answers
20. [x] loader: expose `load_task_ids` without parsing bodies
21. [ ] loader: cache parsed tasks per directory for one run
22. [ ] loader: report all validation errors instead of stopping at the first
23. [x] loader: support nested task directories (`tasks/<category>/`)
24. [x] loader: ignore hidden files starting with `.`
25. [x] loader: reject symlinks that point outside the task directory
26. [x] loader: enforce UTF-8 and reject BOM-prefixed files with a message
27. [x] loader: reject tabs in YAML indentation with the line number
28. [x] schema: add `version` field to task files (start at 1)
29. [x] schema: reject task files whose `version` is newer than the loader supports
30. [x] schema: add `deprecated` flag and hide deprecated tasks from `list` by default
31. [x] schema: add `replaced_by` pointing to a valid task id
32. [x] schema: reject `replaced_by` cycles
33. [x] schema: add `created` and `updated` dates (ISO 8601)
34. [x] schema: reject `updated` earlier than `created`
35. [x] schema: add `owner` field for the person responsible for gold answers
36. [x] schema: add `review_status` (draft, reviewed, published)
37. [ ] schema: only `published` tasks may appear in the leaderboard set
38. [x] schema: reject tasks with `review_status: published` but no `gold_source`
39. [ ] task model: add `Success.weights` for weighted field scoring
40. [x] task model: add `Task.tags` as a sorted tuple
41. [x] task model: add `Task.source_documents` list (URLs of official pages)
42. [x] task model: add `Task.snapshot_date` (date the gold was fetched)
43. [ ] task model: make `Task` hashable for use in sets
44. [x] task model: add `Task.to_dict` for JSON export
45. [x] task model: add `Task.from_dict` as the public constructor
46. [x] task model: provide `__repr__` that omits instructions
47. [x] loader: fail when two files declare the same `title_en`
48. [ ] loader: warn when a task has no `title_ja`
49. [ ] loader: count tasks per category on load (for `validate` output)
50. [ ] loader: count tasks per difficulty on load
51. [x] validate: print a per-category summary line
52. [x] validate: print a per-difficulty summary line
53. [x] validate: exit non-zero when any task is `deprecated` without `replaced_by`
54. [ ] validate: add `--strict` to treat warnings as errors
55. [x] validate: add `--json` for machine-readable output
56. [x] validate: check that every `form_fill` task has a `reached_state` success rule
57. [x] validate: check that every `reached_state` task defines `state`
58. [x] validate: check that `inputs` values are strings, numbers, or lists only
59. [x] validate: reject inputs that look like real personal data (phone-number pattern)
60. [ ] validate: reject inputs that look like real corporate numbers unless marked `fictional: true`
61. [x] validate: check that `safety.auth_required` tasks declare `auth_method`
62. [x] schema: add `auth_method` enum (none, idpw, gbizid)
63. [x] schema: reject `auth_method` set when `auth_required` is false
64. [x] task model: expose `requires_login` property
65. [x] task model: expose `is_form_fill` property
66. [x] task model: expose `is_read_only` property
67. [x] schema: add `max_steps` budget per task (integer, 1–200)
68. [x] schema: reject `max_steps` below 1
69. [x] schema: add `timeout_seconds` per task
70. [x] schema: reject `timeout_seconds` above 1800
71. [x] schema: add `allowed_domains` list for browser agents
72. [x] schema: require `allowed_domains` to include the portal host
73. [x] schema: reject `allowed_domains` entries containing paths
74. [ ] schema: add `expected_pages` count (informational)
75. [x] loader: detect and report duplicate `title_ja` across tasks
76. [ ] loader: detect tasks whose `portal.url` is not reachable in the offline snapshot list
77. [ ] tests: fixture with each validation error type, one test per message
78. [ ] tests: fixture directory with nested categories
79. [ ] tests: loader ignores hidden files
80. [ ] tests: loader rejects BOM files
81. [ ] tests: loader rejects tab indentation
82. [ ] tests: validate `--json` output parses as JSON
83. [ ] tests: validate `--strict` promotes warnings
84. [ ] tests: deprecated tasks hidden from `list`
85. [ ] tests: `replaced_by` cycle detection
86. [ ] docs: task YAML field reference generated from the schema constants
87. [ ] docs: list every error code emitted by validate
88. [ ] docs: explain `review_status` lifecycle
89. [ ] docs: explain `allowed_domains` and why it exists
90. [ ] docs: explain `max_steps` and `timeout_seconds` budgets
91. [ ] refactor: move validation rules into one table
92. [ ] refactor: give each validation rule an error code (JPB001…)
93. [ ] refactor: separate `parse_task` from `validate_task`
94. [ ] refactor: split `task.py` into `model.py` and `loader.py`
95. [ ] refactor: type-annotate `load_tasks` return as `list[Task]` everywhere
96. [ ] perf: avoid re-reading YAML when `validate` and `list` run in one process
97. [ ] perf: parallel file reads for large task sets (>200 files)
98. [ ] tests: benchmark loader on 1000 synthetic task files
99. [ ] release: bump schema version to 2 once `version` field lands
100. [ ] release: write schema migration note from version 1 to 2

## P2. Normalization (101–220)
101. [x] normalize: strip zero-width characters
102. [x] normalize: unify wave dash and tilde variants
103. [x] normalize: map full-width colon `：` and semicolon `；` to ASCII
104. [x] normalize: map full-width parentheses to ASCII
105. [x] normalize: map full-width percent `％` to ASCII
106. [x] normalize: map full-width hyphen-minus `－` to ASCII (already via dash table; add test)
107. [ ] normalize: map `ー` (katakana long vowel) variants `｜` and `―` consistently
108. [ ] normalize: map ideographic full stop `。` and `．` to one form for comparison
109. [x] normalize: map `・` (middle dot) variants `･` and `·`
110. [ ] normalize: map `ヶ` and `ケ` only when option `kana_fold` is on
111. [x] normalize: optional hiragana/katakana folding for comparison (`kana_fold`)
112. [x] normalize: map small kana (ぁぃぅぇぉ) to large forms when `kana_fold` is on
113. [x] normalize: fold `ゐ`/`ゑ` to `い`/`え` when `kana_fold` is on
114. [x] normalize: unify `〒` postal mark removal for address fields
115. [x] normalize: strip postal code hyphen for `postal_code` fields
116. [x] normalize: format `postal_code` as `NNN-NNNN`
117. [x] normalize: parse `＋81` and `+81` phone prefixes to `+81`
118. [x] normalize: strip phone separators (`-`, `(`, `)`, spaces) for `phone` fields
119. [x] normalize: validate phone digit count (10 or 11 domestic)
120. [x] normalize: map `株式会社` ↔ `(株)` ↔ `㈱` (already); add `合名会社` and `合資会社`
121. [x] normalize: map `一般社団法人` and `(一社)` variants
122. [x] normalize: map `一般財団法人` and `(一財)` variants
123. [ ] normalize: map `特定非営利活動法人` and `(NPO)` variants
124. [ ] normalize: map `独立行政法人` variants
125. [ ] normalize: map `有限責任` prefix variants
126. [ ] normalize: strip `本店` and `支店` suffixes for name fields when `strip_branch` is on
127. [ ] normalize: map `代表取締役` titles out of name fields
128. [x] normalize: map kanji numerals `一二三` to digits in address blocks (`一丁目`→`1丁目`)
129. [x] normalize: map `丁目` and `-` variants in address fields
130. [ ] normalize: map `番地` and `番` variants
131. [ ] normalize: map `号` and `号室` variants in address fields
132. [x] normalize: map prefecture omission (`東京`→`東京都`) for address fields
133. [ ] normalize: map `北海道` (no 府/県/都 suffix) correctly
134. [x] normalize: map `京都府` and `大阪府` variants `京都` and `大阪`
135. [ ] normalize: map 政令指定都市 wards (`千代田区`) with and without city name
136. [x] normalize: strip `〒` and postal code from address fields
137. [x] normalize: date: accept `R9.4.1` abbreviation for 令和
138. [x] normalize: date: accept `H31.4.30` abbreviation for 平成
139. [x] normalize: date: accept `S64.1.7` abbreviation for 昭和
140. [ ] normalize: date: accept `元号` with `元年` in all eras
141. [x] normalize: date: reject 平成 dates after 2019-04-30 with a clear error
142. [x] normalize: date: reject 令和 year 0
143. [ ] normalize: date: accept 西暦 forms with `年` and `/` mixed
144. [ ] normalize: date: accept two-digit years only with `allow_short_year` flag
145. [x] normalize: date: reject impossible dates (2027-02-30)
146. [x] normalize: date: handle leap years (2028-02-29 valid, 2027-02-29 invalid)
147. [x] normalize: date: accept `YYYY年MM月DD日` with leading zeros
148. [x] normalize: date: accept `YYYY年M月D日` without leading zeros
149. [ ] normalize: date: normalize time-of-day suffix (`午前`/`午後`) out of date fields
150. [ ] normalize: date: return `None` for empty values instead of `""`
151. [x] normalize: number: accept `¥` and `￥` prefixes
152. [x] normalize: number: accept `円`, `万円`, `億円` (scale 1e4, 1e8)
153. [ ] normalize: number: reject mixed scale without explicit unit
154. [x] normalize: number: accept full-width comma `，` as separator
155. [ ] normalize: number: accept `％` suffix as value/100 for ratio fields
156. [ ] normalize: number: accept `千` (thousand) with kanji numerals for small values
157. [x] normalize: number: reject NaN and infinity
158. [ ] normalize: number: return `Decimal` option for money fields
159. [ ] normalize: number: round money to whole yen when `integer_yen` is on
160. [x] normalize: number: accept `約`, `およそ` prefix and mark as approximate
161. [ ] normalize: number: accept `以上`, `以下` and keep bound direction
162. [ ] normalize: number: accept ranges `100〜200` and return (low, high)
163. [x] normalize: number: accept `無料` as 0
164. [ ] normalize: number: accept `なし` as 0 for count fields only
165. [x] normalize: legal number (法人番号) strip spaces and hyphens
166. [x] normalize: invoice number (T+13) uppercase `T` and strip spaces
167. [x] normalize: invoice number accept lowercase `t` prefix
168. [x] normalize: invoice number reject non-digit body
169. [x] normalize: law number (`令和元年法律第一号`) to canonical form
170. [x] normalize: law number accept `法律第1号` without era
171. [ ] normalize: law number accept `政令第` and `省令第` kinds
172. [ ] normalize: article reference: `第3条第1項第2号` canonical ordering
173. [x] normalize: article reference: accept `第三条` (kanji numerals)
174. [x] normalize: article reference: accept `3条` without 第
175. [x] normalize: article reference: `第3条の2の3` multi-level suffix
176. [ ] normalize: article reference: `附則第3条` supplementary provisions
177. [ ] normalize: article reference: `第3条ただし書` proviso
178. [ ] normalize: article reference: `第3条各号` list reference
179. [x] normalize: URL: remove `utm_*` query parameters
180. [x] normalize: URL: sort query parameters
181. [x] normalize: URL: decode percent-encoded Japanese in path
182. [x] normalize: URL: map `http` to `https` for `.go.jp` hosts
183. [x] normalize: URL: strip default ports `:443`
184. [x] normalize: URL: strip `www.` prefix for comparison
185. [x] normalize: list fields: normalize each element then sort
186. [x] normalize: list fields: drop empty elements
187. [x] normalize: list fields: dedupe after normalization
188. [ ] normalize: boolean fields: accept `はい`/`いいえ`, `有効`/`無効`, `true`/`false`
189. [ ] normalize: boolean fields: map `有` and `無` for existence questions
190. [ ] normalize: enum fields: accept Japanese labels and map to codes
191. [ ] normalize: enum fields: fail on unknown labels with the list of valid ones
192. [ ] normalize: text fields: collapse repeated punctuation (`。。` → `。`)
193. [ ] normalize: text fields: remove trailing full stop for comparison
194. [ ] normalize: text fields: remove emoji
195. [ ] normalize: text fields: normalize Unicode dash `—` and `―` (already partial)
196. [ ] normalize: text fields: keep original text in a sidecar for debugging
197. [ ] normalize: expose `normalize_pipeline(name)` with named steps
198. [ ] normalize: make pipeline steps individually testable
199. [ ] normalize: document order of steps and why it matters
200. [ ] normalize: add `explain(value)` that lists which rules changed the value
201. [ ] normalize: fuzz-test idempotency with 1000 random Japanese strings
202. [ ] normalize: fuzz-test that normalization never raises on arbitrary Unicode
203. [ ] normalize: golden test file of 200 notation variants with expected outputs
204. [ ] normalize: golden test for dates across era boundaries
205. [ ] normalize: golden test for address variants
206. [ ] normalize: golden test for corporate-name variants
207. [ ] normalize: performance: compile all regexes once at import
208. [ ] normalize: performance: avoid NFKC on pure-ASCII input
209. [ ] normalize: performance: cache entity-suffix replacement table
210. [ ] normalize: API: expose `normalize_field` with explicit kind argument
211. [ ] normalize: API: remove implicit kind detection by field-name suffix
212. [ ] normalize: docs: table of notation variants and the rule that covers each
213. [ ] normalize: docs: explain what is deliberately NOT normalized (e.g. 0 vs O)
214. [ ] normalize: examples file for scorer plugin authors
215. [ ] normalize: add `kana_fold` and `strip_branch` to a documented options dataclass
216. [ ] normalize: validate options dataclass combinations
217. [ ] normalize: test that default options are conservative (no folding)
218. [ ] normalize: changelog entry for every rule added
219. [ ] normalize: rule priority table in docs
220. [ ] normalize: deprecate `normalize_text` whitespace removal for name fields (keep for compare)

## P3. Scoring (221–370)
221. [x] scoring: add exact-match baseline via field_match
222. [x] scoring: add scorer registry keyed by success type
223. [x] scoring: fail loudly when a task type has no registered scorer
224. [x] scoring: treat empty model output as no prediction
225. [x] scoring: return a per-field breakdown dict on TaskResult
226. [x] scoring: add `details` field (list of per-field results) to TaskResult
227. [x] scoring: make TaskResult JSON-serialisable via `to_dict`
228. [x] scoring: add `confidence` float to TaskResult (default 1.0)
229. [ ] scoring: field_match: report which field failed first in `detail`
230. [ ] scoring: field_match: support per-field `weights` from success.weights
231. [ ] scoring: field_match: weighted score = sum(weights of hits) / sum(weights)
232. [x] scoring: field_match: treat missing keys as mismatch, not KeyError
233. [x] scoring: field_match: treat `null` prediction as empty string
234. [x] scoring: field_match: option `partial_credit` (default true)
235. [x] scoring: field_match: option `all_or_nothing` for regulated fields
236. [x] scoring: numeric_tolerance: support absolute tolerance option
237. [x] scoring: numeric_tolerance: support relative tolerance option (already present; document)
238. [x] scoring: numeric_tolerance: reject tolerance above 0.5 at load time
239. [x] scoring: numeric_tolerance: handle zero gold value with absolute tolerance
240. [x] scoring: numeric_tolerance: report signed difference in detail
241. [ ] scoring: numeric_tolerance: accept string predictions with units via normalize_number
242. [x] scoring: numeric_tolerance: flag predictions that are NaN as failures
243. [x] scoring: set_overlap: report counts (tp, fp, fn) in detail
244. [x] scoring: set_overlap: use normalized elements for matching
245. [x] scoring: set_overlap: allow order-insensitive duplicates by set semantics (document)
246. [x] scoring: set_overlap: empty prediction with non-empty gold scores 0
247. [x] scoring: set_overlap: empty gold and empty prediction scores 1
248. [x] scoring: set_overlap: treat predictions containing non-list as failure
249. [ ] scoring: set_overlap: support `min_overlap` separately for precision and recall
250. [ ] scoring: set_overlap: export F1 as the score (already); add test for F1 bounds
251. [ ] scoring: reached_state: compare state after normalize_text
252. [x] scoring: reached_state: require `entered` values for all gold fields
253. [x] scoring: reached_state: report which entered field was wrong
254. [x] scoring: reached_state: treat `submitted` missing as false
255. [x] scoring: reached_state: treat `submitted` as string "true" only when clearly boolean
256. [x] scoring: reached_state: safety violation takes precedence over other failures (already); test ordering
257. [ ] scoring: reached_state: record whether the agent stopped before the confirmation screen
258. [ ] scoring: reached_state: allow multiple acceptable target states
259. [x] scoring: add `date_range` success type for period questions
260. [x] scoring: date_range: compare start and end dates separately
261. [x] scoring: date_range: accept open-ended ranges (end = 無期限)
262. [x] scoring: add `enum` success type with label-to-code mapping
263. [x] scoring: enum: fail on unknown label with the valid list
264. [x] scoring: add `boolean` success type for yes/no questions
265. [x] scoring: boolean: normalize はい/いいえ/有/無
266. [x] scoring: add `url_match` success type using normalize_url
267. [x] scoring: add `article_match` success type using normalize_article_ref
268. [x] scoring: add `law_number_match` success type
269. [ ] scoring: add `corporate_number_match` success type with check digit validation
270. [ ] scoring: corporate number check digit: implement official algorithm with test vectors from NTA docs
271. [ ] scoring: corporate number check digit: reject malformed length before checking digit
272. [ ] scoring: add `invoice_number_match` success type (T + 13 digits)
273. [ ] scoring: invoice number: check that body is 13 digits
274. [ ] scoring: invoice number: note that registration status is not derivable from the number
275. [x] scoring: add `postal_code_match` success type
276. [x] scoring: add `phone_match` success type
277. [ ] scoring: add `amount_yen_match` success type with integer yen comparison
278. [ ] scoring: add `ratio_match` success type (percent in, fraction compare)
279. [ ] scoring: add `count_match` success type (integers only)
280. [ ] scoring: add `free_text_match` with normalized containment (opt-in)
281. [ ] scoring: free_text_match: require all keywords from `keywords` list
282. [ ] scoring: free_text_match: report missing keywords in detail
283. [ ] scoring: add `json_schema_match` for nested answers
284. [ ] scoring: json_schema_match: validate predicted object against schema before comparing
285. [ ] scoring: json_schema_match: report JSON path of each mismatch
286. [ ] scoring: json_schema_match: support arrays of objects with keyed matching (`key: id`)
287. [ ] scoring: json_schema_match: ignore extra keys in prediction (option)
288. [x] scoring: add `multi_answer` success type (several acceptable gold values)
289. [x] scoring: multi_answer: pass if any acceptable gold matches
290. [x] scoring: multi_answer: record which gold option matched
291. [x] scoring: add `abstain` success type for questions with no answer
292. [x] scoring: abstain: score 1 when prediction is explicitly `not_found`
293. [x] scoring: abstain: score 0 when prediction invents a value
294. [ ] scoring: add `penalty` for guessing on abstain tasks
295. [ ] scoring: add calibration check (confidence vs correctness) for abstain tasks
296. [ ] scoring: aggregate: macro average across tasks
297. [ ] scoring: aggregate: micro average across fields
298. [ ] scoring: aggregate: report standard error via bootstrap (seeded)
299. [ ] scoring: aggregate: report 95% confidence interval for pass rate
300. [ ] scoring: aggregate: report per-category pass rate
301. [ ] scoring: aggregate: report per-difficulty pass rate (done in report)
302. [ ] scoring: aggregate: report safety violation count separately
303. [ ] scoring: aggregate: fail the run if any safety violation occurs
304. [ ] scoring: aggregate: exclude tasks with no gold from denominator (explicit)
305. [ ] scoring: aggregate: list tasks skipped for missing gold
306. [ ] scoring: plugin: scorer registration via decorator
307. [ ] scoring: plugin: reject scorers that overwrite built-in types
308. [ ] scoring: plugin: wrap scorer exceptions into TaskResult with detail
309. [ ] scoring: plugin: time-limit custom scorers (default 2s)
310. [ ] scoring: plugin: document contract with a worked example
311. [ ] scoring: tests: golden file of 100 prediction/gold pairs with expected results
312. [ ] scoring: tests: property test that perfect prediction always passes
313. [ ] scoring: tests: property test that empty prediction never passes (except abstain)
314. [ ] scoring: tests: property test that score is within [0,1]
315. [ ] scoring: tests: safety violation always fails regardless of fields
316. [ ] scoring: tests: field order does not change score
317. [ ] scoring: tests: weights normalise to 1
318. [ ] scoring: tests: numeric tolerance boundary (exactly at tolerance passes)
319. [ ] scoring: tests: set overlap boundary (exactly min_overlap passes)
320. [ ] scoring: tests: corporate number check digit test vectors
321. [ ] scoring: tests: invoice number format test vectors
322. [ ] scoring: tests: date_range open-ended behaviour
323. [ ] scoring: tests: abstain penalty arithmetic
324. [ ] scoring: tests: multi_answer records matched option
325. [ ] scoring: tests: json_schema_match path reporting
326. [ ] scoring: performance: score 10k predictions under 2 seconds
327. [ ] scoring: performance: avoid recomputing normalized gold per run
328. [ ] scoring: CLI: `score --by-category` output
329. [ ] scoring: CLI: `score --format json`
330. [ ] scoring: CLI: `score --fail-under <rate>` exit code
331. [ ] scoring: CLI: `score --only <task-id>` filter
332. [ ] scoring: CLI: `score --verbose` prints per-field details
333. [ ] scoring: CLI: `score` warns on predictions for unknown tasks
334. [ ] scoring: CLI: `score` warns on gold entries with no prediction
335. [ ] scoring: CLI: `score` rejects non-object prediction files
336. [ ] scoring: CLI: `score` supports JSON Lines input
337. [ ] scoring: CLI: `score` reads predictions from stdin with `-`
338. [ ] scoring: docs: scoring methodology page with formulas
339. [ ] scoring: docs: table of success types and when to use each
340. [ ] scoring: docs: explain why safety violation zeroes the score
341. [ ] scoring: docs: explain abstain and why guessing is penalised
342. [ ] scoring: docs: example predictions for each success type
343. [ ] scoring: refactor: move each scorer to its own module under `scorers/`
344. [ ] scoring: refactor: give scorers a common base result builder
345. [ ] scoring: refactor: remove duplicated gold lookup code in scorers
346. [ ] scoring: refactor: type-annotate every scorer signature
347. [ ] scoring: refactor: make scorer functions pure (no mutation of gold)
348. [ ] scoring: fix: reached_state fields check compares normalized values twice
349. [ ] scoring: fix: set_overlap division when precision and recall are both zero
350. [ ] scoring: fix: numeric_tolerance uses max(|g|,1) which hides small values
351. [ ] scoring: decision: document why numeric tolerance is relative with floor 1
352. [ ] scoring: decision: document why safety precedence is absolute
353. [ ] scoring: decision: document why empty gold set scores 1 only when prediction is empty
354. [ ] scoring: observability: count scorer calls per type in run metadata
355. [ ] scoring: observability: time each scorer call
356. [ ] scoring: observability: emit scorer warnings to stderr only in verbose mode
357. [ ] scoring: safety: reject predictions that include a `submitted` true for any non-form task
358. [ ] scoring: safety: record submitted attempts even when the field is missing
359. [ ] scoring: safety: flag predictions that include credentials-like strings
360. [ ] scoring: safety: redact entered values containing personal-looking data in reports
361. [ ] scoring: safety: never echo entered values in SAFETY VIOLATION detail
362. [ ] scoring: compat: keep `score_all` signature stable
363. [ ] scoring: compat: keep `TaskResult` field order stable
364. [ ] scoring: release: note scoring changes in the changelog with version
365. [ ] scoring: release: publish a scoring spec document (versioned)
366. [ ] scoring: release: freeze gold-answer scoring rules for v1.0
367. [ ] scoring: review: second reviewer signs off on each success type
368. [ ] scoring: review: check every success type against three real portal pages
369. [ ] scoring: review: retire `free_text_match` if it causes false positives in pilot
370. [ ] scoring: review: summarize scoring decisions for the paper appendix

## P4. Prompts and parsing (371–470)
371. [x] prompt: render task instructions in Japanese or English
372. [x] prompt: record a stable hash of each rendered prompt
373. [x] prompt: reject prompts over a length limit
374. [x] parse: extract JSON answers and detect refusals in model output
375. [x] prompt: add `--lang` option to `prompt` command (exists; add test for ja output)
376. [ ] prompt: add system prompt slot in template
377. [x] prompt: add a stricter output-format footer for JSON-only answers
378. [x] prompt: add explicit instruction to stop before submit on form tasks (already present; test it)
379. [ ] prompt: include today's date placeholder for deadline questions
380. [ ] prompt: include the portal's operating hours note when relevant
381. [x] prompt: escape `{` and `}` in inputs so JSON dumps cannot break templates
382. [x] prompt: include an explicit "not found" option for abstain-capable tasks
383. [x] prompt: add few-shot examples file per task (optional)
384. [x] prompt: load few-shot examples from `examples/<task>.yaml`
385. [x] prompt: cap number of few-shot examples at 3
386. [x] prompt: validate few-shot example answers against the task schema
387. [x] prompt: render few-shot examples in the same language as the prompt
388. [x] prompt: add prompt template version to the rendered header
389. [x] prompt: store template version in run metadata
390. [x] prompt: add `prompt --diff` to compare ja and en renderings
391. [x] prompt: add `prompt --json` to emit the prompt as a JSON object
392. [x] prompt: add `prompt --write <dir>` to save all prompts to files
393. [x] prompt: name saved prompt files by task id and language
394. [x] prompt: add a checksum manifest for saved prompts
395. [x] prompt: test that saved prompts match the manifest
396. [x] prompt: remove trailing whitespace in rendered output
397. [x] prompt: normalize line endings to LF
398. [x] prompt: test that rendering is byte-stable across platforms
399. [ ] prompt: docs: how the safety line is inserted and why
400. [ ] prompt: docs: list template placeholders
401. [x] parse: strip `<thinking>` blocks (exists as `think|thinking`); add `<reasoning>` tag
402. [ ] parse: handle JSON with trailing commas by reporting a precise error
403. [ ] parse: handle single-quoted JSON-like output with an explicit error
404. [ ] parse: accept the first valid object when several appear (document)
405. [x] parse: report the position of the failing character in JSON errors
406. [x] parse: strip leading `Answer:` or `回答:` labels
407. [x] parse: strip trailing explanations after the closing brace
408. [x] parse: handle full-width braces `｛｝` by mapping to ASCII before parsing
409. [x] parse: handle full-width quotes `＂` in JSON
410. [x] parse: limit input size to 200 kB before parsing
411. [x] parse: reject NaN and Infinity in JSON
412. [x] parse: reject duplicate keys in the top-level object
413. [x] parse: keep the raw output in an error object for debugging
414. [x] parse: add `ParseError` class with `raw` attribute
415. [x] parse: refusal patterns: add Japanese phrases for "cannot access the page"
416. [x] parse: refusal patterns: add English phrases for "I don't have access"
417. [x] parse: refusal detection returns the matched phrase
418. [x] parse: refusal detection is case-insensitive for English patterns
419. [ ] parse: refusal detection ignores quoted text in the answer
420. [x] parse: add `answer_kind` (json, refusal, empty, invalid) classification
421. [ ] parse: count each answer kind per run for the report
422. [x] parse: tests for each answer kind
423. [x] parse: tests for full-width braces
424. [x] parse: tests for oversize input
425. [x] parse: tests for duplicate keys
426. [ ] parse: fuzz test that extract_json never raises anything but ParseError
427. [ ] parse: fuzz test with random bracket sequences
428. [ ] parse: performance test on 1 MB output
429. [ ] parse: docs: decision table for answer kinds
430. [ ] parse: docs: examples of accepted and rejected outputs
431. [ ] prompt+parse: round-trip test (render, fake answer, parse, score) for each task
432. [ ] prompt+parse: golden outputs for 5 tasks in both languages
433. [x] prompt+parse: check that every task's expected JSON keys appear in the prompt
434. [ ] prompt+parse: check that prompts never leak gold answers (test with gold values)
435. [ ] prompt+parse: check that prompts never include `gold_source` URLs with API keys
436. [x] prompt+parse: check that inputs in prompt match task inputs exactly
437. [ ] prompt+parse: check for accidental Japanese in English prompts (allowlist for names)
438. [x] prompt+parse: check for accidental English in Japanese prompts (allowlist)
439. [x] prompt+parse: check prompt length for every task under the limit
440. [x] prompt+parse: check that every task has both languages non-empty
441. [x] prompt+parse: check output format line matches success type
442. [ ] prompt+parse: reached_state tasks get the entered/state format line
443. [ ] prompt+parse: field_match tasks get a keyed JSON line
444. [ ] prompt+parse: set_overlap tasks get an array format line
445. [ ] prompt+parse: numeric tasks say to output numbers without units
446. [ ] prompt+parse: date tasks say to output ISO 8601
447. [ ] prompt+parse: date tasks mention Japanese era years are allowed
448. [ ] prompt+parse: boolean tasks say to output true or false
449. [ ] prompt+parse: abstain tasks say to output not_found
450. [ ] prompt+parse: include a sample answer line for each success type
451. [ ] prompt+parse: tests that sample answers score 1.0 on their own task
452. [ ] prompt+parse: refuse to render a task whose success type has no format line
453. [ ] prompt+parse: version the format lines together with the scorer spec
454. [ ] prompt+parse: document the mapping from success type to format line
455. [ ] prompt+parse: CLI `prompt --check` validates every task renders
456. [ ] prompt+parse: CLI `prompt --check` exits non-zero on any failure
457. [ ] prompt+parse: CI runs `prompt --check`
458. [ ] prompt+parse: CI uploads rendered prompts as an artifact
459. [ ] prompt+parse: CI diff: fail when rendered prompt changes without a version bump
460. [ ] prompt+parse: release: publish prompt set with the version tag
461. [ ] prompt+parse: review: native speaker checks each Japanese prompt
462. [ ] prompt+parse: review: English prompts checked for clarity by a second person
463. [ ] prompt+parse: review: remove ambiguous phrases found in pilot runs
464. [ ] prompt+parse: review: keep prompts identical across models (no per-model tuning in v1)
465. [ ] prompt+parse: decision: document why prompts are kept minimal
466. [ ] prompt+parse: decision: document why the safety line is not optional
467. [ ] prompt+parse: decision: document why answers must be JSON only
468. [ ] prompt+parse: observability: log prompt hash at the start of each run
469. [ ] prompt+parse: observability: store the parse error count per run
470. [ ] prompt+parse: cleanup: remove the unused `json` import if no longer needed

## P5. Adapters and runner (471–600)
471. [x] runner: add model adapter interface and offline FixedAdapter
472. [x] runner: add `EchoAdapter` that returns the prompt for debugging
473. [x] runner: add `ErrorAdapter` that always raises (for error-path tests)
474. [x] runner: add `RecordingAdapter` that stores prompts in memory
475. [x] runner: add `ReplayAdapter` that reads outputs from a JSONL file
476. [x] runner: ReplayAdapter fails when a prompt hash is missing
477. [x] runner: add `run_suite(adapter, tasks)` returning per-task results
478. [x] runner: run_suite records the prompt hash for each task
479. [x] runner: run_suite records the raw output for each task
480. [x] runner: run_suite records parse error kind for each task
481. [x] runner: run_suite continues after one task fails
482. [x] runner: run_suite stops early when `--fail-fast` is set
483. [x] runner: run_suite respects the task `timeout_seconds`
484. [x] runner: timeouts produce a TIMEOUT result, not an exception
485. [ ] runner: add `max_steps` to the adapter call metadata
486. [ ] runner: add token counting hook (no provider lookup)
487. [x] runner: add cost estimation hook using a price table file
488. [x] runner: price table file is validated at load
489. [x] runner: add `--dry-run` that renders prompts and skips adapters
490. [x] runner: add `--limit N` to run only the first N tasks
491. [x] runner: add `--seed` for deterministic task order
492. [x] runner: add `--repeat K` to run each task K times
493. [x] runner: compute pass@1 and pass@K when repeat > 1
494. [x] runner: write results as JSON Lines to `results/<run-id>.jsonl`
495. [x] runner: run id derived from timestamp and adapter name
496. [x] runner: write run metadata file alongside results
497. [x] runner: metadata includes jpbench version, prompt hashes, and adapter name
498. [x] runner: metadata includes Python version and platform
499. [x] runner: metadata never includes API keys (test with fake key in env)
500. [x] runner: resume an interrupted run from the last complete line
501. [x] runner: detect a half-written last line and drop it safely
502. [ ] runner: lock the results file while writing (fcntl, POSIX only)
503. [x] runner: write results atomically using a temp file and rename
504. [x] runner: exit code 2 when some tasks errored
505. [x] runner: exit code 3 when a safety violation occurred
506. [x] runner: print a summary table at the end
507. [x] runner: print progress as `[n/N] task-id`
508. [x] runner: suppress progress with `--quiet`
509. [ ] runner: colour output only when stdout is a TTY
510. [ ] runner: respect NO_COLOR environment variable
511. [x] runner: retry transient adapter errors up to 2 times
512. [x] runner: do not retry parse errors
513. [ ] runner: back off exponentially with jitter (seeded in tests)
514. [ ] runner: cap total retry time per task
515. [x] runner: record retry count per task
516. [x] runner: concurrency flag `--jobs N` (default 1)
517. [x] runner: concurrency keeps result order stable
518. [x] runner: concurrency test with 20 fake tasks
519. [x] runner: HTTP adapter base class with timeout and JSON body helpers (no network in tests)
520. [x] runner: HTTP adapter: test with a local stub server
521. [x] runner: OpenAI-compatible adapter (base URL and model from env, no key in code)
522. [x] runner: Anthropic Messages adapter (base URL and model from env, no key in code)
523. [x] runner: adapter reads API key from environment only
524. [x] runner: adapter refuses to start if key is missing (clear message)
525. [x] runner: adapter refuses to send requests to non-https hosts
526. [x] runner: adapter strips the key from exception messages
527. [x] runner: local subprocess adapter runs a command with the prompt on stdin
528. [x] runner: subprocess adapter enforces timeout and kills the process
529. [x] runner: subprocess adapter captures stderr separately
530. [x] runner: subprocess adapter rejects commands that are not on an allowlist
531. [ ] runner: browser agent adapter stub (interface only, documented)
532. [ ] runner: browser agent adapter records each navigation as a step
533. [ ] runner: browser agent adapter records screenshots path per step (no image upload)
534. [ ] runner: browser agent adapter enforces `allowed_domains`
535. [ ] runner: browser agent adapter blocks navigation outside `allowed_domains`
536. [ ] runner: browser agent adapter stops at `max_steps`
537. [ ] runner: browser agent adapter stops at the confirmation screen for form tasks
538. [ ] runner: trace file per task (JSON Lines of steps)
539. [ ] runner: trace file never contains entered personal data (redaction hook)
540. [ ] runner: trace file size cap per task
541. [ ] runner: summarize traces into per-step counts
542. [ ] runner: test tracing with a scripted fake browser adapter
543. [ ] runner: test that browser adapter respects allowed_domains
544. [ ] runner: test that browser adapter respects max_steps
545. [ ] runner: test that browser adapter stops before submit
546. [ ] runner: docs: how to write a new adapter
547. [ ] runner: docs: adapter contract and error types
548. [ ] runner: docs: how replay works for offline reproduction
549. [ ] runner: docs: cost and token accounting rules
550. [ ] runner: docs: why keys never go in files
551. [ ] runner: security: scan repo for accidental key-like strings in CI
552. [ ] runner: security: .gitignore covers results with traces containing sensitive data
553. [ ] runner: security: document how to rotate keys after a leak
554. [ ] runner: observability: log adapter latency histogram in metadata
555. [ ] runner: observability: log token totals per run
556. [ ] runner: observability: log retry totals per run
557. [ ] runner: observability: log timeout totals per run
558. [ ] runner: observability: log error kinds per run
559. [ ] runner: compare two runs (`jpbench diff run-a run-b`)
560. [ ] runner: diff shows tasks that changed pass/fail status
561. [ ] runner: diff exits non-zero when a previously passing task now fails
562. [ ] runner: diff reports score deltas per category
563. [ ] runner: archive old results older than N days (dry-run first)
564. [ ] runner: archive command never deletes without `--yes`
565. [ ] runner: export a run as a single JSON document
566. [ ] runner: import a run exported from another machine
567. [ ] runner: validate imported run against schema version
568. [ ] runner: reject imported run with unknown schema version
569. [ ] runner: test resume after simulated crash mid-run
570. [ ] runner: test atomic write under simulated failure
571. [ ] runner: test concurrency with failing tasks
572. [ ] runner: test timeout with a sleeping subprocess
573. [ ] runner: test retry counts with a flaky fake adapter
574. [x] runner: test cost estimation with a fixed price table
575. [x] runner: test price table validation errors
576. [ ] runner: test dry-run makes zero adapter calls
577. [ ] runner: test replay fails on missing hash
578. [ ] runner: test replay produces identical scores to the original run
579. [ ] runner: test that metadata contains no secrets (fake env key)
580. [ ] runner: test that `--limit` and `--seed` are reproducible
581. [ ] runner: performance: run 200 fake tasks in under 5 seconds
582. [ ] runner: performance: avoid re-parsing task YAML per task
583. [ ] runner: performance: stream results instead of keeping them all in memory
584. [ ] runner: refactor: separate scheduling from execution
585. [ ] runner: refactor: separate result writing from scoring
586. [ ] runner: refactor: make adapters stateless where possible
587. [ ] runner: refactor: move retry logic into one decorator
588. [ ] runner: refactor: type-annotate result dataclasses
589. [ ] runner: compat: keep `FixedAdapter` constructor unchanged
590. [ ] runner: compat: keep `run_task` signature unchanged
591. [ ] runner: release: publish a sample run (replay of the fixed answers) in `examples/`
592. [ ] runner: release: note adapter support matrix in README
593. [ ] runner: review: security review of the HTTP adapters
594. [ ] runner: review: check that subprocess allowlist is empty by default
595. [ ] runner: review: check that browser adapter never submits
596. [ ] runner: review: check that trace redaction covers all entered fields
597. [ ] runner: decision: document why retries never apply to parse errors
598. [ ] runner: decision: document why concurrency defaults to 1
599. [ ] runner: decision: document why replay is the default for CI
600. [ ] runner: decision: document the run id format

## P6. CLI and reporting (601–700)
601. [x] cli: add `--version` reading version from package metadata
602. [x] cli: add `show <task-id>` to print a task summary
603. [x] cli: add `list --category` and `list --difficulty` filters
604. [x] cli: add `report` subcommand with per-difficulty summary
605. [x] cli: add `report --format csv`
606. [x] cli: add `list --json` output
607. [x] cli: add `list --tag <tag>` filter (depends on task tags, item 40)
608. [x] cli: add `list --sort id|difficulty|category`
609. [ ] cli: add `list --columns` to choose output columns
610. [x] cli: add `show --json`
611. [x] cli: add `show --prompt` shortcut that renders the English prompt
612. [x] cli: add `show --gold-source` to print the gold source line
613. [ ] cli: add `validate --fix-hints` to print suggested fixes
614. [x] cli: add `validate --only <file>` for a single task file
615. [x] cli: add `doctor` command checking Python, package, and task directory
616. [ ] cli: add `doctor` check that pytest is installed for contributors
617. [x] cli: add `doctor` check that ruff is installed (optional)
618. [x] cli: add `doctor` check that the task directory is writable for results
619. [ ] cli: add `config` command that prints effective settings
620. [ ] cli: config reads `jpbench.toml` from the current directory
621. [ ] cli: config validates keys in `jpbench.toml`
622. [ ] cli: config rejects unknown sections with a clear message
623. [ ] cli: environment variable overrides for config values
624. [ ] cli: `--no-color` flag
625. [ ] cli: `--log-level` flag with debug, info, warning, error
626. [x] cli: log to stderr, output to stdout (audit all commands)
627. [x] cli: exit code table in `--help` epilog
628. [x] cli: exit code 0 on success, 1 on user error, 2 on partial failure
629. [ ] cli: friendly error for unknown subcommand with suggestion
630. [ ] cli: friendly error for missing file arguments
631. [x] cli: friendly error for unreadable JSON with line number
632. [x] cli: `score` reports file path in error messages
633. [x] cli: shell completion script for bash (`jpbench completion bash`)
634. [x] cli: shell completion script for zsh
635. [ ] cli: shell completion script for fish
636. [ ] cli: man page generated from argparse help
637. [x] cli: `--help` lists examples for each subcommand
638. [ ] cli: `jpbench help <topic>` for scoring and safety topics
639. [ ] cli: keep argparse help text in sync with docs (test)
640. [x] cli: test every subcommand's `--help` exits 0
641. [ ] cli: test that unknown global option fails with exit code 1
642. [x] cli: test `show` output format is stable (golden)
643. [x] cli: test `list` output format is stable (golden)
644. [x] cli: test `report` Markdown output format is stable (golden)
645. [x] cli: test `report` CSV has the documented header
646. [x] cli: test `score` against a fixed fixture set
647. [x] report: add per-category table to Markdown report
648. [x] report: add per-success-type table to Markdown report
649. [x] report: add safety section listing any violations
650. [ ] report: add abstain section listing not_found answers
651. [ ] report: add parse error section listing raw output lengths (not contents)
652. [ ] report: add run metadata section (prompt hashes, version)
653. [x] report: add confidence interval for pass rate
654. [ ] report: add bar chart as ASCII in terminal output
655. [ ] report: add `--title` flag for the report heading
656. [x] report: add `--output` flag to write the report to a file
657. [x] report: refuse to overwrite an existing report without `--force`
658. [x] report: HTML output format with the same content
659. [x] report: HTML output escapes all values
660. [x] report: HTML output has no external scripts or fonts
661. [x] report: JSON output format for dashboards
662. [x] report: JSON output includes schema version
663. [ ] report: compare two runs side by side (Markdown table)
664. [ ] report: highlight tasks that regressed between runs
665. [ ] report: highlight tasks that improved between runs
666. [ ] report: sort report rows by score ascending to surface failures
667. [ ] report: include task titles (Japanese and English) in rows
668. [ ] report: include portal name in rows
669. [ ] report: include gold source in an appendix
670. [ ] report: include jpbench version and date in footer
671. [x] report: test golden output for an empty run
672. [x] report: test golden output for a run where all tasks fail
673. [x] report: test golden output for a run where all tasks pass
674. [ ] report: test that report handles unicode titles
675. [x] report: test that report escapes pipe characters in Markdown cells
676. [x] report: test that CSV quotes fields containing commas
677. [x] report: test that HTML escapes angle brackets
678. [ ] report: performance: render report for 1000 rows under 1 second
679. [ ] leaderboard: local leaderboard file (`leaderboard.json`) format
680. [ ] leaderboard: add entry from a run with `jpbench leaderboard add`
681. [ ] leaderboard: refuse entries without run metadata
682. [ ] leaderboard: refuse entries with a dry-run flag
683. [ ] leaderboard: refuse entries with safety violations
684. [ ] leaderboard: sort entries by pass rate then mean score
685. [ ] leaderboard: break ties by lower cost
686. [ ] leaderboard: show model name, version, and date
687. [ ] leaderboard: show number of tasks evaluated
688. [ ] leaderboard: show holdout score separately (when available)
689. [ ] leaderboard: `leaderboard show --markdown`
690. [ ] leaderboard: `leaderboard show --json`
691. [ ] leaderboard: validate `leaderboard.json` against its schema in CI
692. [ ] leaderboard: test that duplicate entries are rejected
693. [ ] leaderboard: test sort order with ties
694. [ ] leaderboard: test markdown rendering
695. [ ] leaderboard: docs: how to submit a result
696. [ ] leaderboard: docs: what a valid run looks like
697. [ ] leaderboard: docs: how holdout results are withheld
698. [ ] leaderboard: docs: policy for re-running and superseding entries
699. [ ] leaderboard: docs: policy for disputed results
700. [ ] leaderboard: docs: model card requirements for submitters

## P7. Bundled task content (701–860)
701. [x] task content: houjin-bangou-lookup, egov-law-article, egov-36kyotei-fill, jgrants-open-subsidies, invoice-number-verify present (v0.1)
702. [ ] task content: houjin-bangou-lookup: add gold for 10 sample corporate numbers (fictional and public)
703. [ ] task content: houjin-bangou-lookup: add case for a corporation with a branch-style name
704. [ ] task content: houjin-bangou-lookup: add case for a name with full-width digits
705. [ ] task content: houjin-bangou-lookup: add case for a closed corporation
706. [ ] task content: houjin-bangou-lookup: add case for a name change within the last year
707. [ ] task content: houjin-bangou-lookup: add case for a name with 特定非営利活動法人 prefix
708. [ ] task content: houjin-bangou-lookup: add case for a 一般社団法人
709. [ ] task content: houjin-bangou-lookup: add case for a 独立行政法人
710. [ ] task content: houjin-bangou-lookup: add distractor with near-identical name
711. [ ] task content: houjin-bangou-lookup: document data source and licence
712. [ ] task content: invoice-number-verify: add registered and unregistered cases
713. [ ] task content: invoice-number-verify: add revoked-registration case
714. [ ] task content: invoice-number-verify: add malformed number case (wrong length)
715. [ ] task content: invoice-number-verify: add lowercase `t` prefix case
716. [ ] task content: invoice-number-verify: add case for a 個人事業者 registrant
717. [ ] task content: invoice-number-verify: add case for a registration effective in the future
718. [ ] task content: invoice-number-verify: document that gold requires the API application ID
719. [ ] task content: egov-law-article: add Civil Code article lookup
720. [ ] task content: egov-law-article: add Labor Standards Act article lookup
721. [ ] task content: egov-law-article: add paragraph-level question
722. [ ] task content: egov-law-article: add item-level (号) question
723. [ ] task content: egov-law-article: add 之 suffix article (第N条の2)
724. [ ] task content: egov-law-article: add supplementary provision question (附則)
725. [ ] task content: egov-law-article: add amended-law version question
726. [ ] task content: egov-law-article: add question about a repealed article
727. [ ] task content: egov-law-article: add question with kanji numeral article number
728. [ ] task content: egov-law-article: add question on proviso (ただし書)
729. [ ] task content: egov-law-article: document gold source and snapshot date
730. [ ] task content: egov-36kyotei-fill: add optional overtime section case
731. [ ] task content: egov-36kyotei-fill: add case with two agreement periods
732. [ ] task content: egov-36kyotei-fill: add numeric limit field case
733. [ ] task content: egov-36kyotei-fill: add date field validation case
734. [ ] task content: egov-36kyotei-fill: add case where agent must not submit (safety)
735. [ ] task content: egov-36kyotei-fill: add distractor form with similar title
736. [ ] task content: egov-36kyotei-fill: add fictional company data file
737. [ ] task content: egov-36kyotei-fill: document why all data is fictional
738. [ ] task content: jgrants-open-subsidies: add deadline extraction question
739. [ ] task content: jgrants-open-subsidies: add eligibility list question
740. [ ] task content: jgrants-open-subsidies: add amount ceiling question
741. [ ] task content: jgrants-open-subsidies: add application status question
742. [ ] task content: jgrants-open-subsidies: add ministry filter question
743. [ ] task content: jgrants-open-subsidies: add prefecture filter question
744. [ ] task content: jgrants-open-subsidies: add closed-call distractor
745. [ ] task content: jgrants-open-subsidies: document snapshot date handling
746. [ ] task content: new family: tax filing lookup (国税庁 タックスアンサー) read-only
747. [ ] task content: new family: tax filing lookup: consumption tax rate question
748. [ ] task content: new family: tax filing lookup: withholding deadline question
749. [ ] task content: new family: 社会保険 lookup (日本年金機構) read-only
750. [ ] task content: new family: 社会保険 lookup: standard monthly remuneration table question
751. [ ] task content: new family: 登記情報 lookup (法務局) read-only summary (no paid fetch)
752. [ ] task content: new family: 登記 lookup: question on registered address field
753. [ ] task content: new family: e-Stat lookup for a published population figure
754. [ ] task content: new family: e-Stat lookup: numeric tolerance case
755. [ ] task content: new family: 官報 search for a notice title
756. [ ] task content: new family: 官報 search: set overlap case
757. [ ] task content: new family: municipal page lookup (one city, read-only)
758. [ ] task content: new family: municipal lookup: opening hours of a service counter
759. [ ] task content: new family: municipal lookup: fee schedule question
760. [ ] task content: new family: form_fill for a municipal address-change notice (stop before submit)
761. [ ] task content: new family: form_fill: fictional applicant data file
762. [ ] task content: new family: form_fill: reached_state rule with confirmation screen
763. [ ] task content: new family: form_fill: safety violation test case
764. [ ] task content: new family: download task: fetch official PDF and report its title (no file kept)
765. [ ] task content: new family: download task: verify PDF page count against gold
766. [ ] task content: new family: download task: checksum comparison
767. [ ] task content: difficulty calibration: run each task with 3 reference answers
768. [ ] task content: difficulty calibration: set difficulty from observed pass rate bands
769. [ ] task content: difficulty calibration: document band thresholds
770. [ ] task content: ambiguity review: flag questions with more than one correct reading
771. [ ] task content: ambiguity review: rewrite flagged instructions in both languages
772. [ ] task content: ambiguity review: add an answer note for each rewritten task
773. [ ] task content: annotation: second annotator checks 20 gold answers
774. [ ] task content: annotation: record disagreement and resolution
775. [ ] task content: annotation: compute agreement rate per task family
776. [ ] task content: annotation: publish annotation guidelines
777. [ ] task content: source snapshots: store checksum of each fetched source page
778. [ ] task content: source snapshots: store fetch date per source
779. [ ] task content: source snapshots: script to refresh snapshots (manual trigger only)
780. [ ] task content: source snapshots: detect drift and list stale tasks
781. [ ] task content: source snapshots: never store personal data from official pages
782. [ ] task content: holdout: split each family into dev and holdout
783. [ ] task content: holdout: mark holdout tasks and exclude them from prompt tuning
784. [ ] task content: holdout: publish holdout IDs only as a hash list
785. [ ] task content: distractors: add a near-duplicate page to two tasks
786. [ ] task content: distractors: add an outdated page to two tasks
787. [ ] task content: distractors: document distractor design rules
788. [ ] task content: licence: record licence of each source (PDL, public domain, terms)
789. [ ] task content: licence: block tasks whose source licence is unknown
790. [ ] task content: licence: attribution line generated from task metadata
791. [ ] task content: licence: README table of sources and licences
792. [x] task content: tags: add `domain` tag (corporate, tax, legal, subsidy, labor)
793. [ ] task content: tags: add `needs_login` tag
794. [ ] task content: tags: add `multi_page` tag
795. [ ] task content: tags: add `japanese_era` tag for dates in era notation
796. [ ] task content: tags: add `full_width_input` tag
797. [x] task content: tags: validate tags against an allowed list
798. [ ] task content: tags: list tasks by tag in README
799. [ ] task content: budgets: set max_steps for every task
800. [ ] task content: budgets: set timeout_seconds for every task
801. [ ] task content: budgets: review budgets after pilot runs
802. [ ] task content: allowed_domains: set for every task
803. [ ] task content: allowed_domains: test that each task's portal host is allowed
804. [ ] task content: allowed_domains: list external domains that may appear in redirects
805. [x] task content: review_status: mark each task draft, reviewed, or published
806. [ ] task content: review_status: publish only reviewed tasks in v0.2
807. [ ] task content: owner: fill owner for each task
808. [x] task content: created and updated dates for each task
809. [x] task content: source documents list for each task
810. [ ] task content: snapshot_date for each task
811. [ ] task content: examples: one worked example per family in `examples/`
812. [ ] task content: examples: examples are never used as gold
813. [ ] task content: examples: examples checked by the validator
814. [ ] task content: pilot: run the full set with a human baseline (one person)
815. [ ] task content: pilot: record time per task for the human baseline
816. [ ] task content: pilot: record failure reasons for the human baseline
817. [ ] task content: pilot: publish human baseline in the report
818. [ ] task content: pilot: remove tasks that no human can finish in budget
819. [ ] task content: pilot: adjust budgets from the human baseline
820. [ ] task content: pilot: check distractors actually mislead the pilot agent
821. [ ] task content: fictional data: company names use the 株式会社サンプル prefix
822. [ ] task content: fictional data: personal names use obviously fictional names
823. [ ] task content: fictional data: addresses use reserved fictional ranges
824. [ ] task content: fictional data: phone numbers use reserved fictional ranges
825. [ ] task content: fictional data: validator rejects inputs matching real-looking personal data
826. [ ] task content: fictional data: document the fictional data policy
827. [ ] task content: regression: lock gold for every v0.2 task in a fixture file
828. [ ] task content: regression: detect gold changes between versions
829. [ ] task content: regression: require a changelog entry for any gold change
830. [ ] task content: regression: require a version bump for any gold change
831. [ ] task content: family README for each category
832. [ ] task content: family README lists sources and snapshot dates
833. [ ] task content: family README lists known limitations
834. [ ] task content: family README lists tasks by difficulty
835. [ ] task content: family README links to the scoring rule used
836. [x] task content: ensure no task requires paid services
837. [ ] task content: ensure no task requires an account the benchmark cannot provide
838. [x] task content: ensure no task needs CAPTCHA solving (skip and document)
839. [x] task content: ensure no task asks the agent to bypass login
840. [x] task content: ensure every task that needs login says so in `auth_method`
841. [ ] task content: reading-order check: instructions match the portal's actual screen order
842. [ ] task content: link check: portal URLs resolve (manual, recorded)
843. [ ] task content: link check: flag URLs that redirect to a different host
844. [ ] task content: spell check Japanese instructions with a dictionary file
845. [ ] task content: spell check English instructions
846. [x] task content: style guide for instructions (short sentences, no jargon without gloss)
847. [ ] task content: style guide: use です/ます in Japanese instructions
848. [ ] task content: style guide: use imperative in English instructions
849. [x] task content: style guide: state the output format in the last line
850. [x] task content: style guide: avoid "please" in English instructions
851. [ ] task content: release: tag task set v0.2
852. [ ] task content: release: write task-set changelog
853. [ ] task content: release: publish task manifest with checksums
854. [ ] task content: release: verify manifest in CI
855. [ ] task content: release: deprecate v0.1 task IDs that changed meaning
856. [ ] task content: release: map old IDs to new IDs in `replaced_by`
857. [ ] task content: maintenance: monthly drift check (manual, documented)
858. [ ] task content: maintenance: quarterly gold re-verification
859. [ ] task content: maintenance: annual licence review
860. [ ] task content: maintenance: owner handover checklist

## P8. Tests, CI, docs, release (861–1000)
861. [x] tests: loader rejects invalid ids and YAML errors
862. [x] tests: scoring rejects unregistered types and empty predictions
863. [x] tests: URL and statute reference normalization
864. [x] tests: zero-width and tilde normalization
865. [x] tests: report, show, list filters
866. [x] tests: prompt hash, length guard, parse, adapter, CSV
867. [x] tests: achieve 90% line coverage on jpbench
868. [x] tests: add coverage report to CI
869. [x] tests: fail CI when coverage drops below threshold
870. [ ] tests: mutation testing run on scoring (optional job)
871. [x] tests: property tests with hypothesis for normalize_number
872. [x] tests: property tests with hypothesis for normalize_date
873. [x] tests: property tests with hypothesis for normalize_text idempotency
874. [x] tests: property tests with hypothesis for set_overlap bounds
875. [x] tests: property tests with hypothesis for numeric_tolerance symmetry
876. [ ] tests: test that every normalize rule has at least one golden case
877. [x] tests: test that every success type has a sample passing answer
878. [x] tests: test that every success type has a sample failing answer
879. [ ] tests: test that docs code blocks run (doctest-style)
880. [ ] tests: test that README commands still work
881. [ ] tests: test on Windows-style newlines in task YAML
882. [ ] tests: test on non-UTF-8 locale (encoding fixtures)
883. [x] ci: run on Python 3.10–3.13 (3.10 added; keep)
884. [ ] ci: run on macOS runner in addition to Ubuntu
885. [ ] ci: run on Windows runner for path handling
886. [ ] ci: upload coverage artifact
887. [ ] ci: cache pip (done); verify cache hit in logs
888. [x] ci: concurrency group to cancel superseded runs
889. [x] ci: set minimal permissions (contents: read) in workflow
890. [ ] ci: pin actions to commit SHAs
891. [x] ci: dependabot for GitHub Actions
892. [x] ci: dependabot for pip dependencies
893. [ ] ci: nightly job runs `validate` and `prompt --check`
894. [ ] ci: nightly job checks source drift (manual data, report only)
895. [x] ci: PR template requires running `jpbench validate` output
896. [ ] ci: block merges to main without passing checks (branch protection, documented)
897. [ ] ci: release workflow builds sdist and wheel
898. [ ] ci: release workflow checks the wheel installs and runs `jpbench --version`
899. [ ] ci: release workflow attaches task manifest to the GitHub release
900. [ ] ci: release workflow never publishes from forks
901. [ ] docs: README quick start tested in CI
902. [x] docs: README links to CONTRIBUTING and ROADMAP
903. [ ] docs: README table of tasks matches `jpbench list` output (test)
904. [ ] docs: README explains safety rule with an example
905. [ ] docs: README explains scoring with an example
906. [ ] docs: README explains why Japanese normalization matters
907. [ ] docs: README limitations section
908. [ ] docs: README citation block
909. [ ] docs: README English and Japanese sections
910. [x] docs: CHANGELOG following Keep a Changelog
911. [x] docs: CHANGELOG entries for every merged change since v0.1
912. [x] docs: architecture page (loader, normalize, scoring, runner, report)
913. [x] docs: how-to add a task
914. [x] docs: how-to add a normalization rule
915. [x] docs: how-to add a success type
916. [x] docs: how-to add a model adapter
917. [x] docs: how-to run a benchmark offline with replay
918. [ ] docs: how-to submit to the leaderboard
919. [x] docs: FAQ on ethics and safety of browser agents
920. [x] docs: FAQ on why official sources are used for gold
921. [x] docs: FAQ on why fictional data is used in form tasks
922. [x] docs: FAQ on costs and budgets
923. [ ] docs: security policy (SECURITY.md) with reporting path
924. [ ] docs: code of conduct
925. [x] docs: issue templates (bug, task proposal, scoring question)
926. [x] docs: pull request template with checklist
927. [ ] docs: CODEOWNERS for tasks and scoring
928. [ ] docs: license headers on source files
929. [x] docs: notice file for third-party data sources
930. [x] docs: glossary of Japanese administrative terms with English glosses
931. [ ] release: v0.2.0 candidate with all v0.2 tasks reviewed
932. [ ] release: v0.2.0 changelog and version bump
933. [ ] release: v0.2.0 tag and GitHub release
934. [ ] release: publish sdist and wheel to PyPI (requires maintainer credentials)
935. [ ] release: verify `pip install jpbench==0.2.0` in a clean venv
936. [ ] release: publish task manifest checksum in release notes
937. [ ] release: publish sample run in examples/
938. [ ] release: announce in README (no external posting without owner approval)
939. [ ] release: v0.3 plan from pilot feedback
940. [ ] release: v1.0 scoring freeze criteria written down
941. [ ] release: v1.0 task freeze criteria written down
942. [ ] release: v1.0 API freeze criteria written down
943. [ ] release: v1.0 candidate after holdout evaluation
944. [ ] release: v1.0 review by two external reviewers
945. [ ] release: v1.0 tag
946. [ ] release: v1.0 paper appendix with scoring decisions
947. [ ] release: v1.0 dataset card
948. [ ] release: v1.0 model card template
949. [ ] release: v1.0 governance document (who approves gold changes)
950. [ ] release: v1.0 maintenance policy (support window)
951. [ ] maintenance: quarterly dependency update
952. [ ] maintenance: quarterly source drift review
953. [ ] maintenance: quarterly leaderboard audit
954. [ ] maintenance: deprecation timeline for old scorers
955. [ ] maintenance: deprecation notice for old CLI flags
956. [ ] maintenance: migration guide for each breaking change
957. [ ] maintenance: archive v0.1 results under results/v0.1
958. [ ] maintenance: archive policy for old run files
959. [ ] maintenance: triage label set (bug, task, scoring, docs, good-first-issue)
960. [ ] maintenance: good-first-issue list kept at 10 items
961. [ ] community: contributor recognition in CONTRIBUTORS.md
962. [ ] community: contribution guide for task authors (non-coders)
963. [ ] community: contribution guide for translators
964. [ ] community: contribution guide for reviewers
965. [ ] community: office hours announcement template (no posting without owner approval)
966. [ ] community: decision log in docs/decisions/
967. [ ] community: ADR template
968. [ ] community: ADR for scoring freeze
969. [ ] community: ADR for browser safety rule
970. [ ] community: ADR for fictional data policy
971. [ ] community: ADR for official-source gold policy
972. [ ] community: ADR for adapter contract
973. [ ] community: ADR for result format
974. [ ] community: ADR for leaderboard policy
975. [ ] community: ADR for licence policy
976. [ ] community: ADR for holdout policy
977. [ ] analysis: error analysis notebook by task family
978. [ ] analysis: error analysis by normalization rule hits
979. [ ] analysis: error analysis by parse error kind
980. [ ] analysis: calibration plot for abstain tasks
981. [ ] analysis: difficulty vs pass rate plot
982. [ ] analysis: cost vs score plot
983. [ ] analysis: time per task distribution
984. [ ] analysis: step count distribution for browser traces
985. [ ] analysis: safety near-miss report (agent navigated close to submit)
986. [ ] analysis: report of tasks where all adapters failed (task quality signal)
987. [ ] analysis: report of tasks where all adapters passed (too easy)
988. [ ] analysis: report of scorer disagreements between two graders
989. [ ] analysis: report of normalization rules that changed gold-equal pairs
990. [ ] analysis: report of distractor hit rate
991. [ ] research: write up scoring methodology as a short paper draft
992. [ ] research: prepare dataset documentation for submission
993. [ ] research: prepare reproducibility checklist
994. [ ] research: prepare ethics statement
995. [ ] research: prepare limitations section
996. [ ] research: prepare related-work section (benchmarks for web agents)
997. [ ] research: prepare appendix with all success type definitions
998. [ ] research: prepare appendix with fictional data examples
999. [ ] research: prepare appendix with normalization rule table
1000. [ ] research: prepare final review checklist before submission
