import sys


def store(key, value, is_factory):
    module = sys.modules[__name__]
    attribute, factory_attribute = module.keys(key)

    setattr(module, attribute, value)
    setattr(module, factory_attribute, is_factory)


def keys(key):
    return f"__{key}__", f"__{key}_is_factory__"
