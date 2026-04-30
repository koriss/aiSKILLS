# OpenClaw RFO v18.2 — Source Quality Weighting System

## 0. Коротко

Эта подсистема нужна, чтобы Research Factory не смешивала разные типы доказательств:

```text
официальная статистика ≠ независимая истина обо всём
слова депутата ≠ статистический показатель
слова блогера “всё пропало” ≠ доказанный факт
10 перепечаток ≠ 10 независимых подтверждений
пресс-релиз ≠ внешняя верификация
академическая статья ≠ первичный юридический статус
```

Главный принцип:

```text
Source quality is claim-relative.
Evidence weight is role-relative.
Official does not mean neutral.
Unofficial does not mean worthless.
```

---

## 1. Что подсистема должна исправить

Плохая модель:

```text
official > academic > media > blog > social
```

Она слишком простая.

Правильная модель:

```text
источник получает не один глобальный trust score,
а evidence vector относительно конкретного claim-а.
```

Официальный источник может быть:

```text
1. сильным источником для официально опубликованной цифры;
2. сильным источником для того, что орган/актор заявил;
3. сильным источником для анализа официального нарратива;
4. слабым или заинтересованным источником для независимого описания реальности;
5. объектом проверки, а не арбитром истины.
```

Блогер/Telegram-канал/оппозиционный источник может быть:

```text
1. слабым источником для масштабного factual claim без данных;
2. сильным источником для своего собственного заявления;
3. useful lead-source;
4. сильным источником, если публикует первичные документы, видео, датасет, логи;
5. источником альтернативного нарратива, но не автоматическим доказательством.
```

---

## 2. Разделение claim regimes

Каждый claim должен быть отнесён к одному или нескольким epistemic regimes.

### 2.1 Record claim

```text
“В документе X написано Y.”
“Росстат опубликовал показатель Z.”
“Компания заявила A.”
```

Нужны источники-records: официальный документ, архив, первичный URL, реестр, стенограмма.

### 2.2 Statement claim

```text
“Актор X сказал Y.”
```

Сильный источник — сам актор, стенограмма, verified profile, видео/аудио с provenance.

### 2.3 Empirical/world-state claim

```text
“В реальности произошло Y.”
“Показатель реально равен Z.”
```

Нужны данные, метод, независимость, первичные наблюдения, triangulation.

### 2.4 Causal claim

```text
“Y произошло из-за X.”
```

Самый строгий режим. Нужны методология, альтернативные объяснения, independent corroboration, causal design.

### 2.5 Legal claim

```text
“Статус X юридически такой-то.”
```

Нужны закон, суд, реестр, регуляторное решение. Медиа и блог — вторичны.

### 2.6 Scientific claim

```text
“Исследование показывает X.”
```

Нужны peer review / preprint / dataset / reproducibility / systematic review / guideline.

### 2.7 Narrative / propaganda claim

```text
“Источник продвигает нарратив X.”
“Сообщение использует метод Y.”
```

Сильны первичные тексты/посты/видео, amplification graph, repeated frames, actor linkage. Official source может быть сильным источником официального нарратива, но не нейтральным арбитром.

### 2.8 Sentiment / perception claim

```text
“У аудитории/группы есть тревога/недоверие/паника.”
```

Нужны соцсигналы, опросы, комментарии, community posts, но нельзя превращать loud minority в population fact.

---

## 3. Evidence vector вместо одного trust score

Каждая связка `source ↔ claim` получает вектор:

```json
{
  "authenticity": 0.95,
  "source_reliability_history": 0.70,
  "claim_role_fit": 0.90,
  "authority_scope_fit": 0.85,
  "proximity_to_observation": 0.80,
  "method_transparency": 0.70,
  "data_access": 0.60,
  "independence": 0.75,
  "strategic_interest_risk": 0.30,
  "environment_distortion_risk": 0.20,
  "laundering_risk": 0.10,
  "corroboration": 0.80,
  "conflict_status": 0.90,
  "freshness": 0.85,
  "scope_granularity_match": 0.90,
  "auditability": 0.80
}
```

