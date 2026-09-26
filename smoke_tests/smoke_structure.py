from links_detector.candidates_segmenter.strategies.structure_strategy import (
    ArticleCandidateStrategy,
    PartCandidateStrategy,
    PointCandidateStrategy,
    SubpointCandidateStrategy,
)
from links_detector.normalization import TextNormalizer


TEXT = """
Согласно ст. 14 Федерального закона.
В соответствии со статьей 30.1 КоАП РФ.
На основании статей 10, 11 и 12 настоящего закона.

Согласно ч. 1 ст. 12.8 КоАП РФ.
В соответствии с частью 3 статьи 7 Федерального закона.
На основании частей 1, 2 и 4 статьи 15 закона.

Согласно п. 2 ст. 14 Федерального закона.
В силу пункта 3.345 статьи 66 НК РФ.
В соответствии с пунктами 3.2, 4.1 и 7 статьи 12 Федерального закона.

Согласно пп. 1 п. 1 ст. 374 НК РФ.
В соответствии с пп. 4, 5, 6 и 8 п. 1 ст. 14 Федерального закона.
Согласно подпунктам "а", "б" и "в" пункта 2 статьи 12 Федерального закона.
Согласно подпункту 2 пункта "б" статьи 22 Федерального закона.
""".strip()


def print_matches(name: str, matches) -> None:
    print(f"\n{name}")
    print("-" * len(name))

    for match in matches:
        print(f"{match} -> values={match.values}")


def main() -> None:
    text = TextNormalizer().normalize(TEXT)

    print("INPUT")
    print("=====")
    print(TEXT)

    strategies = (
        ("ARTICLES", ArticleCandidateStrategy()),
        ("PARTS", PartCandidateStrategy()),
        ("POINTS", PointCandidateStrategy()),
        ("SUBPOINTS", SubpointCandidateStrategy()),
    )

    for name, strategy in strategies:
        print_matches(name, strategy.find(text))


if __name__ == "__main__":
    main()
