"""Mara admin views"""

import html
import pprint
import sys

from mara_page import acl
from mara_base.config import get_get_current_config

import flask
from mara_page import navigation, response, _, bootstrap

mara_config = flask.Blueprint('mara_config', __name__, url_prefix='/config2', static_folder='static')

acl_resource = acl.AclResource('Configuration')


@mara_config.route('/')
@acl.require_permission(acl_resource)
def configuration_page():
    config_modules = {}
    for configs in get_get_current_config():
        api_name, func = configs
        module_name = func.__module__
        module = sys.modules[module_name]
        if module_name not in config_modules:
            config_modules[module_name] = {'doc': module.__doc__, 'functions': {}}
        try:
            value = func()
        except Exception:
            value = 'error calling function'
        config_modules[module_name]['functions'][api_name] \
            = {'doc': func.__doc__ or '', 'value': value}

    return response.Response(
        html=[(bootstrap.card(
            title_left=_.b[html.escape(module_name)],
            body=[_.p[html.escape(str(config['doc']))],
                  bootstrap.table(
                      [],
                      [_.tr[
                           _.td[function_name.replace('_', '_<wbr/>')],
                           _.td[_.em[function['doc']]],
                           _.td[_.pre[html.escape(pprint.pformat(function['value']))]]]
                       for function_name, function in config['functions'].items()])
                  ]) if config['functions'] else '') for module_name, config in
              sorted(config_modules.items())],
        title='Mara Configuration')


def navigation_entry():
    return [navigation.NavigationEntry('Configuration',
                                       uri_fn=lambda: flask.url_for('.configuration_page'),
                                       icon='cogs', rank=100),
            ]
