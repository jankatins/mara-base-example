"""
Config system based on functions

The config system consists of two ends:
* a functions which can be replaced
* a way to replace these functions

It can use environment variables and actual function implementations to replace the config function

"""
import functools
import logging
import os
from typing import Callable, Tuple, Dict, List

log = logging.getLogger(__name__)

__CONFIG_REGISTRY: Dict[str, Tuple[Callable, bool]] = {}
__ORIG_API_REGISTRY: Dict[str, Callable] = {}


def replaceable(config_name=None):
    """Decorator for public API which can be replaced by downstream packages

    The default config_name is modulename.funcname.
    """
    outer_config_name = config_name

    def _replaceable(func):
        config_name = (outer_config_name if outer_config_name
                       else (func.__module__ or '<no_module>') + '.' + func.__name__)
        log.debug("Registered new replaceable function '%s'", config_name)
        __ORIG_API_REGISTRY[config_name] = func

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if config_name in __CONFIG_REGISTRY:
                replacement_func, include_original_function = __CONFIG_REGISTRY[config_name]
                if include_original_function:
                    kwargs['original_function'] = func
                # log.debug("Using replaced function '%s'", replacement_func.__name__)
                return replacement_func(*args, **kwargs)
            else:
                # log.debug("Using original function '%s'", func.__name__)
                return func(*args, **kwargs)

        return wrapper

    return _replaceable


def replace(config_name: str, include_original_function=False, function: Callable = None):
    """Replaces a API function in another package

    Can be used as a decorator:
    >>> @replace('soh_without_function_pointer')
    >>> def replacement(...):
    >>>     pass

    or as a function:
    >>> def replacement(...):
    >>>     pass
    >>> if should_be_replaced:
    >>>     replace('soh_without_function_pointer', replacement)

    """
    if function is None:
        # usage as decorator
        def submitting_decorator(func):
            replace(config_name=config_name, include_original_function=include_original_function, function=func)
            return func

        return submitting_decorator
    else:
        assert callable(function), f"New function for '{config_name}' is not callable: {type(function)}"
        if config_name in __CONFIG_REGISTRY:
            orig_replacement, _ = __CONFIG_REGISTRY[config_name]
            log.warn("Replacing already replaced function for '%s': %s.%s",
                     config_name, orig_replacement.__module__, orig_replacement.__name__)
        __CONFIG_REGISTRY[config_name] = (function, include_original_function)
        log.debug("Replacing function '%s' with %s.%s", config_name, function.__module__, function.__name__)


def _reset_config():
    """Reset config internal state

    Internal function for testing purpose"""
    for k in list(__CONFIG_REGISTRY.keys()):
        del __CONFIG_REGISTRY[k]
    for k in list(__ORIG_API_REGISTRY.keys()):
        del __ORIG_API_REGISTRY[k]


def get_get_current_config() -> List[Tuple[str, Callable]]:
    return list(__CONFIG_REGISTRY.items())


@replaceable("mara_default_environment_prefix")
def default_environment_prefix():
    return os.environ.get('MARA_MARA_BASE__CONFIG_SYSTEM__DEFAULT_ENVIRONMENT_PREFIX', 'MARA')


def _bool(value):
    valid_str = {'true': True, 't': True, '1': True,
                 'false': False, 'f': False, '0': False,
                 }
    lower_value = value.lower()
    try:
        return valid_str[lower_value]
    except:
        raise ValueError('invalid literal for boolean: "%s"' % value)


def _float(input: str) -> float:
    # workaround for getting "1,0" recognized as "1.0"
    val = float(input.replace(',', '.'))
    return val


def add_config_from_environment():
    """Add configuration from the environment

    This only works for config items which return either strings or numbers (floats).

    Any environment variable (in lovercase) which starts 'soh_' is turned into
    functions which returns the value. The rest of the environment variable name
    has any '__' replaced by '.'. If the value is a valid float or boolean, it's returned
    as a float/boolean. Otherwise it's returned as a string.

    E.g. the following variable

        SOH_PACKAGENAME__CONFIG_ITEM=y

    is equivalent to the following @replace call

    >>> @replace('packagename.config_item')
    >>> def replacement():
    >>>     return 'y'

    The prefix can be configured as well, just not from the environment
    """
    prefix = default_environment_prefix().lower()
    loaded = False
    for k in os.environ.keys():
        key = str(k).lower()
        if key.startswith(prefix):
            config_name = key[len(prefix) + 1:].replace('__', '.')
            value = os.environ[k]
            try:
                # try to convert to a number, but just keep the string if it doesn't work
                value = _float(value)
            except:
                try:
                    value = _bool(value)
                except:
                    # we treat it as a string
                    pass
            loaded = True
            replace(config_name, False, lambda: value)
    if loaded:
        log.debug("Loaded config from environment")


def add_config_from_local_setup_py():
    # apply environment specific settings (not in git repo)
    import importlib
    from ..config import default_app_module
    parts = default_app_module().split('.')
    while parts:
        try:
            pos_module = '.'.join(parts) + '.local_setup'
            importlib.import_module(pos_module)
            log.debug("Loaded config from local_setup.py at %s", pos_module)
            return
        except ModuleNotFoundError:
            pass
        parts.pop()
    log.debug("No local_setup.py found.")
    return


def print_config():
    max_len = 0
    for k, v in get_get_current_config():
        max_len = max(len(k), max_len)
    format_str = f'%-{max_len}s -> %s'
    for k, v in get_get_current_config():
        f, include_parent = v
        print(format_str % (k, f()))
