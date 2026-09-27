from __future__ import annotations


class TestTextBuilder:
    """Build one noisy document from hand-written legal-reference fragments."""

    _NOISE = (
        "Привет, это обычный текст без юридического смысла.",
        "Пока, здесь просто несколько лишних слов, точек и запятых.",
        "Ещё немного произвольного текста вокруг ссылки.",
        "Обычная фраза, которая не должна влиять на результат.",
    )

    @classmethod
    def build(cls, references: list[str]) -> str:
        parts = [cls._NOISE[0]]

        for index, reference in enumerate(references):
            parts.append(reference)
            parts.append(cls._NOISE[(index + 1) % len(cls._NOISE)])

        return " ".join(parts)
