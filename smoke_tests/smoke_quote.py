from links_detector.candidates_segmenter.strategies.quote_strategy import (
    QuoteCandidateStrategy,
)
from links_detector.normalization import TextNormalizer


TEXT = """
Федеральный закон «О персональных данных» устанавливает требования.
Федеральный закон "О государственной регистрации недвижимости" применяется в данном случае.
В тексте также встречается обычная фраза без кавычек.
ПБУ 19/02 «УЧЕТ ФИНАНСОВЫХ ВЛОЖЕНИЙ» регулирует порядок учета.
""".strip()


def main() -> None:
    text = TextNormalizer().normalize(TEXT)
    strategy = QuoteCandidateStrategy()

    print("INPUT")
    print("=====")
    print(TEXT)

    print("\nQUOTES")
    print("------")

    for match in strategy.find(text):
        print(match)


if __name__ == "__main__":
    main()
