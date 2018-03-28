import functools
from typing import Callable, Tuple, Dict, List
import logging
import warnings
import os

log = logging.getLogger(__name__)

__CONFIG_REGISTRY: Dict[str, Tuple[Callable, bool]] = {}
__ORIG_API_REGISTRY: Dict[str, Callable] = {}


def replaceable(func):
    """Decorator for public API which can be replaced by downstream packages"""
    api_name = (func.__module__ or '<no_module>') + '.' + func.__name__
    log.debug("Registered new API '%s'", api_name)
    __ORIG_API_REGISTRY[api_name] = func

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if api_name in __CONFIG_REGISTRY:
            replacement_func, include_original_function = __CONFIG_REGISTRY[api_name]
            if include_original_function:
                kwargs['original_function'] = func
            log.debug("Using replaced API function '%s'", replacement_func.__name__)
            return replacement_func(*args, **kwargs)
        else:
            log.debug("Using original API function '%s'", func.__name__)
            return func(*args, **kwargs)

    return wrapper


def replace(api_name: str, include_original_function=False, function: Callable = None):
    """Replaces a API function in another package

    Can be used as a decorator:
    >>> @replace('mara_without_function_pointer')
    >>> def replacement(...):
    >>>     pass

    or as a function:
    >>> def replacement(...):
    >>>     pass
    >>> if should_be_replaced:
    >>>     replace('mara_without_function_pointer', replacement)

    """
    if function is None:
        # usage as decorator
        def submitting_decorator(func):
            replace(api_name=api_name, include_original_function=include_original_function, function=func)
            return func

        return submitting_decorator
    else:
        if api_name in __CONFIG_REGISTRY:
            warnings.warn(f"Replacing already replaced function for API '{api_name}'", RuntimeWarning)
        assert callable(function), f"New function for API '{api_name}' is not callable: {type(function)}"
        __CONFIG_REGISTRY[api_name] = (function, include_original_function)
        log.info("Replacing API '%s' with %s", api_name, function.__name__)


def _reset_config():
    """Reset config internal state

    Internal function for testing purpose"""
    for k in list(__CONFIG_REGISTRY.keys()):
        del __CONFIG_REGISTRY[k]
    for k in list(__ORIG_API_REGISTRY.keys()):
        del __ORIG_API_REGISTRY[k]


def get_get_current_config() -> List[Tuple[str, Callable]]:
    return list(__ORIG_API_REGISTRY.items())


def add_config_from_environment():
    """Add configuration from the environment

    This only works for config items which return either strings or numbers (floats).

    Any environment variable (in lovercase) which starts 'mara_' is turned into
    functions which returns the value. The rest of the environment variable name
    has any '__' replaced by '.'. If the value is a valid float, it's returned
    as a float. Otherwise it's returned as a string.

    E.g. the following variable

        MARA_PACKAGENAME__CONFIG_ITEM=y

    is equivalent to the following @replace call

    >>> @replace('packagename.config_item')
    >>> def replacement():
    >>>     return 'y'

    """
    for k in os.environ.keys():
        key = str(k).lower()
        if key.startswith('mara_'):
            api_name = k[5:].replace('__', '.')
            value = os.environ[k]
            try:
                # try to convert to a number, but just keep the string if it doesn't work
                value = float(value)
            except:
                pass
            replace(api_name, False, lambda: value)
