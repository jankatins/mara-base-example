"""Mara admin command line interface"""

import logging
import os
import sys

import click

log = logging.getLogger(__name__)


def _add_syslog_handler():
    """Adds a handler that the log produced by the CLI commands also got to systemd log"""
    # This needs to be done in a function in each command as flask run will also import this files to have the
    # click commands available
    if os.name == 'posix':
        import logging.handlers
        # /dev/log is linux only (would need a different path on Mac, but who cares on dev machines...)
        handler = logging.handlers.SysLogHandler(address='/dev/log')
        # If it's added to this modules log, only log mesages in this module would be sent...
        logging.root.addHandler(handler)



@click.group(help="""\
This shell command acts as general utility script for mara applications.

All configured downloader will be available.

To run the webapp, use 'flask run'.

""")
@click.option('--debug/--no-debug', default=False)
def cli(debug: bool):
    # --debug is consumed by the setup_commandline_commands but it's here to let it show up in help and
    pass

def setup_commandline_commands():
    """Needs to be run before click itself is run so the config which contributes click commands is available"""
    debug = '--debug' in sys.argv
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s, %(name)s: %(message)s',
                        datefmt='%Y-%m-%dT%H:%M:%S',
                        stream=sys.stdout)
    _add_syslog_handler()

    if debug:
        logging.root.setLevel(logging.DEBUG)
        log.debug("Enabled debug output via commandline")

    # Initialize the config system
    from .config_system import add_config_from_environment, add_config_from_local_setup_py
    add_config_from_local_setup_py()
    add_config_from_environment()

    # we try the second mechanism as well
    from .config import debug as configured_debug
    if configured_debug():
        logging.root.setLevel(logging.DEBUG)
        log.debug("Enabled debug output via config")

    # overwrite any config system with commandline debug switch
    if debug and not configured_debug():
        from .config_system import replace
        replace('debug', function = lambda: True)

    from . import _call_app_composing_function
    _call_app_composing_function()

    from . import get_flattend_configuration
    for module, command in get_flattend_configuration('MARA_CLICK_COMMANDS'):
        if command and 'callback' in command.__dict__ and command.__dict__['callback']:
            package = command.__dict__['callback'].__module__.rpartition('.')[0]
            if package != 'flask':
                command.name = package + '.' + command.name
                cli.add_command(command)


def main():
    setup_commandline_commands()
    args = sys.argv[1:]
    cli.main(args=args, prog_name='mara')


@cli.command()
def print_config():
    """Prints the current config"""
    from .config_system import print_config
    print_config()


if __name__ == '__main__':
    cli()
