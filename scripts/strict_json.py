"""Чтение JSON, в котором повторяющиеся ключи — ошибка, а не молчаливая перезапись.

Файлы слоёв ключуются по id записи. Стандартный `json.loads` при повторе ключа
оставляет последнее значение, и первый блок пропадает без следа: по ошибке
приписанный второй раз id стёр бы прежнюю склейку, правку или подпись.
"""

from __future__ import annotations

import json


def loads_unique(text: str, what: str):
    """`what` — о чём файл, в родительном падеже после «в»: «в подписях повторяются ключи»."""
    def reject_repeats(pairs: list[tuple[str, object]]) -> dict:
        keys = [key for key, _ in pairs]
        repeated = sorted({key for key in keys if keys.count(key) > 1})
        if repeated:
            raise ValueError(f'в {what} повторяются ключи: {repeated}')
        return dict(pairs)

    return json.loads(text, object_pairs_hook=reject_repeats)
