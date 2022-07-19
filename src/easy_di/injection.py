import builtins
import inspect
import logging
import re
import sys
from types import ModuleType
from typing import TypeVar, Type, Dict, Optional, Callable

from easy_di.resource_locator import DI
from easy_di.exceptions import UndefinedResourceException

_logger = logging.getLogger(__name__)

INJECTION_MARKER = "__id_injected__"

TYPE = TypeVar("TYPE")


def injected(type_: TYPE, name: Optional[str] = None) -> TYPE:
    return InjectionWrapper(type_, name)


def inject(module_name: str):
    DiModuleInjector().inject(sys.modules[module_name], resource_locator=DI)


class InjectionWrapper:
    def __init__(self, class_, name: Optional[str]):
        self.class_ = class_
        self.name = name


class DiModuleInjector:
    def inject(self, module: ModuleType, resource_locator):
        if not isinstance(module, ModuleType):
            return
        injector = DiClassInjector()
        for module_object in module.__dict__.values():
            if self._is_injectable_class(module_object, module.__name__):
                injector.inject(module_object, resource_locator)

    @classmethod
    def _is_injectable_class(cls, object_: Type, module_name: str):
        return bool(
            inspect.isclass(object_)
            and object_.__module__ == module_name
            and getattr(object_, "__annotations__", None)
        )


_BUILTIN_TYPES = {
    name: type_ for name, type_ in builtins.__dict__.items() if isinstance(type_, type)
}


class DiClassInjector:
    INJECT_RE = re.compile(
        r"(Optional\[)?injected\((?P<class_>[A-Za-z_][A-Z-a-z_0-9]+)\s*(,\s*['|\"](?P<name>[^'\"]+)['\"])?\s*\)(])?"
    )

    def inject(self, class_: Type, resource_locator):
        requirements: Dict[str, InjectionWrapper] = {}
        module = sys.modules[class_.__module__]
        try:
            annotations_ = class_.__annotations__.items()
        except AttributeError:
            _logger.debug(
                "Can't extract annotations from class: %s, skipping", class_.__name__
            )
            annotations_ = {}
        for field_name, resource_reference in annotations_:
            if isinstance(resource_reference, str):
                resource_reference = self._translate_string_into_reference(
                    module, resource_reference
                )

            if isinstance(resource_reference, InjectionWrapper):
                _logger.debug(
                    "Class %s needs resource %s of type %s in field %s",
                    class_.__name__,
                    resource_reference.name or field_name,
                    str(resource_reference.class_),
                    field_name,
                )
                requirements[field_name] = resource_reference

        if not requirements:
            return

        self._wrap_constructor(class_, requirements, resource_locator)

    def _translate_string_into_reference(self, module, resource_reference):
        if match := self.INJECT_RE.match(resource_reference):
            other_class_name = match.group("class_")
            if other_class_name in _BUILTIN_TYPES:
                other_class = _BUILTIN_TYPES[other_class_name]
            else:
                other_class = module.__getattribute__(other_class_name)
            name = match.group("name") or None
            resource_reference = injected(other_class, name)
        return resource_reference

    def _wrap_constructor(
        self, class_: Type, requirements: Dict[str, InjectionWrapper], resource_locator
    ):
        # assure there is a constructor
        constructor = self._get_or_create_constructor(class_)
        injected_constructor = ConstructorWrapper().wrap_constructor(
            class_, constructor, requirements, resource_locator
        )
        class_.__init__ = injected_constructor
        setattr(class_, INJECTION_MARKER, class_)

    @classmethod
    def _get_or_create_constructor(cls, class_: Type):
        constructor = class_.__init__
        if constructor_class := getattr(constructor, INJECTION_MARKER, None):
            if constructor_class is class_:
                # Constructor already wrapped with DI
                return constructor  # will be ignored afterwards
            assert constructor_class in class_.__mro__

            # class shares constructor with parent: we must create an empty one calling super()
            return DiClassInjector.call_parent

        return constructor

    @staticmethod
    def call_parent():
        pass


class ConstructorWrapper:
    def wrap_constructor(
        self,
        class_: Type,
        constructor: Callable,
        requirements: Dict[str, InjectionWrapper],
        resource_locator,
    ) -> Callable:
        if getattr(constructor, INJECTION_MARKER, None):
            # Process each class just once
            return constructor

        code = self._assemble_code(requirements, constructor)
        constructor_ = self._compile_wrapper(
            code, constructor, class_, resource_locator=resource_locator
        )

        setattr(constructor_, INJECTION_MARKER, class_)
        setattr(constructor_, "__di_code__", code)
        setattr(constructor_, "__di_wrapped__", constructor)
        return constructor_

    @classmethod
    def _assemble_code(
        cls, requirements: Dict[str, InjectionWrapper], constructor
    ) -> str:
        code = "def injected_constructor(self, *params, **kwargs):\n"
        code += "    try:\n"
        for key, requirement in requirements.items():
            code += f"        self.{key} = DI.get('{requirement.name or key}')\n"
        code += "    except UndefinedResourceException as e:\n"
        code += "        raise UndefinedResourceException(\n"
        code += "              f'`{e.args[0]}` Needed by class {self.__class__.__name__}') from e\n"
        if constructor is DiClassInjector.call_parent:
            code += "    super(class_, self).__init__(*params, **kwargs)\n"
        elif constructor is not object.__init__:  # do not call object's constructor
            code += "    constructor(self, *params, **kwargs)\n"

        return code

    @classmethod
    def _compile_wrapper(
        cls, code: str, constructor: Callable, class_: Type, resource_locator
    ) -> Callable:
        the_code = compile(code, "injected_constructor", "exec")
        _locals = {}
        _globals = {
            "DI": resource_locator,
            "constructor": constructor,
            "_logger": _logger,
            "class_": class_,
            "UndefinedResourceException": UndefinedResourceException,
        }
        # pylint: disable=eval-used
        eval(the_code, _globals, _locals)
        injected_constructor = _locals["injected_constructor"]
        return injected_constructor
