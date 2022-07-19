from __future__ import annotations

from easy_di import injected
from .resources import Object2


class Base:
    foo: injected(Object2)
