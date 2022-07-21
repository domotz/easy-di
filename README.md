# Easy-DI

**Easy-DI** is an easy to use Dependency Injection library.

Easy-DI allows you to implement the [Dependency Injection](https://en.wikipedia.org/wiki/Dependency_injection) pattern
and manage the complexity of your Python applications.

## Installing Easy-DI and Supported Versions

Easy-DI is available on PyPI:

```console
$ python -m pip install easy-dependency-injection
```

Easy-DI officially supports Python 3.8+.

## Key characteristics

* Lightweight: the added overhead is comparable to accessing a module's constants
* `mypy`-friendly: allows your IDE to infer the type of injected resources and help you with auto-complete and type hinting
* Does one thing, does it well: it's just a dependency injection library.
* Not invasive: you won't have to rewrite your application to use it; you can start taking advantage of the inversion 
  of control gradually
* Test-friendly: easy to integrate in your unit tests.

## Known limitations

* Only classes can be injected: no functions, no modules
* Not tested with metaclasses
* Performances decrease linearly with the number of injected resources


## Example

```python
from easy_di import DI, inject, injected


class Swallow:
    velocity: injected(str)

    def answer(self):
        return f"My airspeed velocity is {self.velocity}"

# this is needed only because the Swallow class is in the __main__ module,
# more realistic scenarios won't need the `inject` function call
inject(__name__)

if __name__ == "__main__":
    DI.register("velocity", "24 miles per hour")
    print(Swallow().answer())

```