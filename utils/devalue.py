"""解析 Nuxt/Vue SSR 中常见的 devalue (dehydrated) JSON 格式."""

from __future__ import annotations

import json


def parse_devalue(text: str) -> object:
    """将 Nuxt/Pinia 的 dehydrated state 数组还原为 Python 对象.

    格式示例: [[\"ShallowReactive\",1],{\"data\":2,...},...]
    其中整数表示对数组其他索引的引用, [\"ShallowReactive\",N] 为包装类型.
    """
    text = text.strip().rstrip(";")
    arr = json.loads(text)

    def revive(idx: int) -> object:
        val = arr[idx]
        # 包装类型解引用
        if (
            isinstance(val, list)
            and len(val) == 2
            and isinstance(val[0], str)
            and isinstance(val[1], int)
        ):
            return revive(val[1])
        if isinstance(val, dict):
            new: dict = {}
            for k, v in val.items():
                new[k] = (
                    revive(v)
                    if isinstance(v, int) and 0 < v < len(arr)
                    else v
                )
            return new
        if isinstance(val, list):
            return [
                revive(i) if isinstance(i, int) and 0 < i < len(arr) else i
                for i in val
            ]
        return val

    # 根对象通常位于索引 1 (索引 0 为类型标记)
    return revive(1)
