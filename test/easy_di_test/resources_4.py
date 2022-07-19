from __future__ import annotations

from .resources import Object1, Object2, Object3
from easy_di import injected


class Base:
    a: injected(Object2, "factory")


class Child(Base):
    b: injected(Object1, "object_1")
    value = 0

    def __init__(self, k):
        super().__init__()
        self.__class__.value += 1
        self.k = k


class GranChild(Child):
    c: injected(Object3, "object_3")


class GrandGrandChild(GranChild):
    d: injected(Object3, "object_3")
