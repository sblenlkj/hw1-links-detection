from __future__ import annotations

import re


# Explicit patterns are intentional here: the code family is small and stable,
# while Russian case endings make exact string matching too brittle.
_CODE_PATTERNS: tuple[tuple[int, re.Pattern[str]], ...] = (
    (0, re.compile(r"(?<!\w)арбитражн\w{0,5}\s+процессуальн\w{0,5}\s+кодекс\w{0,5}(?!\w)", re.IGNORECASE)),
    (1, re.compile(r"(?<!\w)бюджетн\w{0,5}\s+кодекс\w{0,5}(?!\w)", re.IGNORECASE)),
    (2, re.compile(r"(?<!\w)водн\w{0,5}\s+кодекс\w{0,5}(?!\w)", re.IGNORECASE)),
    (3, re.compile(r"(?<!\w)воздушн\w{0,5}\s+кодекс\w{0,5}(?!\w)", re.IGNORECASE)),
    (4, re.compile(r"(?<!\w)градостроительн\w{0,5}\s+кодекс\w{0,5}(?!\w)", re.IGNORECASE)),
    (5, re.compile(r"(?<!\w)гражданск\w{0,5}\s+кодекс\w{0,5}(?!\w)", re.IGNORECASE)),
    (6, re.compile(r"(?<!\w)гражданск\w{0,5}\s+процессуальн\w{0,5}\s+кодекс\w{0,5}(?!\w)", re.IGNORECASE)),
    (7, re.compile(r"(?<!\w)жилищн\w{0,5}\s+кодекс\w{0,5}(?!\w)", re.IGNORECASE)),
    (8, re.compile(r"(?<!\w)семейн\w{0,5}\s+кодекс\w{0,5}(?!\w)", re.IGNORECASE)),
    (9, re.compile(r"(?<!\w)таможенн\w{0,5}\s+кодекс\w{0,5}(?!\w)", re.IGNORECASE)),
    (10, re.compile(r"(?<!\w)трудов\w{0,5}\s+кодекс\w{0,5}(?!\w)", re.IGNORECASE)),
    (11, re.compile(r"(?<!\w)уголовно-исполнительн\w{0,5}\s+кодекс\w{0,5}(?!\w)", re.IGNORECASE)),
    (12, re.compile(r"(?<!\w)уголовно-процессуальн\w{0,5}\s+кодекс\w{0,5}(?!\w)", re.IGNORECASE)),
    (13, re.compile(r"(?<!\w)уголовн\w{0,5}\s+кодекс\w{0,5}(?!\w)", re.IGNORECASE)),
    (14, re.compile(r"(?<!\w)лесн\w{0,5}\s+кодекс\w{0,5}(?!\w)", re.IGNORECASE)),
    (15, re.compile(r"(?<!\w)налогов\w{0,5}\s+кодекс\w{0,5}(?!\w)", re.IGNORECASE)),
    (16, re.compile(r"(?<!\w)земельн\w{0,5}\s+кодекс\w{0,5}(?!\w)", re.IGNORECASE)),
    (17, re.compile(r"(?<!\w)кодекс\w{0,5}(?:\s+(?:Российск\w{0,5}\s+Федераци\w{0,5}|России|РФ))?\s+об\s+административн\w{0,5}\s+правонарушени\w{0,5}(?!\w)", re.IGNORECASE)),
    (18, re.compile(r"(?<!\w)кодекс\w{0,5}\s+административн\w{0,5}\s+судопроизводств\w{0,5}(?!\w)", re.IGNORECASE)),
    (19, re.compile(r"(?<!\w)кодекс\w{0,5}\s+внутренн\w{0,5}\s+водн\w{0,5}\s+транспорт\w{0,5}(?!\w)", re.IGNORECASE)),
    (20, re.compile(r"(?<!\w)кодекс\w{0,5}\s+торгов\w{0,5}\s+мореплавани\w{0,5}(?!\w)", re.IGNORECASE)),
)

_SHORT_NAMES: tuple[tuple[int, str], ...] = (
    (0, "АПК"),
    (1, "БК"),
    (5, "ГК"),
    (6, "ГПК"),
    (7, "ЖК"),
    (8, "СК"),
    (10, "ТК"),
    (11, "УИК"),
    (12, "УПК"),
    (13, "УК"),
    (14, "ЛК"),
    (15, "НК"),
    (16, "ЗК"),
    (17, "КоАП"),
)


_WINDOW = 120


class CodeResolver:
    def resolve(self, text: str, anchor_start: int, anchor_end: int) -> int | None:
        window_start = max(0, anchor_start - _WINDOW)
        window = text[window_start:anchor_end + _WINDOW]
        start = anchor_start - window_start
        end = anchor_end - window_start

        spans: list[tuple[int, int, int]] = []

        for law_id, pattern in _CODE_PATTERNS:
            for match in pattern.finditer(window):
                spans.append((match.start(), match.end(), law_id))

        for law_id, short_name in _SHORT_NAMES:
            for match in re.finditer(
                rf"(?<!\w){re.escape(short_name)}(?:\s+РФ)?(?!\w)",
                window,
                re.IGNORECASE,
            ):
                spans.append((match.start(), match.end(), law_id))

        overlapping = [
            span for span in spans
            if span[0] < end and start < span[1]
        ]
        if not overlapping:
            return None

        longest = max(span[1] - span[0] for span in overlapping)
        law_ids = {
            law_id for span_start, span_end, law_id in overlapping
            if span_end - span_start == longest
        }
        if len(law_ids) == 1:
            return next(iter(law_ids))

        return None
