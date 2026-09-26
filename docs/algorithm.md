# Legal Reference Detector — подробное описание алгоритма

> Этот документ описывает **текущее устройство кода**, а не желаемую будущую архитектуру. Его цель — позволить новому участнику проекта понять pipeline, ответственность модулей, основные эвристики и места расширения без восстановления контекста из истории разработки.

## 1. Что решает проект

Проект извлекает из русского текста ссылки на нормативные документы и возвращает их в унифицированном виде:

```python
LawLink(
    law_id: int,
    article: str | None,
    point_article: str | None,
    subpoint_article: str | None,
)
```

Пример:

```text
В соответствии с пп. 1 п. 1 ст. 374 НК РФ ...
```

превращается в:

```python
LawLink(
    law_id=15,
    article="374",
    point_article="1",
    subpoint_article="1",
)
```

Задача разделена на две принципиально разные части:

1. понять **геометрию ссылки в тексте**: статья, пункт, подпункт, семейство документа, название в кавычках;
2. понять **какой именно документ** имеется в виду и получить его `law_id`.

Это разделение является центральной идеей архитектуры.

---

## 2. Pipeline целиком

Основной facade — `LinksFinalizer`.

```text
raw text
   │
   ▼
TextNormalizer
   │
   ▼
NormalizedText
   │
   ▼
independent regex strategies
   │
   ├── DiscourseCandidateStrategy
   ├── ArticleCandidateStrategy
   ├── PartCandidateStrategy
   ├── PointCandidateStrategy
   ├── SubpointCandidateStrategy
   ├── FamilyCandidateStrategy
   └── QuoteCandidateStrategy
   │
   ▼
all Match objects sorted by text offsets
   │
   ▼
CandidateSegmentor
   │
   ├── invalid Segment ──────────────► diagnostics
   │
   ▼
valid Segment
   │
   ▼
DocumentResolver
   │
   ├── unresolved ──────────────────► diagnostics
   │
   ▼
ResolvedDocument(law_id, family)
   │
   ▼
LinksFinalizer._expand()
   │
   ▼
Cartesian product of structural values
   │
   ▼
deduplication
   │
   ▼
FinalizerResult(links, stats)
```

Важно: стратегии **не пытаются целиком распознать юридическую ссылку одной большой регуляркой**. Каждая стратегия независимо находит только свой тип сигнала. Segmentor затем собирает эти сигналы в кандидаты, а resolver устанавливает конкретный документ.

---

## 3. Нормализация текста

Файлы:

```text
src/links_detector/normalization/
├── models.py
└── normalizer.py
```

`TextNormalizer` намеренно минимален:

```python
NormalizedText(
    original=text,
    lowercase=text.lower(),
)
```

### Почему хранятся две версии

`lowercase` удобен для case-insensitive структурных конструкций:

- `ст. 14`;
- `статьей 30.1`;
- `пункта 3`;
- `подпунктах а, б и с`.

`original` нужен там, где исходный регистр семантически важен, и для сохранения точных offsets.

В частности, семейства документов различают конструкции вроде:

- `Федеральный закон`, где `закон` написан со строчной;
- `Закон`, который является отдельным family `rf_law`.

Поэтому глобально приводить весь pipeline к lowercase нельзя.

### Почему нормализация пока не агрессивная

Offsets `start/end` относятся непосредственно к исходному тексту. Изменение длины строки — например схлопывание пробелов или замена последовательностей символов — разрушило бы соответствие между normalized и original text.

Новые правила нормализации следует добавлять только под конкретный подтверждённый кейс.

---

## 4. Strategy layer

Файлы:

```text
src/links_detector/candidates_segmenter/strategies/
├── discourse_strategy.py
├── structure_strategy.py
├── family_strategy.py
└── quote_strategy.py
```

Стратегии независимы друг от друга. Их задача — найти локальные признаки и вернуть Match-объекты с offsets.

### 4.1. Discourse strategy

Находит вводные конструкции:

- `в соответствии с`;
- `на основании`;
- `руководствуясь`;
- `согласно`;
- `в силу`;
- `предусмотрено`;
- `в порядке, установленном`.

Результат:

```python
DiscourseMatch(start, end, original_text)
```

