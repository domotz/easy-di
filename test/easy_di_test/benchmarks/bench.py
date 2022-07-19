from timeit import timeit
from unittest.mock import Mock

from easy_di_test.benchmarks.resources import Trivial

from easy_di import DI, di_init, di_storage
from easy_di.exceptions import UndefinedResourceException

di_init()


class WithParameter:
    def __init__(self, object_1):
        self.object_1 = object_1


class SameBehaviour:
    def __init__(self, *params, **kwargs):
        try:
            self.object_1 = di_storage.__object_1__
            if di_storage.__object_1_is_factory__:
                self.object_1 = self.object_1()
        except AttributeError as e:
            raise UndefinedResourceException(
                f"`{e.args[0]}` Needed by class {self.__class__.__name__}"
            ) from e


if __name__ == "__main__":
    param = Mock()
    DI.register("object_1", param)
    samples = []
    for _ in range(1001):
        time_std = timeit(lambda: WithParameter(param), number=100000)
        # time_std = timeit(SameBehaviour, number=1000)
        time_di = timeit(Trivial, number=100000)
        ratio = time_di / time_std
        samples.append(ratio)
        if _ % 100 == 0:
            print(_ / 10)
        else:
            print(".", end="")
    print()
    samples = sorted(samples)
    print(samples[0], samples[500], samples[1000], sum(samples) / len(samples))
    # 0.5126389719370664 1.1142558579656041 1.7976765997944888 1.113755149241448
    # avg and median are quite similar, less than 12% overhead with one parameter
    # by disabling the factory check, we can reduce the overhead to 0 (+/- 1.5%):
    # 0.5239752336705583 0.9968740531260165 2.2677320813336457 1.0145659893103876
