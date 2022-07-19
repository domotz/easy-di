from .resources import Object1, Object2, Object3
from easy_di import injected


class OtherFakeInjectedClass:
    object_1: injected(Object1)
    object_2: injected(Object2, "factory")
    object_3: "injected(Object3)"
    another: 'injected(Object1, "object_1")'
    the_name: "injected(str)"
    bar: "str"

    def foo(self):
        return self.object_1.build()


class Parent:
    a: int

    def __init__(self, a):
        self.a = a


class Child(Parent):
    b: injected(Object1, "object_1")


class Parent2:
    pass


class Child2(Parent2):
    b: injected(Object1, "object_1")
