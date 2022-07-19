from easy_di import injected


class Object1:
    def build(self):
        print("Builds an object")

    def prova(self):
        return 1


class Object2:
    def __init__(self, param: int):
        self.param = param

    def build(self):
        print(f"Builds an object with param {self.param}")


class Object3(Object1):
    def __init__(self):
        self.a = "A"


class FakeInjectedClass:
    object_1: injected(Object1)
    object_2: injected(Object2, "factory")
    object_3: injected(Object3)
    key: int

    def __init__(self, key):
        self.key = key

    def foo(self):
        return self.object_1.prova()
