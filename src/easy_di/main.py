import sys

from easy_di.injection import DiModuleInjector
from easy_di.loaders_patching import InjectedMetaPaths


class _StaticData:
    _initialized = False

    @classmethod
    def is_initialized(cls):
        return cls._initialized

    @classmethod
    def initialized(cls):
        cls._initialized = True


def di_init():
    """We make sure all the Finders in the sys.meta_path are patched so that every loaded module is patched for
    DI if required"""
    if _StaticData.is_initialized():
        return

    sys.meta_path = InjectedMetaPaths(sys.meta_path[:])
    injector = DiModuleInjector()

    # Injecting already loaded modules
    loaded_modules = []
    for module in sys.modules.values():
        loaded_modules.append(module)
    for module in loaded_modules:
        injector.inject(module)
    _StaticData.initialized()


di_init()