Discourse marker **не является обязательной частью юридической ссылки**. Валидные ссылки могут существовать без него.

Его основная роль далее — boundary signal для segmentor: новый discourse marker начинает новый кандидат.

---

### 4.2. Structure strategies

Четыре независимые стратегии:

```text
ArticleCandidateStrategy  → ArticleMatch
PartCandidateStrategy     → PartMatch
PointCandidateStrategy    → PointMatch
SubpointCandidateStrategy → SubpointMatch
```

Каждый structural match содержит:

```python
start
end
original_text
values: tuple[str, ...]
```

Примеры:

```text
ст. 14                  → ("14",)
статей 10, 11 и 12      → ("10", "11", "12")
пункта 3.345, 23        → ("3.345", "23")
пункта а                → ("а",)
п. р                    → ("р",)
пп. 4, 5, 6 и 8        → ("4", "5", "6", "8")
подпунктах а, б и с     → ("а", "б", "с")
```

Поддерживаются числовые значения, составные номера через точку, одиночные кириллические буквы и значения в прямых кавычках.

В dataset также присутствует опечатка `пунта б`; она поддерживается намеренно.

#### Как извлекаются values

Regex structural strategy содержит именованную группу:

```text
(?P<values>...)
```

Это принципиально важно. `_extract_values()` применяется **только к этой группе**, а не ко всему `original_text`. Иначе после добавления буквенных значений слово `пункта` само распалось бы на ложные values.

Союз `и` является разделителем списка и исключается из результата.

---

### 4.3. Family strategy

`FamilyCandidateStrategy` определяет **семейство документа**, но не конкретный `law_id`.

Результат:

```python
FamilyMatch(
    start=...,
    end=...,
    original_text=...,
    family="federal_law",
)
```

Текущие families:

| Family | Примеры |
|---|---|
| `code` | `кодекс`, `Кодекс`, `НК`, `ГК`, `КоАП`, `АПК` |
| `presidential_order` | `Распоряжение Президента`, `РП` |
| `federal_law` | `Федеральный закон`, `ФЗ` |
| `presidential_decree` | `Указ Президента`, `Указ` |
| `fundamentals_of_legislation` | `Основы законодательства` |
| `rf_law` | `Закон` |
| `federal_accounting_standard` | `ФСБУ`, полное название |
| `accounting_regulation` | `ПБУ`, `ПОЛОЖЕНИЕ ПО БУХГАЛТЕРСКОМУ УЧЕТУ` |

Короткие имена кодексов не зашиты в FamilyStrategy вручную. Они загружаются из:

```text
law_aliases/families/codes.json
```

и динамически добавляются к pattern семейства `code`.

Family strategy работает по `text.original`, поскольку регистр является частью логики классификации family.

---

### 4.4. Quote strategy

Находит текст внутри:

```text
"..."
«...»
```

и возвращает:

```python
QuoteMatch(
    start=...,
    end=...,
    original_text='«О персональных данных»',
    value="О персональных данных",
)
```

Quote strategy ничего не знает о базе законов. Она лишь сообщает: «здесь есть quoted span». Проверка того, является ли значение названием известного документа, выполняется позже resolver'ом.

Перенос строки внутри quote текущим regex не поддерживается.

---

## 5. CandidateSegmentor

Файл:

```text
src/links_detector/candidates_segmenter/segmenter.py
```

Segmentor получает все независимые matches и сначала сортирует их:

```python
sorted(matches, key=lambda match: (match.start, match.end))
```

После этого один линейный проход собирает их в `Segment`.

### Типы сигналов

Условно:

```text
START:
    DiscourseMatch

STRUCTURE:
    ArticleMatch
    PartMatch
    PointMatch
    SubpointMatch

DOCUMENT:
    FamilyMatch
    QuoteMatch
```

### Границы сегментов

Новый segment начинается, если:

1. встречен новый `DiscourseMatch`;
2. после `FamilyMatch` или `QuoteMatch` начинается новая structural конструкция.

`QuoteMatch` сразу закрывает текущий segment.

`FamilyMatch` сразу segment не закрывает, потому что после family может идти quoted title:

```text
ст. 14 Федерального закона "О персональных данных"
```

### Валидность Segment

Segment считается валидным только если содержит:

