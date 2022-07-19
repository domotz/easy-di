from __future__ import annotations
from easy_di import injected

from .resources import Object1


class SelfReferencing:
    b: injected(Object1, "object_1")

    @classmethod
    def build(cls) -> SelfReferencing:
        ret = cls()
        return ret
