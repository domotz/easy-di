from time import sleep
from timeit import timeit
from unittest.mock import Mock

from easy_di import di_init, DI
from easy_di.exceptions import UndefinedResourceException
from easy_di_test.benchmarks.resources import Trivial

di_init()


class WithParameter:
    def __init__(self, object_1):
        self.object_1 = object_1


DI._object_1 = Mock()


class SameBehaviour:
    def __init__(self, *params, **kwargs):
        try:
            self.object_1 = DI._object_1
        except UndefinedResourceException as e:
            raise UndefinedResourceException(
                f"`{e.args[0]}` Needed by class {self.__class__.__name__}"
            ) from e


if __name__ == "__main__":
    param = Mock()
    DI.register("object_1", param)
    samples = []
    for _ in range(1001):
        # time_std = timeit(lambda: WithParameter(param), number=1000)
        time_std = timeit(SameBehaviour, number=1000)
        time_di = timeit(Trivial, number=1000)
        ratio = time_di / time_std
        samples.append(ratio)
    samples = sorted(samples)
    print(samples[0], samples[500], samples[1000], sum(samples) / len(samples))
