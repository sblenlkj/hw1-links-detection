from links_detector.candidates_segmenter.segmenter import CandidateSegmentor
from links_detector.normalization import TextNormalizer


TEXT = """
Согласно п. 2 ст. 14 Федерального закона «О персональных данных».
Статья 15 Федерального закона применяется отдельно.
Согласно ст. 20 «О государственной регистрации недвижимости».
Согласно Федеральному закону «О связи».
В тексте случайно упомянут ст. 99 без документа.
Согласно ч. 1 ст. 12.8 КоАП.
""".strip()


def main() -> None:
    text = TextNormalizer().normalize(TEXT)
    segmentor = CandidateSegmentor()

    print("INPUT")
    print("=====")
    print(TEXT)

    print("\nSEGMENTS")
    print("========")

    for index, segment in enumerate(segmentor.segment(text), start=1):
        print(
            f"\n#{index}: valid={segment.valid} "
            f"start={segment.start} end={segment.end} "
            f"next_start={segment.next_start}"
        )

        for match in segment.matches:
            print(f"  {type(match).__name__}: {match}")


if __name__ == "__main__":
    main()