```text
хотя бы один STRUCTURE
        AND
(FamilyMatch OR QuoteMatch)
```

То есть:

```text
ст. 14
```

сам по себе недостаточен.

И:

```text
Федеральный закон
```

тоже недостаточен.

Но:

```text
ст. 14 Федерального закона
```

имеет необходимую структуру кандидата, после чего resolver должен установить конкретный документ.

### Почему invalid segments сохраняются

Они не выбрасываются внутри segmentor. Это позволяет различать:

- segmentor не смог сформировать валидного кандидата;
- кандидат был валидным структурно, но resolver не смог установить документ.

Это полезно для диагностики качества pipeline.

### next_start

После построения всех segments каждому назначается `next_start`:

- start следующего segment;
- для последнего — `len(text.original)`.

Resolver использует окно:

```python
text.original[segment.start:segment.next_start]
```

поэтому может искать номер/дату/полное название не только строго внутри последнего Match.

---

## 6. Данные документов

Основная исходная база находится в `law_aliases`.

Для runtime resolver использует компактные family datasets:

```text
law_aliases/families/
├── codes.json
├── structured_acts.json
├── federal_accounting_standards.json
└── accounting_regulations.json
```

Всего текущая классификация охватывает 1055 записей и 8 families.

### codes.json

Для кодексов хранятся:

```text
law_id
name
short_name
```

### structured_acts.json

Сюда входят:

- presidential orders;
- federal laws;
- presidential decrees;
- fundamentals of legislation;
- RF laws.

Основные поля:

```text
law_id
number
date
title
title_unique
```

### federal_accounting_standards.json

Основной идентификатор — title.

### accounting_regulations.json

Хранятся title и PBU identifier. У отдельных записей `pbu` может отсутствовать.

---

## 7. DocumentResolver

Файлы:

```text
src/links_detector/document_resolver/
├── resolver.py
├── code_resolver.py
└── models.py
```

Результат успешного разрешения:

```python
ResolvedDocument(
    law_id=...,
    family=...,
)
```

Resolver вызывается только для валидных segments.

### 7.1. Общая последовательность

Сначала из segment берутся первый `FamilyMatch` и первый `QuoteMatch`.

Если family известна:

1. берутся документы только этой family;
2. если есть quote — сначала выполняется exact normalized title matching;
3. затем применяется family-specific resolution.

Если family не удалось разрешить, но quote существует, выполняется global exact title lookup по всем families.

### 7.2. Локальная нормализация resolver

Для сравнения titles resolver использует:

```text
lowercase
ё → е
collapse whitespace
```

Эта нормализация локальна и не меняет исходный текст/offsets.

### 7.3. Structured families

Для structured acts resolver начинает со всех документов family.

Далее:

1. ищет совпадающий number;
2. если number найден — сужает candidates;
3. ищет date среди оставшихся candidates;
4. если date найден — ещё раз сужает candidates;
5. если остаётся ровно один документ — возвращает его `law_id`;
6. иначе resolution считается неоднозначным и возвращается `None`.

### 7.4. Codes

Кодексы вынесены в отдельный `CodeResolver`.

Причина: family небольшая и стабильная, а русские падежные окончания делают exact matching полного имени слишком хрупким.

Для полных названий используются явные regex patterns:

```text
Арбитражный процессуальный кодекс
Гражданский кодекс
Уголовно-процессуальный кодекс
Кодекс об административных правонарушениях
...
```

Они допускают падежные окончания.

Также поддерживаются short names:

```text
АПК
БК
ГК
ГПК
ЖК
СК
ТК
УИК
УПК
УК
ЛК
НК
ЗК
КоАП
```

После short name допускается `РФ`.

Если найден ровно один уникальный `law_id`, resolution успешен. Несколько разных совпадений считаются неоднозначностью.

### 7.5. ПБУ

Для `accounting_regulation` resolver ищет PBU identifier в search window. Учитываются только записи, где `pbu` присутствует.

### 7.6. ФСБУ

У текущих данных ФСБУ основным discriminating signal является title. Поэтому family marker без подходящего quote сам по себе не даёт конкретный `law_id`.

---

## 8. Finalizer

Файл:

```text
src/links_detector/finalizer/finalizer.py
```

`LinksFinalizer` — facade верхнего уровня.

