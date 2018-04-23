"""Default configurtion visible in all mara packages"""
import os

from .config_system import replaceable


@replaceable("debug")
def debug():
    return False


@replaceable("mara_app")
def default_app_module():
    """Sets the default app module where the app composing functions are defined (Default: $MARA_APP or 'app.app')"""
    # this is not replaceable in local_setup.py, only 'replaceable' to get it show up in the flask view
    # hack to already get the info before the config system is fully initialized
    return os.environ.get('MARA_APP', 'app.app')