Важно: `strategic_interest_risk` и `environment_distortion_risk` — это риски, не веса. Они уменьшают итоговый вес, но не превращают источник автоматически в ложный.

---

## 4. Итоговые веса

### 4.1 Нельзя полностью доверять арифметике

Веса — не замена аналитике. Они нужны для gate/validator/sorting.

Итоговая оценка:

```text
evidence_weight =
  base_claim_role_fit
  × authority_scope_fit
  × proximity_to_observation
  × method_transparency
  × data_access
  × independence
  × corroboration
  × freshness
  × scope_granularity_match
  × auditability
  × penalties
```

Penalties:

```text
strategic_interest_penalty
environment_distortion_penalty
laundering_penalty
conflict_penalty
scope_mismatch_penalty
```

Если `authority_scope_fit = 0`, итоговый вес = 0 независимо от репутации источника.

### 4.2 Не все claim types требуют одинакового порога

```text
record_claim:
  может быть confirmed одним сильным первичным record-source.

public_statement:
  может быть confirmed одним первичным actor-source.

official_statistical_value:
  может быть confirmed официальной статистикой within official methodology,
  но это не подтверждает альтернативный “реальный показатель”.

causal_explanation:
  почти никогда не confirmed одним источником;
  нужен метод + независимые источники + конфликтный поиск.

propaganda/narrative:
  подтверждается первичным материалом + паттернами + repetition/amplification,
  а не “кто прав”.
```

---

## 5. Claim-source fit matrix

### 5.1 official_statistical_value

Strong:

```text
official_statistics
central_bank within mandate
international_organization within statistical mandate
official dataset / registry within scope
```

Medium:

```text
academic_peer_reviewed using same dataset
database_secondary with transparent upstream provenance
reputable media directly citing primary data
```

Weak / lead:

```text
expert_blog explaining data
media summary without primary link
```

Invalid as primary:

```text
political_actor
party_media
opinion_column
personal_blog
social_post
forum_post
```

Но:

```text
official_statistical_value должен рендериться как:
“confirmed as official value / within published methodology”
а не “ultimate reality”.
```

### 5.2 alternative_estimate / methodology_critique

Strong:

```text
transparent dataset
reproducible method
academic / expert methodology
auditable calculation
independent raw data
```

Medium:

```text
think_tank with method
investigative_media with documents
expert blog with data and reproducible calculation
```

Weak:

```text
blog opinion without data
political claim without method
anonymous estimate
```

### 5.3 political_position / public_statement

Strong:

```text
political_actor for own statement
official transcript
verified account
official press release
video/audio with provenance
```

But this only proves:

```text
actor said it / actor position / narrative
```

Not:

```text
claim is factually true
```

### 5.4 causal_explanation

Strong:

```text
peer-reviewed causal design
official investigation within mandate
court finding within legal scope
multi-source investigation with documents
```

Medium:

```text
expert analysis with disclosed method
think tank with methodology
investigative media with primary documents
```

Weak:

```text
political actor
opinion column
blog without method
```

### 5.5 propaganda_method_match

Strong:

```text
primary content sample
repeated narrative frame
known method from KB matched to text
amplification graph
actor linkage
```

Medium:

```text
academic/media/NGO analysis with examples
```

Weak:

```text
single partisan accusation
unsupported “this is propaganda”
```

---

## 6. Official-source nuance

Официальный источник должен иметь `official_mode`.

```text
custodian_of_record
statistical_publisher
regulatory_decision_maker
court_or_legal_authority
actor_press_office
state_media
political_executive
security_service_statement
wartime_information_actor
```

### 6.1 `custodian_of_record`

Высокий вес для:

```text
record exists
record says X
legal/registry status within scope
```

Низкий/средний вес для:

```text
interpretation outside mandate
causal narrative
self-exculpatory claim
```

