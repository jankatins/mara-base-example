import logging
import types

import entrypoints

log = logging.getLogger(__name__)


# Contributing the config stuff to the FLASK APP
class _bp():
    def __iter__(self):
        import mara_base.config.view as view
        return iter([view.mara_config])


MARA_FLASK_BLUEPRINTS = _bp()


class _acl():
    def __iter__(self):
        import mara_base.config.view as view
        return iter([view.acl_resource])


MARA_ACL_RESOURCES = _acl()


class _nav():
    def __iter__(self):
        import mara_base.config.view as view
        return iter([view.navigation_entry])


MARA_NAVIGATION_ENTRY_FNS = _nav()

# The main API functionality
_register_funcs = []


def register_all_in_module(self, module: types.ModuleType):
    """Registers all declared functionality with the installed extension points
    """
    if not _register_funcs:
        for ep in entrypoints.get_group_all('mara_base.mara_consumer'):
            try:
                register_func = ep.load()
            except Exception:
                log.exception('Error loading register function')
            else:
                _register_funcs.append(register_func)

    for register_func in _register_funcs:
        register_func(module)
