from .models import NormalizedText


class TextNormalizer:
    """First preprocessing layer.

    Keep the first version intentionally small. More normalization rules should
    be added only when a concrete downstream case needs them.
    """

    def normalize(self, text: str) -> NormalizedText:
        return NormalizedText(
            original=text,
            lowercase=text.lower(),
        )