### 6.2 `statistical_publisher`

Высокий вес для:

```text
official measure
published methodology
time series
```

С осторожностью для:

```text
contested definitions
missing categories
suppressed methodology
politically sensitive metrics
```

### 6.3 `actor_press_office`

Высокий вес для:

```text
what actor claims
official line
narrative position
```

Низкий вес для:

```text
independent factual verification
causal claims about opponents
claims of innocence/guilt
```

### 6.4 `state_media`

Обычно:

```text
strong for narrative analysis
medium/weak for factual claims depending on sourcing
high strategic_interest_risk
requires independent corroboration for contested facts
```

---

## 7. Non-official-source nuance

### 7.1 Blogger / expert blog

Низкий вес для:

```text
broad empirical claim without data
catastrophic generalization
causal claim without method
```

Может стать medium/high, если есть:

```text
primary documents
raw data
reproducible calculations
domain expertise
transparent method
track record
specific falsifiable claim
```

### 7.2 Social post

Сильный для:

```text
the author posted this
early lead
eyewitness claim if provenance preserved
narrative/sentiment sample
```

Слабый для:

```text
population-level fact
causality
statistics
unverified accusation
```

### 7.3 Media

Сила зависит от:

```text
primary sourcing
named sources
documents shown
method transparency
corrections policy
independence
whether it is reprint or original reporting
```

---

## 8. Source laundering / echo amplification

### 8.1 Правило

```text
Many citations are not many confirmations.
```

Если 20 сайтов перепечатали один пресс-релиз:

```text
independent_support_count = 1
visibility_count = 20
```

### 8.2 Использование

Derived sources могут доказывать:

```text
spread / amplification / visibility
```

Но не должны доказывать:

```text
truth of original claim
```

---

## 9. Conflict handling

При конфликте разных source roles нельзя усреднять.

Пример:

```text
Official: показатель X = 5.1.
Blogger: “реально X = 20, всё скрывают”.
Expert: “официальная методика не учитывает сегмент Y”.
```

Правильный split:

```text
CLM-1:
  official X = 5.1 according to official methodology
  verdict: confirmed_within_scope

CLM-2:
  blogger claims X=20 / hidden
  verdict: confirmed_as_statement; unverified_as_world_state unless data/method

CLM-3:
  methodology may omit segment Y
  verdict: evaluate by expert/data quality

CLM-4:
  alternative estimate X=20
  verdict: requires reproducible method and data
```

---

## 10. Source rank classes

Не использовать один `trust score`. Использовать классы:

```text
E5 authoritative_in_scope
E4 strong_primary_or_methodic
E3 useful_but_limited
E2 weak_or_interested
E1 lead_only
E0 invalid_for_claim
```

Пример:

```text
Росстат для official CPI:
  E5 authoritative_in_scope

Росстат для “политическая причина инфляции”:
  E2/E0 depending on statement and scope

Депутат для “он сказал X”:
  E5

Депутат для “реальная инфляция Y”:
  E1/E2 unless provides data/method

Блогер с документами и расчётом:
  E3/E4 depending on auditability

Блогер “всё пропало”:
  E1 as signal/opinion, E0 for factual confirmation
```

---

## 11. Verdict model

```text
confirmed_within_scope:
  strong in-scope source, scope explicitly stated

confirmed_as_statement:
  actor/source said it; no claim that statement is true

likely:
  high evidence weight, independent support, no major unresolved conflict

partial:
  evidence supports part of claim or limited scope

contested:
  strong sources conflict, no resolution

unverified:
  weak/lead/opinion only

misleading:
  contains true elements but wrong implication/scope

rejected:
  reliable in-scope evidence contradicts claim

insufficient_evidence:
  not enough source fit / provenance
```

---

## 12. Render policy

### 12.1 HTML citation labels

Each citation must expose source role:

```text
[12 official_statistics / E5 / official value only]
[18 political_actor / E5 statement / E1 factual]
[21 expert_blog / E3 methodology critique]
[27 media_news / E2 derived reprint]
```

