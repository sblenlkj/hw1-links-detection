from links_detector.candidates_segmenter.segmenter import CandidateSegmentor
from links_detector.document_resolver import DocumentResolver
from links_detector.normalization import TextNormalizer


TEXT = """
Согласно ст. 1 Федерального закона № 127-ФЗ от 07.06.2025.
В соответствии со ст. 2 Федерального закона «О налоге на сверхприбыль».
Согласно ст. 3 ПБУ 19/02 «УЧЕТ ФИНАНСОВЫХ ВЛОЖЕНИЙ».
Согласно ст. 4 Арбитражного процессуального кодекса.
В соответствии со статьей 5 Бюджетного кодекса.
Согласно статье 6 Гражданскому процессуальному кодексу.
На основании ст. 7 Уголовно-процессуального кодекса.
В силу статьи 8 Кодекса административного судопроизводства.
Согласно ст. 9 Кодексу торгового мореплавания.
Согласно ст. 12.8 КоАП.
В соответствии со статьей 15 ГК РФ.
На основании ст. 125 АПК.
""".strip()


def main() -> None:
    text = TextNormalizer().normalize(TEXT)
    segmentor = CandidateSegmentor()
    resolver = DocumentResolver()

    print("INPUT")
    print("=====")
    print(TEXT)

    print("\nRESOLUTION")
    print("==========")

    segments = segmentor.segment(text)

    for index, segment in enumerate(segments, start=1):
        resolved = resolver.resolve(segment, text)

        print(
            f"\n#{index}: valid={segment.valid} "
            f"start={segment.start} end={segment.end} "
            f"next_start={segment.next_start}"
        )

        for match in segment.matches:
            print(f"  {type(match).__name__}: {match}")

        if not resolved:
            print("  -> unresolved")
        elif len(resolved) == 1:
            document = resolved[0]
            print(
                f"  -> law_id={document.law_id} "
                f"family={document.family}"
            )
        else:
            candidates = ", ".join(str(document.law_id) for document in resolved)
            print(f"  -> ambiguous: candidates={candidates}")


if __name__ == "__main__":
    main()
