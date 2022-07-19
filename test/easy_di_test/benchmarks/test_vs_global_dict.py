from timeit import timeit
from unittest import TestCase
from unittest.mock import Mock

from easy_di import DI
from easy_di.exceptions import UndefinedResourceException
from easy_di_test.benchmarks.resources import Trivial

ACCEPTABLE_OVERHEAD = 2.2


class WithParameter:
    def __init__(self, object_1):
        self.object_1 = object_1


class SameBehaviour:
    def __init__(self):
        try:
            self.object_1 = DI.get("object_1")
        except UndefinedResourceException as e:
            raise UndefinedResourceException(
                f"`{e.args[0]}` Needed by class {self.__class__.__name__}"
            ) from e


class TestAgainstNoInversionOfControl(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.object_1 = Mock()
        DI.cleanup()
        DI.register("object_1", cls.object_1)

    def test_100000(self):
        self.assertIs(self.object_1, Trivial().object_1)
        param = self.object_1
        time_std = timeit(lambda: WithParameter(param), number=100000)
        time_di = timeit(Trivial, number=100000)
        ratio = time_di / time_std
        self.assertLessEqual(time_std, time_di)
        self.assertLessEqual(ratio, ACCEPTABLE_OVERHEAD)


class TestAgainstSameBehaviour(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.object_1 = Mock()
        DI.cleanup()
        DI.register("object_1", cls.object_1)

    def test_100000(self):
        self.assertIs(self.object_1, Trivial().object_1)
        time_std = timeit(SameBehaviour, number=100000)
        time_di = timeit(Trivial, number=100000)
        ratio = time_di / time_std
        self.assertLessEqual(time_std, time_di)
        self.assertLessEqual(ratio, 1.1)
