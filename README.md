# mara-base

Base package of mara ecosystem. The packages functionalities:

* a way to compose an app
* a `mara` command start registered click commands
* a simply config system based on replacable functions

## Build an app

The goal of mara ecosystem is that if you update a package, new
functionality is added automatically to your app or database
migration automatically include newly declared models. To make
the app still composable, you build a function `compose_app()` in
module `app.app`. This function should then call
`mara_base.register_all_in_module(module)` for all modules it wants
to include.

The default module can be overwritten by setting the env variable:
`MARA_APP=module.submodule`.

## Contribute functionality in a package

A package has to expose their functionality via `MARA_*` iterables
(either lists or generators). The iterable contains the to be added
functionality. It is advised to use generators so submodules can be
lazily loaded when the functionality is actually used. This is
especially important if you use optional functionality (e.g. a flask
view which exposes the config system, but the config system itself
is useable without the flask views).

If a package contains sub-functionality which can be consumed
independently from each other, consider putting them into subpackages
and let the main module return a union of all sub-functionality.

## Consume contributed functionality

Contributed functionally can be consumed by calling
`mara_base.get_flattend_configuration(MARA_VARIABLE_NAME)` which yields
the functionality in tuples `(module, content)`. `module` is the
module used in the `mara_base.register_all_in_module(module)` call.

The consumer should then add the functionality in the right places, e.g.
the `mara` commandline adds all contributed click commands as subcommands.

## Mara config

Configuration system based on replaceable functions.

One side defines a replaceable function by decorating that
functions with `@replaceable`. To change this config,
decorate a replacement function with `@replace('name')`.

The default name of a config is `orig_package.func` but can be overwritten
in the `@replaceable('name')` decorator.

### Example

```python
# in package which declares API
from mara_base.config_system import replaceable
@replaceable("name")
def something(argument:str=None) -> str:
    return "x"

print(something())
print(something("ABC"))

# In downstream package which want's to overwrite the API
from mara_base.config_system import replace
@replace('name')
def replacement_for_something(argument:str=None) -> str:
    return argument or 'y'

print(something())
print(something("ABC"))
```

## Configs from local_setup.py

Per default a `local_setup.py` in the module defined in the environment
variable `MARA_APP` and all modules higher up (first one found wins) is
imported. Use this to place all you local modifications to configs and
exclude this file from the repo (`.gitignore`).


## Configs from Environment

To aid dockerization, replacement functions are also generated from
environment variables. Environment config is loaded last and wins over
`local_setup.py`!

This only works for config items which return either numbers (floats),
bools, or strings.

Any environment variable (case insensitive) which starts with 'MARA_' is
turned into functions which returns the value. The rest of the environment
variable name has any '__' replaced by '.'. If the value is a valid float,
it's returned as a float. If it's a valid bool, it's returned as a boolean.
Otherwise it's returned as a string.

E.g. the following variable

    MARA_PACKAGENAME__CONFIG_ITEM=y

is equivalent to the following `@replace` call

```python
from mara_base.config_system import replace

@replace('packagename.config_item')
def replacement():
     return 'y'
```

## MARA_* properties

To make any functionality available in the app, the module which wants it available 
has to import the module and passed it to `mara_base.register_all_in_module(module)`.

### MARA_CLICK_COMMANDS: Click commands, grouped by package

`MARA_CLICK_COMMANDS` is a generator which yields `@click.command()`
decorated functions (or a list of such functions).
