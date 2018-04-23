import collections
import copy
import logging
import sys
import types
import typing
import itertools

log = logging.getLogger(__name__)


# Contributing the config stuff to the FLASK APP

def MARA_FLASK_BLUEPRINTS():
    from .config_system import view as view
    yield view.mara_config


def MARA_ACL_RESOURCES():
    from .config_system import view as view
    yield view.acl_resource


def MARA_NAVIGATION_ENTRY_FNS():
    from .config_system import view as view
    yield view.navigation_entry_fns


# The main API functionality
_mara_configuration: {str: list} = collections.defaultdict(list)


def register_all_in_module(module: types.ModuleType):
    """Registers all declared functionality"""
    for attr in dir(module):
        if attr.startswith('MARA_'):
            items = getattr(module, attr)
            assert (callable(items) or isinstance(items, typing.Iterable))
            _mara_configuration[attr].append((module, items))


def get_flattend_configuration(name: str) -> typing.Iterable:
    all_items = _mara_configuration[name]
    for module, items in all_items:
        if callable(items):
            # a generator
            yield from zip(itertools.repeat(module), items())
        else:
            # lists and so on
            yield from zip(itertools.repeat(module), items)


def register_all_imported_modules():
    for name, module in copy.copy(sys.modules).items():
        register_all_in_module(module)

def _call_app_composing_function():
    import importlib
    from .config import default_app_module
    app_module_name = default_app_module()
    try:
        app = importlib.import_module(app_module_name)
    except ModuleNotFoundError:
        log.error("MARA_DEFAULT_APP (%s) is not an importable module.", app_module_name)
        return
    if not hasattr(app, 'compose_app'):
        log.error("MARA_DEFAULT_APP (%s) has no 'compose_app() function.", app_module_name)
        return
    compose_app = getattr(app, 'compose_app')
    log.debug("About to call '%s.compose_app()'", app_module_name)
    try:
        compose_app()
    except BaseException:
        log.exception("Calling '%s.compose_app()' resulted in an exception")
        return
    log.debug("Finished '%s.compose_app()'", app_module_name)
    return
