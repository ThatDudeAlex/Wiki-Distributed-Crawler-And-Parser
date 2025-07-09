from typing import Any


class DotDict(dict):
    def __init__(self, d: dict[str, Any]):
        for k, v in d.items():
            if isinstance(v, dict):
                v = DotDict(v)
            elif isinstance(v, list):
                v = [DotDict(i) if isinstance(i, dict) else i for i in v]
            self[k] = v

    def __getattr__(self, attr: str):
        try:
            return self[attr]
        except KeyError:
            raise AttributeError(attr)

    def __setattr__(self, key: str, value: Any):
        self[key] = value

    def __delattr__(self, key: str):
        del self[key]
