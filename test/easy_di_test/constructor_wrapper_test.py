import unittest
from unittest.mock import Mock

from easy_di.injection import ConstructorWrapper, DiClassInjector, InjectionWrapper


# pylint: disable=protected-access
class ConstructorWrapperTestCase(unittest.TestCase):
    def test_assemble_code_no_constructor(self):
        requirements = {"a": InjectionWrapper(str, None)}
        testing = ConstructorWrapper()

        code = testing._assemble_code(requirements, object.__init__)
        self.assertEqual(
            """def injected_constructor(self, *params, **kwargs):
    try:
        self.a = di_storage.__a__
        if di_storage.__a_is_factory__:
           self.a = self.a()
    except AttributeError as e:
        raise UndefinedResourceException(
              f'`{e.args[0]}` Needed by class {self.__class__.__name__}') from e
""",
            code,
        )

    def test_assemble_code_override_constructor(self):
        requirements = {
            "a": InjectionWrapper(str, None),
            "b": InjectionWrapper(str, "the_b"),
        }
        testing = ConstructorWrapper()

        code = testing._assemble_code(requirements, Mock())
        self.assertEqual(
            """def injected_constructor(self, *params, **kwargs):
    try:
        self.a = di_storage.__a__
        if di_storage.__a_is_factory__:
           self.a = self.a()
        self.b = di_storage.__the_b__
        if di_storage.__the_b_is_factory__:
           self.b = self.b()
    except AttributeError as e:
        raise UndefinedResourceException(
              f'`{e.args[0]}` Needed by class {self.__class__.__name__}') from e
    constructor(self, *params, **kwargs)
""",
            code,
        )

    def test_assemble_call_super(self):
        requirements = {
            "a": InjectionWrapper(str, None),
            "b": InjectionWrapper(str, "the_b"),
        }
        testing = ConstructorWrapper()

        code = testing._assemble_code(requirements, DiClassInjector.call_parent)
        self.assertEqual(
            """def injected_constructor(self, *params, **kwargs):
    try:
        self.a = di_storage.__a__
        if di_storage.__a_is_factory__:
           self.a = self.a()
        self.b = di_storage.__the_b__
        if di_storage.__the_b_is_factory__:
           self.b = self.b()
    except AttributeError as e:
        raise UndefinedResourceException(
              f'`{e.args[0]}` Needed by class {self.__class__.__name__}') from e
    super(class_, self).__init__(*params, **kwargs)
""",
            code,
        )
