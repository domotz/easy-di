from unittest.mock import Mock

from easy_di.exceptions import DuplicateResourceException, UndefinedResourceException


class DI:
    resources = {}
    _initialized = False

    @classmethod
    def register(cls, resource_name, resolver, force=False, is_factory=False):
        """Registers a resource to be injected in needing objects.

        :type resource_name: six.text_type the resource name
        :type resolver:  object|callable  If callable it will be called with no parameters and the returned value will
        be the injected object. Otherwise, the injected object will be 'resolver' itself.
        :type is_factory: boolean - if True, the resolver will be treated as if it were a callable object, even if it is
        not (usable for injecting factories)

        WARNING: if it's callable, the resolver will be called every time a new object is constructed - be careful with
        expensive functions.
        :type force: bool overwrites previously registered resolvers, set to True only in test
        """
        resource_name = str(resource_name)
        if resource_name in cls.resources and not force:
            raise DuplicateResourceException(resource_name)
        cls.resources[resource_name] = resolver, is_factory

    @classmethod
    def register_mock(cls, resource_name) -> Mock:
        """Used for unit testing: creates a mock, registers it as a resource and returns it"""
        mock = Mock()
        cls.register(resource_name, mock, force=True)
        return mock

    @classmethod
    def get(cls, resource_name, default=None):
        """Resolves the resource. Usually you don't want to use this method, the @injected decorator does all the work.

        Sometimes you need to use the DI like it was a Resource Locator and this method allows something likely"""
        try:
            resolver, is_factory = cls.resources[str(resource_name)]
        except KeyError as e:
            if default is not None:
                return default
            raise UndefinedResourceException(resource_name) from e
        if is_factory:
            return resolver()
        else:
            return resolver

    @classmethod
    def exists(cls, resource_name):
        return str(resource_name) in cls.resources

    @classmethod
    def cleanup(cls):
        cls.resources = {}
