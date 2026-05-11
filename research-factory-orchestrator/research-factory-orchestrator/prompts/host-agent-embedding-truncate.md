# Host agent: truncate before embedding (RFO claims / snippets)

RFO computes **RAF / citation grounding** from `claims-registry.json` and `citation-grounding-result.json` on disk — that path does **not** use your separate embedding model. If **your** host stack embeds claim text, evidence snippets, or relay HTML for RAG / rerank / memory:

## Rules

1. **Hard cap** — перед вызовом embed обрежь вход до **≤ 2000 символов Unicode** (или лимита твоей модели эмбеддинга минус запас под префикс инструкции). Для очень длинных полей бери **заголовок + первый осмысленный абзац**, не сырой HTML целиком.
2. **Структура** — одна строка на сущность: `[claim_id] {короткая формулировка} :: {обрезанный сниппет}`; не дублируй полный `full-report.html`.
3. **Язык** — не полагайся на «эмбеддинг сам поймёт язык»; для смешанных ранов нормализуй пробелы/невидимые символы и убери нулевые байты.
4. **Детерминизм** — один и тот же вход должен давать тот же вектор в повторных прогонах (фиксируй правило обрезки в промпте агента, не «на глаз» в чате).

## One-liner для system / tool prompt

> Before calling your embedding API on any RFO-derived claim, evidence snippet, or fetched page text, truncate to **at most 2000 Unicode characters** (title + lede only for web pages); strip HTML tags; never embed the full `full-report.html` body.
