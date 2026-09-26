# Law families

`law_aliases.json` is already arranged in contiguous blocks, so we treat those blocks as separate document families.

The families are not only metadata. They define different matching domains and may use different models / parsing logic.

## 1. Structured acts

### Presidential order — 21..54

Typical useful fields:

- family aliases: `Распоряжение Президента Российской Федерации`, shorter variants;
- number;
- date;
- title.

Expected matching strategy:

```text
family marker -> number/date/title -> law_id
```

### Federal law — 55..542

Typical useful fields:

- family aliases: `Федеральный закон`, `ФЗ`, grammatical variants;
- number;
- date;
- title.

Number alone is not guaranteed to be unique, so date/title may be needed for disambiguation.

Expected matching strategy:

```text
family marker -> number + optional date/title -> law_id
```

### Presidential decree — 543..957

Typical useful fields:

- family aliases: `Указ Президента Российской Федерации`, `Указ Президента РФ`, etc.;
- number;
- date;
- title.

Expected matching strategy is almost the same as for federal laws and presidential orders.

These three families are the first implementation target because they have a very regular structure and together cover most of the dataset.

## 2. Codes — 0..20

Codes are a different domain.

There is usually no useful `number + date + title` structure. Instead, each code has a relatively small set of long and short aliases:

```text
Налоговый кодекс Российской Федерации
НК РФ
НК
```

```text
Уголовный кодекс Российской Федерации
УК РФ
УК
```

The likely strategy is alias-based matching:

- canonical long name;
- medium name;
- short abbreviation;
- normalized grammatical variants where needed.

Because there are only 21 codes, this family can be handled explicitly and independently from the large structured-act families.

## 3. Fundamentals of legislation — 958

Single-item family.

It can be implemented separately after the main families. No need to generalize around one object prematurely.

## 4. Laws of the Russian Federation — 959..990

32 documents.

Structurally they are close to federal laws:

- family marker;
- number;
- date;
- title.

They should probably reuse most of the structured-law matching logic, with their own family aliases.

## 5. Federal accounting standards — 991..1035

45 documents.

This is a title-oriented domain. The canonical first alias is usually the quoted standard title, while other aliases may contain FSB/standard wording.

Likely matching signals:

- quoted title;
- standard identifier when present;
- explicit federal-standard wording.

This should not be mixed with PBU / accounting regulations because their naming conventions differ.

## 6. Accounting regulations / PBU — 1036..1054

19 documents:

- one general accounting regulation at index 1036;
- PBU-style documents at 1037..1054.

Likely matching signals:

- quoted title;
- PBU identifier such as `ПБУ 19/02`;
- `Положение по бухгалтерскому учету` / `ПБУ` aliases.

This family should have its own model / matcher separate from federal accounting standards.

## Suggested implementation order

1. `presidential_order`
2. `federal_law`
3. `presidential_decree`
4. `code`
5. `rf_law`
6. `fundamentals_of_legislation`
7. `federal_accounting_standard`
8. `accounting_regulation`

The first three families share the strongest common structure and are the best place to design the reusable `number / date / title` representation.
