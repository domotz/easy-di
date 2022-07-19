from timeit import timeit
from unittest import TestCase
from unittest.mock import Mock

from easy_di_test.benchmarks.resources import Trivial

from easy_di import DI, di_storage
from easy_di.exceptions import UndefinedResourceException

ACCEPTABLE_OVERHEAD = 1.2


class WithParameter:
    def __init__(self, object_1):
        self.object_1 = object_1


class SameBehaviour:
    def __init__(self):
        try:
            self.object_1 = di_storage.__object_1__
            if di_storage.__object_1_is_factory__:
                self.object_1 = self.object_1()
        except AttributeError as e:
            raise UndefinedResourceException(
                f"`{e.args[0]}` Needed by class {self.__class__.__name__}"
            ) from e


class TestAgainstNoInversionOfControl(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.object_1 = Mock()
        DI.register("object_1", cls.object_1, force=True)

    def test_100000(self):
        self.assertIs(self.object_1, Trivial().object_1)
        param = self.object_1
        time_std = timeit(lambda: WithParameter(param), number=100000)
        time_di = timeit(Trivial, number=100000)
        ratio = time_di / time_std
        self.assertLessEqual(ratio, ACCEPTABLE_OVERHEAD)


class TestAgainstSameBehaviour(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.object_1 = Mock()
        DI.register("object_1", cls.object_1, force=True)

    def test_100000(self):
        self.assertIs(self.object_1, Trivial().object_1)
        time_std = timeit(SameBehaviour, number=100000)
        time_di = timeit(Trivial, number=100000)
        ratio = time_di / time_std
        self.assertLessEqual(ratio, ACCEPTABLE_OVERHEAD)
