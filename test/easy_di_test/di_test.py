__author__ = "Iacopo Papalini <iacopo@domotz.com>"

from unittest import TestCase
from unittest.mock import Mock
from easy_di import DI, di_init
from easy_di.exceptions import UndefinedResourceException, DuplicateResourceException
from .resources import Object2, Object1, FakeInjectedClass, Object3


class Object4(Object3):
    def __init__(self):
        super().__init__()
        self.b = "B"


class InjectionTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        di_init()
        cls.mock_factory = Mock()
        cls.object_1 = Object1()
        DI.register("object_1", cls.object_1)
        DI.register("factory", cls.mock_factory, is_factory=True)
        DI.register("object_3", Object3())
        DI.register("object_4", Object4())
        DI.register("the_name", "Brian")

    def test_instantiate(self):
        testing = FakeInjectedClass(3)

        self.assertEqual(3, testing.key)
        self.assertEqual("A", testing.object_3.a)
        self.assertIsInstance(testing.object_1, Object1)
        self.assertIs(testing.object_2, self.mock_factory.return_value)

    def test_get(self):
        self.assertEqual("A", DI.get("object_4").a)

    def test_import(self):
        from .resources_2 import OtherFakeInjectedClass

        testing = OtherFakeInjectedClass()

        self.assertEqual("A", testing.object_3.a)
        self.assertIsInstance(testing.object_1, Object1)
        self.assertIs(testing.object_2, self.mock_factory.return_value)
        self.assertIs(testing.another, self.object_1)
        with self.assertRaises(AttributeError):
            _ = testing.bar

    def test_parent_is_not_injected(self):
        from .resources_2 import Parent, Child

        p = Parent(1)
        self.assertIs(1, p.a)
        with self.assertRaises(AttributeError):
            _ = p.b

        c = Child(1)
        self.assertIs(1, c.a)
        self.assertIsNotNone(c.b)
        self.assertIsNot(Parent.__init__, Child.__init__)

    def test_parent_is_not_injected_2(self):
        from .resources_2 import Parent2, Child2

        p = Parent2()
        with self.assertRaises(AttributeError):
            _ = p.b

        c = Child2()
        self.assertIsNotNone(c.b)
        self.assertIsNot(Parent2.__init__, Child2.__init__)

    def test_self_referencing(self):
        from .resources_3 import SelfReferencing

        test = SelfReferencing.build()

        self.assertIsNotNone(test)
        self.assertIsNotNone(test.b)

    def test_parent_is_called(self):
        from .resources_4 import GranChild, Child, Base

        o = GranChild(1)

        self.assertIsNotNone(
            GranChild.__init__.__di_code__,
        )

        self.assertIsNotNone(
            Child.__init__.__di_code__,
        )

        self.assertIsNotNone(
            Base.__init__.__di_code__,
        )

        self.assertIsNotNone(o.a)
        self.assertIsNotNone(o.b)
        self.assertIsNotNone(o.c)
        self.assertEqual(1, o.k)

    def test_constructor_called_once(self):
        from .resources_4 import Child

        Child.value = 1
        Child(1)
        self.assertEqual(2, Child.value)

    def test_grand_grand_child_no_infinite_recursion(self):
        from .resources_4 import GrandGrandChild

        GrandGrandChild(1)

    def test_undefined_resource(self):
        from .resources_5 import Base

        with self.assertRaises(UndefinedResourceException):
            Base()

    def test_duplicate_resource(self):
        with self.assertRaises(DuplicateResourceException):
            DI.register("object_1", Mock())
