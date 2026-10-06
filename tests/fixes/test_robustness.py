import pytest

from links_detector.finalizer import LinksFinalizer


@pytest.fixture(scope="module")
def finalizer() -> LinksFinalizer:
    return LinksFinalizer()


@pytest.mark.parametrize(
    "text",
    [
        "",
        " ",
        "\n\t   \n",
        "Обычный текст без юридических ссылок.",
        "🙂 🚀 ⚖️ 中文 العربية עברית",
        "ст.",
        "ст. 10",
        "п. 1 ст.",
        "пп. а п. 2 ст.",
        "ФЗ",
        "ФЗ №",
        "ФЗ №abc",
        "Закон РФ №",
        'Федеральный закон "',
        'ст. 10 Федерального закона "незакрытая кавычка',
        "ст. 9999999999999999999999999999999999999999 ФЗ №999999999999-ФЗ",
        "ст. ст. ст. ст. ст. 10 ФЗ №127-ФЗ",
        "№ № № № № ст. п. пп. ч.",
    ],
)
def test_finalizer_does_not_crash_on_malformed_or_irrelevant_text(
    finalizer: LinksFinalizer,
    text: str,
) -> None:
    result = finalizer.extract(text)

    assert result is not None
    assert isinstance(result.links, tuple)
    assert isinstance(result.ambiguous, tuple)


def test_finalizer_handles_large_text_without_legal_references(
    finalizer: LinksFinalizer,
) -> None:
    text = ("Обычный текст без юридических ссылок. " * 10_000).strip()

    result = finalizer.extract(text)

    assert result.links == ()
    assert result.ambiguous == ()


def test_finalizer_handles_many_repeated_valid_references(
    finalizer: LinksFinalizer,
) -> None:
    text = " ".join("ст. 105 УК РФ." for _ in range(1_000))

    result = finalizer.extract(text)

    # Finalizer deduplicates identical unambiguous LawLinks.
    assert len(result.links) == 1
    assert result.ambiguous == ()
