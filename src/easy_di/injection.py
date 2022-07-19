import builtins
import inspect
import logging
import re
import sys
from types import ModuleType
from typing import Callable, Dict, Optional, Type, TypeVar

from easy_di import di_storage
from easy_di.exceptions import UndefinedResourceException

_logger = logging.getLogger(__name__)

INJECTION_MARKER = "__id_injected__"

TYPE = TypeVar("TYPE")


def injected(type_: TYPE, name: Optional[str] = None, force_no_factory=False) -> TYPE:
    """
    Specify that a class attribute must be injected at runtime in every instance of the class.

    :arg type_ the expected type, only for mypy or similar tools
    :arg name the name of the looked up resource, if different from the field name
    :arg force_no_factory if you're sure the injected resource won't be a factory you can set this flag to true, and
            you'll gain a consistent performances improvement
    """
    return InjectionWrapper(type_, name, force_no_factory)


def inject(module_name: str):
    DiModuleInjector().inject(sys.modules[module_name])


class InjectionWrapper:
    def __init__(self, class_, name: Optional[str], force_no_factory=False):
        self.class_ = class_
        self.name = name
        self.force_no_factory = force_no_factory


class DiModuleInjector:
    def inject(self, module: ModuleType):
        if not isinstance(module, ModuleType):
            return
        injector = DiClassInjector()
        for module_object in module.__dict__.values():
            if self._is_injectable_class(module_object, module.__name__):
                injector.inject(module_object)

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

    def inject(self, class_: Type):
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

        self._wrap_constructor(class_, requirements)

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
        self, class_: Type, requirements: Dict[str, InjectionWrapper]
    ):
        # assure there is a constructor
        constructor = self._get_or_create_constructor(class_)
        injected_constructor = ConstructorWrapper().wrap_constructor(
            class_, constructor, requirements
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
            if constructor_class not in class_.__mro__:
                raise RuntimeError(
                    "Class %s that contains the constructor must be in the MRO of class %s",
                    constructor_class.__name__,
                    class_.__name__,
                )

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
    ) -> Callable:
        if getattr(constructor, INJECTION_MARKER, None):
            # Process each class just once
            return constructor

        code = self._assemble_code(requirements, constructor)
        constructor_ = self._compile_wrapper(code, constructor, class_)

        setattr(constructor_, INJECTION_MARKER, class_)
        setattr(constructor_, "__di_code__", code)
        setattr(constructor_, "__di_wrapped__", constructor)
        return constructor_

    @classmethod
    def _assemble_code(
        cls,
        requirements: Dict[str, InjectionWrapper],
        constructor,
    ) -> str:
        code = "def injected_constructor(self, *params, **kwargs):\n"
        code += "    try:\n"
        for key, requirement in requirements.items():
            key_ref, is_factory_key = di_storage.keys(requirement.name or key)
            code += f"        self.{key} = di_storage.{key_ref}\n"
            if not requirement.force_no_factory:
                code += f"        if di_storage.{is_factory_key}:\n"
                code += f"           self.{key} = self.{key}()\n"
        code += "    except AttributeError as e:\n"
        code += "        raise UndefinedResourceException(\n"
        code += "              f'`{e.args[0]}` Needed by class {self.__class__.__name__}') from e\n"
        if constructor is DiClassInjector.call_parent:
            code += "    super(class_, self).__init__(*params, **kwargs)\n"
        elif constructor is not object.__init__:  # do not call object's constructor
            code += "    constructor(self, *params, **kwargs)\n"

        return code

    @classmethod
    def _compile_wrapper(
        cls, code: str, constructor: Callable, class_: Type
    ) -> Callable:

        the_code = compile(code, "injected_constructor", "exec")
        _locals = {}
        _globals = {
            "di_storage": di_storage,
            "constructor": constructor,
            "_logger": _logger,
            "class_": class_,
            "UndefinedResourceException": UndefinedResourceException,
        }
        # pylint: disable=eval-used
        eval(the_code, _globals, _locals)  # nosec
        # We are evaluating code generated by our own function
        injected_constructor = _locals["injected_constructor"]
        return injected_constructor
