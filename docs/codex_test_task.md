# Codex black-box test task

## Goal

Test the running legal-link detection service as a black box.

Do not modify the parser, resolver, API implementation, aliases, or tests during this task.
Your job is to generate valid test text from prepared targets, call the running FastAPI service, compare expected and detected law IDs, and report failures.

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

`/detect` intentionally returns both exact matches and all candidates from ambiguous matches.
The test is recall-oriented with respect to ambiguity, but it validates the full parsed structure: a run passes only when every expected `(law_id, article, point_article, subpoint_article)` tuple is present in the returned set.

## Step 1. Generate balanced targets

Run:

```bash
uv run python scripts/codex_generate_cases.py --runs 5 --references 3 --seed 42
```

This creates:

```text
.artifacts/codex_test_cases.json
```

The file contains 5 runs with 3 targets each.
Sampling is balanced across document families as much as possible.
A family with only one available document is sampled at most once.

Each target has:

```json
{
  "law_id": 970,
  "family": "rf_law",
  "structure_kind": "parts_article",
  "structure": "части 2 и 4 статьи 14",
  "document_form": "Федеральный закон \"О беженцах\"",
  "expected_links": [
    {
      "law_id": 970,
      "article": "14",
      "point_article": "2",
      "subpoint_article": null
    },
    {
      "law_id": 970,
      "article": "14",
      "point_article": "4",
      "subpoint_article": null
    }
  ]
}
```

The generator deliberately varies structure shape. Across the batch you may see:

- one article: `статья 12`;
- several articles: `статьи 12 и 18`;
- one point without an article: `пункт 4`;
- several points without an article: `пункты 2 и 7`;
- one or several parts of one article;
- one or several points of one article;
- one or several subpoints of one point/article;
- several points combined with several articles, which should expand to multiple LawLink combinations.

Do not simplify a generated structure. Preserve every value it contains.

## Step 2. Generate test text yourself

Read `.artifacts/codex_test_cases.json`.

For each run, write one natural Russian legal-style paragraph or short multi-sentence fragment containing all targets from that run exactly once.

The parser is intentionally rule-based. Every target must appear locally in exactly this shape:

```text
<STRUCTURE> <DOCUMENT_FORM>
```

Examples:

```text
статья 82 Федерального закона №13-ФЗ
статьи 82 и 91 Федерального закона №13-ФЗ
пункт 6 Федерального закона №13-ФЗ
пункты 3 и 7 Федерального закона №13-ФЗ
части 2 и 4 статьи 91 Семейного кодекса
пункты 6 и 8 статьи 84 Федерального закона от 11.11.2003 №138-ФЗ
подпункты "а" и "в" пункта 12 статьи 17 ФЗ от 29.12.2020 №472-ФЗ
пункты 2 и 4 статей 10 и 12 Федерального закона №13-ФЗ
```

Rules:

- Put the structure before the document form.
- Keep structure and document form adjacent except for normal grammatical spacing.
- Preserve `document_form` exactly as provided: spelling, number, date, abbreviation, title, quotes, and case.
- Do not replace a document with "данный закон", "указанный акт", etc.
- Do not put the structure after the document or in parentheses after it.
- Do not invent another document type or number.
- Do not add additional legal references not present in the run.
- Do not include `law_id`, run IDs, target IDs, comments, Markdown emphasis, footnotes, or explanations inside the generated text.
- Ordinary surrounding legal prose is allowed.
- Do not change the service code when a generated case fails.

Write all generated texts to:

```text
.artifacts/codex_generated_texts.json
```

with this exact shape:

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

Include exactly one item for every run in the cases file.

## Step 3. Run the black-box checker

Run:

```bash
uv run python scripts/codex_check_cases.py
```

The checker:

1. sends every generated text to `POST /detect`;
2. collects the full returned LawLink tuples:
   `(law_id, article, point_article, subpoint_article)`;
3. compares them with every `expected_links` entry generated for the target;
4. treats ambiguous candidates as valid detections because `/detect` already flattens them;
5. verifies expansion of multi-value structures, not only document detection;
6. writes a detailed report to:

```text
.artifacts/codex_test_report.json
```

A run is PASS when every expected full LawLink is returned:

```text
expected_links ⊆ detected_links
```

For example, if the target contains `пункты 2 и 4 статьи 10`, the server must return both:

```text
(law_id, article=10, point_article=2)
(law_id, article=10, point_article=4)
```

If the target contains `пункты 2 и 4 статей 10 и 12`, all four article/point combinations are expected.

Unexpected extra detections do not fail the run, but they must remain visible in the report.

## Step 4. Analyze failures

If all 5 runs pass, report the result and stop.

If any run fails, do not modify production code.

Read `.artifacts/codex_test_report.json` and classify each failed run into one of:

1. **GENERATION_ERROR** — your text violated the required `<STRUCTURE> <DOCUMENT_FORM>` contract or changed the target.
2. **UNSUPPORTED_FORM** — the text follows the requested target but exposes a format outside the parser's intended contract.
3. **PARSER_CANDIDATE_BUG** — the text follows the contract and the expected `law_id` is still absent.

For every failed run report:

- run ID;
- original targets;
- generated text;
- expected law IDs;
- detected law IDs;
- missed full LawLink tuples;
- unexpected full LawLink tuples;
- classification;
- concise explanation of the likely cause.

Do not patch code automatically.
Do not rewrite aliases automatically.
Do not rerun with easier text merely to hide a failure.

## Final response

Return a concise summary containing:

- number of runs passed;
- number failed;
- family distribution from the cases file;
- structure distribution from the cases file;
- any unexpected detections;
- one short section per failed run with its classification and likely cause;
- path to the JSON report.

If all runs pass, explicitly say that the black-box check passed 5/5.
