from __future__ import annotations

import argparse
import json
import os
import random
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

from links_detector.finalizer import LinksFinalizer


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ALIASES_DIR = PROJECT_ROOT / "law_aliases" / "families"

AUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
BASE_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
MODEL_NAME = "GigaChat-2"
DEFAULT_SCOPE = "GIGACHAT_API_PERS"


@dataclass(frozen=True)
class SampledReference:
    law_id: int
    family: str
    document_form: str
    structure: str
    raw_item: dict[str, Any]


def _load_all_documents() -> list[tuple[str, tuple[str, ...], dict[str, Any]]]:
    documents: list[tuple[str, tuple[str, ...], dict[str, Any]]] = []

    for path in sorted(ALIASES_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        groups = data if isinstance(data, list) else [data]

        for group in groups:
            family = group["family"]
            family_name = family["name"]
            aliases = tuple(family.get("aliases", ()))

            for item in group["items"].values():
                documents.append((family_name, aliases, item))

    return documents


def _choose_document_form(
    family: str,
    aliases: tuple[str, ...],
    item: dict[str, Any],
    rng: random.Random,
) -> str:
    options: list[str] = []

    if family == "code":
        if item.get("short_name"):
            options.append(item["short_name"])
        if item.get("name"):
            options.append(item["name"])

    elif family == "federal_accounting_standard":
        if item.get("fsbu"):
            options.append(f"ФСБУ {item['fsbu']}")
        if item.get("title"):
            options.append(f'"{item["title"]}"')

    elif family == "accounting_regulation":
        if item.get("pbu"):
            options.append(item["pbu"])
        if item.get("title"):
            options.append(f'"{item["title"]}"')

    else:
        number = item.get("number")
        date = item.get("date")
        title = item.get("title")

        if number:
            for alias in aliases:
                options.append(f"{alias} {number}")
                if date:
                    options.append(f"{alias} от {date} {number}")

        if title:
            options.append(f'"{title}"')

    if not options:
        raise ValueError(f"No usable document form for law_id={item['law_id']}")

    return rng.choice(options)


def _choose_structure(rng: random.Random) -> str:
    article = str(rng.randint(1, 250))
    point = str(rng.randint(1, 12))
    part = str(rng.randint(1, 8))
    subpoint = rng.choice(("а", "б", "в", "г", "д"))

    return rng.choice(
        (
            f"статья {article}",
            f"часть {part} статьи {article}",
            f"пункт {point} статьи {article}",
            f'подпункт "{subpoint}" пункта {point} статьи {article}',
        )
    )


def _sample_balanced_references(
    documents: list[tuple[str, tuple[str, ...], dict[str, Any]]],
    count: int,
    rng: random.Random,
) -> list[SampledReference]:
    by_family: dict[str, list[tuple[tuple[str, ...], dict[str, Any]]]] = {}

    for family, aliases, item in documents:
        by_family.setdefault(family, []).append((aliases, item))

    if count > sum(len(items) for items in by_family.values()):
        raise ValueError("Requested more unique documents than available")

    families = list(by_family)
    rng.shuffle(families)

    quotas = {family: 0 for family in families}
    remaining = count

    # First give every family one slot when possible. Singleton families are
    # therefore represented once, but are never oversampled afterwards.
    for family in families:
        if remaining == 0:
            break
        quotas[family] = 1
        remaining -= 1

    # Distribute the remaining slots round-robin over families that still have
    # unused documents. This keeps family counts as even as possible.
    while remaining > 0:
        available = [
            family
            for family in families
            if quotas[family] < len(by_family[family])
        ]
        if not available:
            raise ValueError("Not enough unique documents to satisfy balanced sampling")

        rng.shuffle(available)
        for family in available:
            if remaining == 0:
                break
            quotas[family] += 1
            remaining -= 1

    selected: list[SampledReference] = []
    for family, quota in quotas.items():
        sampled = rng.sample(by_family[family], k=quota)
        for aliases, item in sampled:
            selected.append(
                SampledReference(
                    law_id=item["law_id"],
                    family=family,
                    document_form=_choose_document_form(family, aliases, item, rng),
                    structure=_choose_structure(rng),
                    raw_item=item,
                )
            )

    rng.shuffle(selected)
    return selected


def _build_prompt(references: list[SampledReference]) -> str:
    targets = "\n".join(
        f"{index}. law_id={ref.law_id}; "
        f"структура={ref.structure}; "
        f"представление документа={ref.document_form}"
        for index, ref in enumerate(references, start=1)
    )

    return f"""
Мы тестируем rule-based парсер юридических ссылок. Он НЕ понимает произвольные
юридические формулировки и должен тестироваться только на ссылках строго такого вида:

    <СТРУКТУРА> <ПРЕДСТАВЛЕНИЕ ДОКУМЕНТА>

где <СТРУКТУРА> — одна из форм:
- статья N
- часть N статьи M
- пункт N статьи M
- подпункт "X" пункта N статьи M

а <ПРЕДСТАВЛЕНИЕ ДОКУМЕНТА> — ровно та форма документа, которая дана в TARGETS.

Примеры допустимого формата:
- статья 82 Федерального закона №13-ФЗ
- пункт 6 статьи 84 Федерального закона от 11.11.2003 №138-ФЗ
- подпункт "в" пункта 12 статьи 17 ФЗ от 29.12.2020 №472-ФЗ
- часть 2 статьи 91 Семейного кодекса
- пункт 10 статьи 85 "УЧЕТ ОПЕРАЦИЙ СИСТЕМЫ КАЗНАЧЕЙСКИХ ПЛАТЕЖЕЙ"

Примеры НЕДОПУСТИМОГО формата:
- Федеральный закон №13-ФЗ, в частности статья 82
- Федеральный закон №13-ФЗ (статья 82)
- статья 82 указанного закона
- Указ №504, согласно которому подпункт "а" пункта 4 статьи 104...
- статья 82 документа "..."
- статья 82 Федерального закона "...", если в TARGETS было только название в кавычках

Напиши один естественный фрагмент русского юридического текста длиной примерно
2-5 абзацев. В тексте должны встретиться ВСЕ заданные ниже юридические ссылки,
каждая ровно один раз и строго в описанном выше формате.

TARGETS:
{targets}

Правила:
- Не перечисляй ссылки списком: вплети их в связный юридический текст.
- Для каждой ссылки обязательно сохрани заданный law_id только как скрытую цель.
  НИКОГДА не выводи law_id, строки вида "(law_id=...)" или любые другие служебные
  идентификаторы в готовом тексте.
- Используй представление документа ИМЕННО В ТОМ ВИДЕ, как оно дано в TARGETS.
  Воспроизводи document form буквально: не меняй регистр, кавычки, порядок слов,
  номер, дату, сокращение и написание.
  Если дано сокращение вроде "ФЗ", "УК", "ПБУ", "ФСБУ", не заменяй его полной формой.
  Если представление документа дано только названием в кавычках, используй ровно
  это название в тех же кавычках и НЕ добавляй перед ним другой тип акта
  ("постановление", "указ", "федеральный закон" и т.п.).
  НЕ склоняй и НЕ переформулируй название документа.
- Словесные формы самой структуры ссылки можно естественно склонять и согласовывать
  с предложением.
- Используй указанную структуру ссылки, но можешь естественно склонять слова
  "статья", "часть", "пункт", "подпункт".
- Структура ссылки и указанное представление документа должны образовывать одну
  явную локальную юридическую ссылку в одном предложении и находиться рядом друг
  с другом. Не разделяй их длинным промежуточным текстом.
- ОБЯЗАТЕЛЬНО ставь структуру ссылки ПЕРЕД представлением документа:
  например, "пункт 6 статьи 63 Лесного кодекса", а не
  "Лесной кодекс, в частности пункт 6 статьи 63".
- Не заменяй указанное представление документа анафорическими выражениями вроде
  "данный нормативный акт", "данный закон", "указанный кодекс", "настоящий акт"
  и т.п. Например, если задано "пункт 6 статьи 63 | Лесной кодекс", в тексте
  должна явно присутствовать конструкция вроде "пункт 6 статьи 63 Лесного кодекса".
- Разрешены обычные вариации пунктуации, регистра и пробелов, характерные для
  реального текста.
- Добавь вокруг ссылок нейтральный юридический шум, чтобы текст не выглядел
  синтетическим, но НЕ добавляй никаких дополнительных юридических ссылок, которых
  нет в TARGETS.
- Не используй Markdown вообще: никаких *, **, _, #, backticks, markdown-заголовков
  или списков.
- Не выводи law_id, target, "код target", "закон №<law_id>" и любые другие
  служебные идентификаторы или пояснения.
- Не объясняй задачу и не добавляй комментарии.
- Верни только готовый текст.

ФИНАЛЬНАЯ ПРОВЕРКА ПЕРЕД ОТВЕТОМ:
Для КАЖДОГО TARGET мысленно проверь, что в готовом тексте буквально присутствует
одна локальная конструкция вида

    <СТРУКТУРА> <ПРЕДСТАВЛЕНИЕ ДОКУМЕНТА>

именно в таком порядке: сначала структура, сразу после нее документ.
Не ставь документ перед структурой, не переноси структуру в скобки после документа,
не заменяй документ словами "данный закон", "указанный акт" и не придумывай другой
тип или номер документа. Убедись также, что document form воспроизведен буквально,
без склонения, изменения кавычек или регистра, в тексте нет Markdown, law_id и нет
дополнительных юридических ссылок вне TARGETS. Если хотя бы один TARGET не
соответствует этому шаблону, исправь текст до отправки.
""".strip()


def get_access_token(auth_key: str, scope: str) -> str:
    response = requests.post(
        AUTH_URL,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "RqUID": str(uuid.uuid4()),
            "Authorization": f"Basic {auth_key}",
        },
        data={"scope": scope},
        verify=False,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def ask_model(
    access_token: str,
    prompt: str,
    *,
    model: str,
    temperature: float,
    max_tokens: int,
) -> str:
    response = requests.post(
        BASE_URL,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
        verify=False,
        timeout=90,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


def _print_result(run_index: int, references: list[SampledReference], text: str) -> None:
    result = LinksFinalizer().extract(text)

    print(f"\n{'=' * 24} RUN {run_index} {'=' * 24}")
    print("\nTARGETS:")
    for ref in references:
        print(
            f"- law_id={ref.law_id} | family={ref.family} | "
            f"{ref.structure} | {ref.document_form}"
        )

    print("\nGENERATED TEXT:\n")
    print(text)

    print("\nDETECTED:")
    if result.links:
        for link in result.links:
            print(f"- {link}")
    else:
        print("- <no unambiguous links>")

    print("\nAMBIGUOUS:")
    if result.ambiguous:
        for item in result.ambiguous:
            print(f"- {item}")
    else:
        print("- <none>")

    detected_ids = {link.law_id for link in result.links}
    for item in result.ambiguous:
        detected_ids.update(link.law_id for link in item.candidates)

    expected_ids = {ref.law_id for ref in references}
    print("\nEXPECTED law_ids:                    ", sorted(expected_ids))
    print("DETECTED law_ids (exact + ambiguous):", sorted(detected_ids))
    print("MISSED law_ids:                      ", sorted(expected_ids - detected_ids))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate synthetic legal text with GigaChat and immediately run LinksFinalizer."
    )
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--references", type=int, default=3)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--model", default=MODEL_NAME)
    parser.add_argument("--scope", default=os.getenv("GIGACHAT_SCOPE", DEFAULT_SCOPE))
    parser.add_argument("--temperature", type=float, default=0.9)
    parser.add_argument("--max-tokens", type=int, default=1200)
    args = parser.parse_args()

    if args.runs < 1:
        raise SystemExit("--runs must be >= 1")
    if args.references < 1:
        raise SystemExit("--references must be >= 1")

    documents = _load_all_documents()
    total_references = args.runs * args.references
    if total_references > len(documents):
        raise SystemExit(
            "runs * references is larger than the number of available documents"
        )

    auth_key = os.getenv("GIGACHAT_AUTH_KEY")
    if not auth_key:
        auth_key = input("GigaChat AUTH_KEY: ").strip()

    access_token = get_access_token(auth_key, args.scope)
    rng = random.Random(args.seed)
    reference_pool = _sample_balanced_references(
        documents,
        total_references,
        rng,
    )

    family_counts: dict[str, int] = {}
    for ref in reference_pool:
        family_counts[ref.family] = family_counts.get(ref.family, 0) + 1

    print("\nBALANCED SAMPLE BY FAMILY:")
    for family, family_count in sorted(family_counts.items()):
        print(f"- {family}: {family_count}")

    for run_index in range(1, args.runs + 1):
        start = (run_index - 1) * args.references
        end = start + args.references
        references = reference_pool[start:end]
        prompt = _build_prompt(references)
        generated = ask_model(
            access_token,
            prompt,
            model=args.model,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
        )
        _print_result(run_index, references, generated)


if __name__ == "__main__":
    main()
