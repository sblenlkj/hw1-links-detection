# Legal Reference Detector — краткая архитектура

Проект извлекает ссылки на российские нормативные документы из произвольного текста и возвращает:

```python
LawLink(
    law_id: int,
    article: str | None,
    point_article: str | None,
    subpoint_article: str | None,
)
```

## Pipeline

```text
raw text
   ↓
TextNormalizer
   ↓
independent regex strategies
   ↓
CandidateSegmentor
   ↓
valid Segment
   ↓
DocumentResolver
   ↓
ResolvedDocument(law_id)
   ↓
LinksFinalizer
   ↓
Cartesian expansion + deduplication
   ↓
LawLink[]
```

## 1. Normalization

`TextNormalizer` хранит одновременно:

- `original` — исходный текст и точные offsets;
- `lowercase` — удобная версия для case-insensitive structural matching.

Глобальная нормализация намеренно минимальна, чтобы не менять длину текста.

## 2. Strategies

`src/links_detector/candidates_segmenter/strategies/`

Независимые detectors находят локальные сигналы:

- `DiscourseMatch` — `согласно`, `в соответствии с`, `на основании` и т.д.;
- `ArticleMatch` — статья/ст.;
- `PartMatch` — часть/ч.;
- `PointMatch` — пункт/п.;
- `SubpointMatch` — подпункт/пп.;
- `FamilyMatch` — тип документа: code, federal_law, presidential_decree и т.д.;
- `QuoteMatch` — текст в `"..."` или `«...»`.

Structural matches умеют хранить несколько values:

```text
пп. 4, 5, 6 и 8 → ("4", "5", "6", "8")
пункта 3.345, 23 → ("3.345", "23")
подпунктах а, б и с → ("а", "б", "с")
```

Family detection и поиск конкретного `law_id` разделены.

## 3. Segmentor

Все matches сортируются по offsets и объединяются в `Segment`.

Segment валиден, если содержит:

```text
STRUCTURE + (FamilyMatch OR QuoteMatch)
```

Discourse marker служит boundary, но для валидности не обязателен.

Invalid segments сохраняются для диагностики.

## 4. Resolver

`DocumentResolver` превращает valid Segment в:

```python
ResolvedDocument(law_id, family)
```

Он использует compact datasets из:

```text
law_aliases/families/
```

Способы resolution:

- quoted title;
- number/date для structured acts;
- отдельный regex-based `CodeResolver` для кодексов;
- PBU identifier для ПБУ;
- global exact title lookup как fallback для quote.

## 5. Finalizer

`LinksFinalizer.extract(text)` orchestrates весь pipeline.

После resolution structural lists раскрываются Cartesian product.

Например:

```text
подпунктах а, б и с
пункта 3.345, 23
статье 66 НК РФ
```

создаёт 6 ссылок:

```text
2 points × 3 subpoints = 6 LawLink
```

`PartMatch` и `PointMatch` в текущем output оба записываются в `point_article`.

После expansion одинаковые LawLink удаляются с сохранением порядка первого появления.

## 6. Diagnostics

`FinalizerResult.stats`:

- `total_segments`;
- `invalid_segments`;
- `resolver_failed`;
- `resolved_segments`;
- `expanded_segments`;
- `unique_links`.

Это позволяет отличить ошибку segmentation от ошибки document resolution.

## 7. Tests

Regex strategies покрыты pytest:

```bash
uv run pytest
```

End-to-end regression baseline:

```bash
uv run python smoke_tests/smoke_candidates.py 0
```

Для `00_readme_example` текущий gold:

```text
expected:   34
matched:    34
missing:     0
unexpected:  0
```

После изменения regex сначала запускаем unit tests, затем end-to-end gold smoke.

## 8. Где менять код

```text
новая форма статьи/пункта → structure_strategy.py
новый discourse marker   → discourse_strategy.py
новый alias family       → family_strategy.py
новый quote format       → quote_strategy.py
family есть, law_id нет  → document_resolver/
изменение output rules   → finalizer/
```

Главная ментальная модель:

```text
Strategies → что написано?
Segmentor  → что относится к одной ссылке?
Resolver   → какой это документ?
Finalizer  → какие LawLink вернуть?
```
