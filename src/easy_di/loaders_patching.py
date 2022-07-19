import functools
from importlib.abc import Loader

from easy_di.injection import DiModuleInjector

# Copied and modified from
# https://github.com/brettlangdon/importhook   (MIT Licence)


class InjectedMetaPaths(list):
    """
    Custom list that will ensure any items added are wrapped as a "hooked" finder
    This class is made to replace `sys.meta_paths`
    """

    def __init__(self, finders):
        super().__init__([_injection_patch(f) for f in finders])

    def __setitem__(self, key, val):
        super().__setitem__(key, _injection_patch(val))


class _InjectionPatchLoader(Loader):
    """
    Custom `importlib.abc.Loader` which ensures we modify all constructors that require injection when a module is
    loaded.
    """

    loader: Loader

    def __init__(self, loader):
        if not loader:
            raise RuntimeError("Empty loader")
        self.loader = loader

    def module_repr(self, module):
        return self.loader.module_repr(module)

    def __getattribute__(self, name):
        # If they are requesting the "loader" attribute, return it right away
        loader = super().__getattribute__("loader")

        if name == "loader":
            return loader

        # Pass through attributes/methods only if they exist on the underlying loader
        if hasattr(loader, name):
            try:
                return super().__getattribute__(name)
            except AttributeError:
                return getattr(loader, name)

        raise AttributeError(f"Can't get attribute of loader: {name}")

    def create_module(self, spec):
        if not hasattr(self.loader, "create_module"):
            return None

        return self.loader.create_module(spec)

    def load_module(self, fullname):
        if not hasattr(self.loader, "load_module"):
            return None

        module = self.loader.load_module(fullname)
        if module is None:
            return None

        DiModuleInjector().inject(module)

        return module

    def exec_module(self, module):
        if not hasattr(self.loader, "exec_module"):
            return None

        mod = self.loader.exec_module(module)
        if mod is not None:
            module = mod

        DiModuleInjector().inject(module)

        return module


def _injection_patch(finder):
    """
    Helper function to create a new "hooked" subclass of the provided finder class
    This function replaces the `Finder.find_spec` function to ensure that any ModuleSpecs will
    use an `InjectionPatchLoader`
    """
    # If this finder has already been wrapped, then return as-is
    if hasattr(finder, "__wrapped_for_injection__"):
        return finder

    # Override the functions we care about
    if hasattr(finder, "find_spec"):
        setattr(finder, "find_spec", _wrap_find_spec(finder.find_spec))
    if hasattr(finder, "find_loader"):
        setattr(finder, "find_loader", _wrap_find_loader(finder.find_loader))

    # Make this finder as being wrapped
    setattr(finder, "__wrapped_for_injection__", True)
    return finder


def _wrap_find_loader(find_loader):
    @functools.wraps(find_loader)
    def wrapper(fullname, path):
        loader = find_loader(fullname, path)
        return _InjectionPatchLoader(loader)

    return wrapper


def _wrap_find_spec(find_spec):
    @functools.wraps(find_spec)
    def wrapper(fullname, path, target=None):
        spec = find_spec(fullname, path, target=target)
        if spec is not None and spec.loader is not None:
            spec.loader = _InjectionPatchLoader(spec.loader)
        return spec

    return wrapper