Публичная операция:

```python
result = LinksFinalizer().extract(text)
```

Внутри она:

1. нормализует text;
2. запускает segmentor;
3. пропускает invalid segments;
4. разрешает valid segments через resolver;
5. раскрывает structural lists;
6. удаляет дубликаты;
7. возвращает links + diagnostics.

---

## 9. Раскрытие списков и Cartesian product

Это важная часть семантики.

Пример:

```text
пп. 4, 5, 6 и 8 п. 1 ст. 14 Федерального закона ...
```

Structural strategies возвращают:

```text
articles  = ("14",)
points    = ("1",)
subpoints = ("4", "5", "6", "8")
```

Finalizer строит Cartesian product и получает четыре `LawLink`.

Другой пример:

```text
подпунктах а, б и с пункта 3.345, 23 в статье 66 НК РФ
```

даёт:

```text
articles  = ("66",)
points    = ("3.345", "23")
subpoints = ("а", "б", "с")
```

Следовательно, создаются 2 × 3 = 6 отдельных ссылок.

Это осознанная семантика проекта: **один point — одна итоговая LawLink**, а не строка `"3.345, 23"` внутри одного поля.

### Part и Point

Текущая target model не имеет отдельного поля `part`.

Поэтому и `PartMatch`, и `PointMatch` записываются в:

```python
LawLink.point_article
```

Это соответствует текущему gold format.

---

## 10. Deduplication

После expansion выполняется:

```python
tuple(dict.fromkeys(expanded))
```

Поскольку `LawLink` — frozen dataclass, объекты hashable.

Таким образом одинаковая ссылка, найденная несколько раз, присутствует в финальном результате один раз, при этом сохраняется порядок первого появления.

---

## 11. Диагностическая статистика

`FinalizerResult` содержит не только links, но и `FinalizerStats`:

```text
total_segments
invalid_segments
resolver_failed
resolved_segments
expanded_segments
unique_links
```

Смысл:

- `total_segments` — сколько segments построил segmentor;
- `invalid_segments` — segments без необходимой комбинации STRUCTURE + DOCUMENT;
- `resolver_failed` — segment структурно валиден, но документ не удалось определить;
- `resolved_segments` — сколько segments получили конкретный law_id;
- `expanded_segments` — сколько resolved segments породили больше одного LawLink;
- `unique_links` — количество итоговых ссылок после deduplication.

Разделение `invalid_segments` и `resolver_failed` специально позволяет понимать, на каком слое возникла ошибка.

---

## 12. Тестирование

Есть два разных уровня проверки.

### 12.1. Unit tests regex strategies

```text
tests/strategies/
├── test_discourse_strategy.py
├── test_family_strategy.py
├── test_quote_strategy.py
└── test_structure_strategy.py
```

Запуск:

```bash
uv run pytest
```

Эти тесты фиксируют известное поведение regex layer:

- морфологические формы;
- сокращения;
- списки;
- числовые и буквенные structural values;
- code aliases;
- регистр family markers;
- прямые и типографские quotes;
- offsets;
- negative cases.

Главная цель — при изменении регулярного выражения немедленно увидеть, не сломалось ли уже поддерживаемое поведение.

На текущем этапе unit tests намеренно сфокусированы именно на strategies. Segmentor/resolver/finalizer пока не являются целью этого набора unit tests.

### 12.2. End-to-end smoke / gold

Главный runner:

```bash
uv run python smoke_tests/smoke_candidates.py 0
```

`DatasetLoader` находит:

```text
dataset/markdown/00_readme_example.md
dataset/gold/00_readme_example.jsonl
```

и сравнивает итоговые `LawLink` как sets:

```text
matched
missing
unexpected
```

Текущая baseline для sample 0:

```text
expected:   34
matched:    34
missing:     0
unexpected:  0
```

Этот пример является regression baseline всего pipeline.

Для dataset files без gold runner всё равно выводит найденные links и META, но автоматического expected comparison нет.

### Рекомендуемый порядок после изменений

```bash
uv run pytest
uv run python smoke_tests/smoke_candidates.py 0
```

Первый запуск проверяет локальные contracts strategies. Второй — их совместную работу с segmentation, resolution и finalization.

---

## 13. Как читать типичную ошибку