### 12.2 Report text

Bad:

```text
“Источники подтверждают...”
```

Good:

```text
“Официальная цифра подтверждена как опубликованный показатель Росстата.
Альтернативная оценка блогера подтверждена только как публичное заявление;
для factual confirmation у неё недостаточно метода/данных.”
```

### 12.3 Telegram summary

```text
Качество источников:
- официальная статистика: использована только для official value;
- заявления акторов: использованы как позиции/нарративы;
- блог/соцсети: использованы как leads/sentiment, не как статистика;
- альтернативные оценки: приняты только там, где есть данные и метод.
```

---

## 13. Validators

Required validators:

```text
validate_source_quality_schema.py
validate_claim_source_fit.py
validate_official_source_scope.py
validate_political_actor_not_statistics.py
validate_self_claim_not_external_confirmation.py
validate_blog_opinion_not_factual_confirmation.py
validate_source_laundering.py
validate_citation_quality_labels.py
validate_claim_verdict_requires_weight.py
validate_propaganda_mode_separates_truth_from_narrative.py
```

---

## 14. Failure codes

```text
F170 political_actor_used_as_statistics_source
F171 self_claim_promoted_to_external_fact
F172 source_laundering_counted_as_independence
F173 citation_missing_source_quality_label
F174 confirmed_claim_without_valid_source_fit
F175 official_source_used_out_of_scope
F176 opinion_column_used_as_factual_causality
F177 aggregator_without_upstream_provenance
F178 official_statement_treated_as_neutral_truth
F179 blogger_catastrophe_claim_promoted_without_method
F180 propaganda_narrative_confused_with_fact_verdict
F181 many_reprints_counted_as_independent_confirmation
F182 alternative_estimate_without_method_marked_confirmed
```

---

## 15. Agent pattern

Recommended agents/workers:

```text
source_classifier:
  classifies source type, official mode, publisher, editorial mode.

claim_decomposer:
  splits official/statement/world-state/causal/narrative claims.

provenance_auditor:
  checks upstream origin, chain, timestamp, archival copy.

source_fit_checker:
  checks source ↔ claim fit.

laundering_detector:
  clusters reprints and upstream dependencies.

contrary_evidence_worker:
  searches for refuting/competing evidence.

propaganda_context_worker:
  separates narrative, actor interest, amplification, framing.

citation_support_checker:
  verifies each citation actually supports the specific sentence.

final_gate:
  blocks confirmed verdict without valid evidence weight.
```

---

## 16. Minimal implementation plan for v18.2

```text
1. Add schemas.
2. Add source-quality-policy.json.
3. Add claim-source-fit matrix.
4. Add rank classes E0-E5.
5. Add validators F170-F182.
6. Add report citation labels.
7. Add source-quality section to final-answer-gate.
8. Add source laundering artifact.
9. Add propaganda-aware claim split.
10. Add smoke test with official vs blogger vs political actor conflict.
```

---

## 17. Acceptance test

Input:

```text
Исследуй инфляцию и спор вокруг официальных данных.
```

Evidence:

```text
SRC-1: official statistics agency publishes CPI = 5.1
SRC-2: deputy says “real inflation is hidden”
SRC-3: blogger says “everything collapsed”
SRC-4: expert publishes reproducible basket calculation = 12.4
SRC-5: 15 media outlets reprint deputy claim
```

Expected:

```text
CLM-1 official CPI=5.1:
  confirmed_within_scope, E5 official value only

CLM-2 deputy said hidden:
  confirmed_as_statement, E5 statement / E1 factual

CLM-3 everything collapsed:
  E1 sentiment/lead, unverified as world-state

CLM-4 alternative estimate=12.4:
  E3/E4 depending on method/data, separate from official CPI

CLM-5 claim has wide media spread:
  confirmed as amplification/visibility, not truth

No merged verdict like:
  “official says 5.1 but really everything is hidden”
```
