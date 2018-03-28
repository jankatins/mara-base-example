"""Mara admin command line interface"""

import click
import types
import typing
import sys
import logging

log = logging.getLogger(__name__)

_group = click.Group(help="""\
This shell command acts as general utility script for mara applications.

All configured downloader will be available.

To run the webapp, use 'flask run'.

""")


def register_declared_commands(self, module: types.ModuleType):
    """Adds all declared click commands to the app, grouped by package

    You can declare click commands by adding a `MARA_CLICK_COMMANDS` property to
    the module which contains a list of `@click.command()` decorated functions.

    Does nothing, if no `MARA_CLICK_COMMANDS` is declared in the module or the list is empty.
    """
    if not hasattr(module, 'MARA_CLICK_COMMANDS'):
        return
    commands = getattr(module, 'MARA_CLICK_COMMANDS')
    assert (isinstance(commands, typing.Iterable))
    for command in commands:
        if 'callback' in command.__dict__ and command.__dict__['callback']:
            package = command.__dict__['callback'].__module__.rpartition('.')[0]
            if package != 'flask':
                command.name = package + '.' + command.name
                _group.add_command(command)


def main():
    #log.setLevel(logging.DEBUG)
    args = sys.argv[1:]
    _group.main(args=args, prog_name='mara')


if __name__ == '__main__':
    main()