Если end-to-end результат неправильный, полезно диагностировать сверху вниз.

### Ошибка structural value

Например потерян `пункта а`.

Проверять:

```text
StructureCandidateStrategy
    ↓
Match.values
```

### Не найдено family

Проверять `FamilyCandidateStrategy`.

Особенно внимательно относиться к регистру: он здесь может иметь семантическое значение.

### Segment invalid

Проверять, присутствуют ли одновременно:

```text
STRUCTURE
+
FamilyMatch/QuoteMatch
```

и не разрезал ли boundary segment раньше времени.

### resolver_failed

Segment уже структурно корректен. Следовательно проблема ниже:

- title matching;
- number/date;
- code resolution;
- PBU identifier;
- неоднозначность candidates.

### Лишнее/неправильное количество LawLink

Если документ разрешён правильно, но число ссылок неверно, проверять:

1. `values` structural matches;
2. Cartesian expansion в finalizer;
3. deduplication.

---

## 14. Важные архитектурные ограничения текущей версии

### Regex layer является эвристическим

Проект не выполняет полноценный морфологический анализ русского языка. Падежные формы покрываются regex patterns и известными вариантами.

### Family detection и document resolution — разные задачи

Нахождение `Федерального закона` ещё не означает, что известен конкретный закон.

Family strategy должна оставаться дешёвым detector layer; конкретный `law_id` — ответственность resolver.

### Quote не означает автоматически legal title

Quote strategy находит любые поддерживаемые кавычки. Только resolver проверяет quote относительно datasets.

### Не вся нормализация должна быть глобальной

Любая preprocessing операция, меняющая длину текста, потенциально ломает offsets. Поэтому нормализацию лучше делать локально там, где она нужна для matching.

### Списки раскрываются только в конце

Strategies должны сохранить найденные structural values, а не самостоятельно создавать несколько LawLink. Cartesian expansion — ответственность finalizer.

---

## 15. Где расширять систему

Если появляется новая форма написания `статья/пункт/подпункт` — расширять `structure_strategy.py` и сразу добавлять regression unit test.

Если появляется новый discourse marker — `discourse_strategy.py`.

Если появляется новый способ обозначить уже существующее family — `family_strategy.py`.

Если появляется новый вид quotes — `quote_strategy.py`.

Если family находится правильно, но не определяется конкретный документ — расширять `document_resolver`, а не family strategy.

Если меняется правило объединения нескольких найденных structural values в output — это уровень `finalizer`.

---

## 16. Практический принцип изменения regex

Regex layer намеренно покрыт unit tests, потому что небольшое изменение общей конструкции может неожиданно изменить десятки форм.

Рабочий цикл:

```text
новый реальный кейс
      ↓
добавить/уточнить unit test
      ↓
минимально изменить strategy
      ↓
uv run pytest
      ↓
end-to-end smoke against gold
```

Не следует расширять regex «на всякий случай» без примера, который требует такого поведения.

---

## 17. Основные директории проекта

```text
src/links_detector/
├── normalization/          # representation original/lowercase
├── candidates_segmenter/
│   ├── strategies/         # independent regex detectors
│   ├── models.py           # Segment and match type aliases
│   └── segmenter.py        # match stream → Segment[]
├── document_resolver/      # Segment → law_id
├── finalizer/              # orchestration + Cartesian expansion
├── models/
│   └── law_link.py         # public result model
└── utils/                  # dataset loader, CLI helpers, paths

law_aliases/
├── law_aliases.json        # source aliases dataset
└── families/               # compact runtime family datasets

dataset/
├── markdown/               # test texts
└── gold/                   # expected LawLink JSONL where available

tests/strategies/           # pytest regression tests for regex strategies
smoke_tests/                # manual/integration/end-to-end diagnostics
docs/                       # project documentation
```

---

## 18. Ключевая ментальная модель

Самый простой способ помнить архитектуру:

```text
Strategies:
    "Что локально написано в тексте?"

Segmentor:
    "Какие локальные признаки относятся к одной ссылке?"

Resolver:
    "Какой именно это документ?"

Finalizer:
    "Какие конкретные LawLink нужно вернуть?"
```

Именно это разделение позволяет расширять regex detection, правила segmentation и способы resolution независимо друг от друга.
