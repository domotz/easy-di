import unittest
from unittest.mock import Mock


from easy_di.injection import InjectionWrapper, ConstructorWrapper, DiClassInjector


# pylint: disable=protected-access
class ConstructorWrapperTestCase(unittest.TestCase):
    def test_assemble_code(self):
        requirements = {
            "a": InjectionWrapper(str, None),
            "b": InjectionWrapper(str, "the_b"),
        }
        testing = ConstructorWrapper()

        code = testing._assemble_code(requirements, Mock())
        self.assertEqual(
            """def injected_constructor(self, *params, **kwargs):
    try:
        self.a = DI.get('a')
        self.b = DI.get('the_b')
    except UndefinedResourceException as e:
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
        self.a = DI.get('a')
        self.b = DI.get('the_b')
    except UndefinedResourceException as e:
        raise UndefinedResourceException(
              f'`{e.args[0]}` Needed by class {self.__class__.__name__}') from e
    super(class_, self).__init__(*params, **kwargs)
""",
            code,
        )
