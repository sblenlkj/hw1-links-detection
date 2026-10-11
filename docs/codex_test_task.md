# Codex black-box test task

## Goal

Test the running legal-link detection service as a black box.

Do not modify the parser, resolver, API implementation, aliases, or tests during this task.
Your job is to:

1. generate a balanced set of targets;
2. turn those targets into natural Russian legal-style text;
3. deliberately exercise a small set of supported edge cases;
4. call the running FastAPI service;
5. compare expected and detected full LawLink tuples;
6. report failures without patching production code.

The service is expected to be running at:

```text
http://127.0.0.1:8978
```

The endpoint under test is:

```text
POST /detect
{"text": "..."}
```

The response contract is:

```json
{
  "links": [
    {
      "law_id": 123,
      "article": "10",
      "point_article": "2",
      "subpoint_article": "а"
    }
  ]
}
```

`/detect` intentionally returns both exact matches and all candidates from ambiguous matches, preserving their text order.

The test is recall-oriented with respect to ambiguity, but validates the full parsed structure. A run passes only when every expected

```text
(law_id, article, point_article, subpoint_article)
```

tuple is present in the returned set.

Unexpected extra detections remain visible in the report and must be discussed even though they do not fail the run.

## Step 1. Generate balanced targets

Run, for example:

```bash
uv run python scripts/codex_generate_cases.py --runs 5 --references 3 --seed 211
```

Use a different explicit seed for later independent batches.

This creates:

```text
.artifacts/codex_test_cases.json
```

Sampling is balanced across document families as much as possible. A family with only one available document is sampled at most once.

Each target contains:

- `law_id`;
- document `family`;
- `structure_kind`;
- concrete `structure`;
- concrete `document_form`;
- one or more `expected_links`.

The generator deliberately varies structure shape. Across a normal 5×3 batch it attempts to cover:

- one article;
- several articles;
- one point without an article;
- several points without an article;
- one or several parts of an article;
- one or several points of an article;
- one or several subpoints;
- several points combined with several articles.

Do not simplify multi-value structures. For example:

```text
пункты 2 и 4 статей 10 и 12
```

must represent four expected LawLinks.

## Step 2. Generate legal-style test text

Read:

```text
.artifacts/codex_test_cases.json
```

For each run, write one natural Russian legal-style paragraph or short multi-sentence fragment containing every target from that run exactly once.

The baseline parser contract is:

```text
<STRUCTURE> <DOCUMENT_FORM>
```

The structure must come before the document. Keep them local to one another.

Examples:

```text
статья 82 Федерального закона №13-ФЗ
пункт 6 статьи 84 Федерального закона №138-ФЗ
части 2 и 4 статьи 91 Семейного кодекса
подпункты "а" и "в" пункта 12 статьи 17 ФЗ №472-ФЗ
пункты 2 и 4 статей 10 и 12 Федерального закона №13-ФЗ
```

### Regression probes to exercise

The parser now intentionally supports several edge cases. When the current targets permit it, distribute these probes across the batch rather than making every reference maximally difficult.

#### 1. Number-prefix variants

For structured acts whose `document_form` contains a number such as:

```text
Федеральный закон №225-ФЗ
```

it is allowed to use an equivalent surface variant in selected cases:

```text
Федеральный закон № 225-ФЗ
Федеральный закон N 225-ФЗ
```

Do not change the actual number, suffix, date, family, or title.

Use these variants only for numbered structured acts. Do not invent a number for title-only documents.

#### 2. Compact structure markers

In selected cases, normal spacing may be removed after abbreviated structural markers:

```text
ст.5
п.10
пп.«а»
```

Do not reorder the hierarchy.

#### 3. Guillemets for subpoints

A quoted subpoint may use Russian guillemets:

```text
пп. «а»
```

instead of ordinary double quotes when this does not alter the target value.

#### 4. Several references in one sentence

It is useful to place two complete references in the same sentence using connectors such as:

```text
и
а также
при этом
```

Each target must still remain structurally identifiable.

In particular, the parser must distinguish:

```text
п. 1 ст. 5 ... и п. 2 ст. 7 ...
```

from a single multi-value construction such as:

```text
пункты 1 и 2 статей 5 и 7 ...
```

Do not silently rewrite one form into the other.

#### 5. Benign negative noise

A small amount of ordinary prose may contain expressions such as:

```text
т. п.
т.п.
т. ч.
т.ч.
```

These must not be intentionally presented as legal references.

Use this only as surrounding prose. Do not place such noise between a target's structure and its document form.

#### 6. Nearby second code mention

For a code-family target, one run may contain a nearby comparison such as:

```text
ст. 10 ГК РФ (в отличие от УК РФ)
```

The first complete reference must remain detectable even though another code is mentioned nearby.

Do this sparingly and never replace the target's actual code.

#### 7. Text order

When a run contains several references, keep a clear order in the generated text. The public `/detect` endpoint is expected to return exact links and ambiguous candidates in source-text order.

### Important boundaries

Do NOT test unsupported semantics merely because they appear in natural language.

In particular, do not generate:

- document before structure, e.g. `НК РФ, статья 5`;
- simultaneous point + part mapped into separate output fields, e.g. `п. 2 ч. 1 ст. 12.8`;
- reversed hierarchy such as `ст. 5 ч. 3 п. 2`;
- arbitrary long-distance inheritance of a document across unrelated prose;
- lowercase/case variants unless they were explicitly chosen as a regression probe supported by the current parser.

The goal is to stress supported behavior, not silently expand the assignment contract.

### General generation rules

- Include every target exactly once.
- Do not add extra legal references except for a deliberate nearby-code comparison probe.
- Do not output `law_id`, run IDs, target IDs, comments, Markdown, footnotes, or explanations inside the generated text.
- Do not replace a document with "данный закон", "указанный акт", etc.
- Do not invent another document type, number, date, or title.
- Title-only `document_form` values must remain title-only.
- Preserve nested quoted titles carefully. If a title itself contains straight quotes, do not wrap the whole title in the same straight quotes. Use Russian guillemets outside and keep the inner straight quotes, for example: `«О некоторых вопросах фонда "Русский мир"»`.
- Do not change production code when a generated case fails.

Write all generated texts to:

```text
.artifacts/codex_generated_texts.json
```

with exactly:

```json
{
  "runs": [
    {
      "run_id": 1,
      "text": "..."
    }
  ]
}
```

Include one item for every run in the cases file.

## Step 3. Run the black-box checker

Run:

```bash
uv run python scripts/codex_check_cases.py
```

The checker:

1. sends every generated text to `POST /detect`;
2. collects full returned LawLink tuples;
3. compares them with every generated `expected_links` entry;
4. treats ambiguous candidates as valid detections;
5. verifies multi-value expansion;
6. records unexpected detections;
7. writes:

```text
.artifacts/codex_test_report.json
```

A run is PASS when:

```text
expected_links ⊆ detected_links
```

Unexpected extra detections do not fail the run, but must remain visible in the report.

## Step 4. Analyze failures

If every run passes, report the result and stop. Do not patch production code.

If any run fails, classify it as one of:

1. **GENERATION_ERROR** — generated text violated the intended target or unsupported semantics were introduced.
2. **UNSUPPORTED_FORM** — text is reasonable but outside the parser contract defined above.
3. **PARSER_CANDIDATE_BUG** — text follows the supported contract but an expected full LawLink is missing.
4. **REGRESSION_BUG** — one of the explicitly supported regression probes above no longer works.

For each failure report:

- run ID;
- target(s);
- generated text;
- expected full LawLinks;
- detected full LawLinks;
- missed tuples;
- unexpected tuples;
- classification;
- likely cause.

Do not modify aliases or parser code automatically. Do not rerun with easier text merely to hide a failure.

## Final response

Return a concise summary containing:

- passed / failed run count;
- seed;
- family distribution;
- structure distribution;
- which regression probes were exercised;
- any unexpected detections;
- classification for every failed run;
- report path.

If all five runs pass, explicitly state that the black-box check passed 5/5.
