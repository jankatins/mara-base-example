# mara-base

Base package of mara ecosystem. The packages has two main functionalities:

* A simply config system based in replacable functions
* A way to declare and consume extension points

## Extension points

### Use contributed functionality of a package

An application has two ways to use functionality in a contributing package:

* A "take all" approach: `import package; mara_base.register_module(package)`
* Only using specific functionality: every functionality you want 
  needs to registered with the specific consumer of these 
  functionality: e.g. this registers only the click commands of 
  `package` with the `mara_base` click commands extension point: 
  `import package; mara_base.cli.register_declared_commands(package)`. 
  
The goal of mara ecosystem is that if you update a package, new 
functionality is added automatically to your app or e.g. database 
migration automatically include newly declared models. For that to 
work, it's best to use the "take all" approach. In the other case 
you are also responsible to include all items which are needed for 
some specific functionality.


### Declaring extension points and extending them

`mara_base` declares a base way of declaring extention points. Extention 
points consist of one side declaring that something can be extended 
and packages extending that functionality. 

For packages which can be extended, they need need to declare a 
function which can "insert" the contribution in the normal way.

In setup.py
```python
setup(
    # [...]
    entry_points={
        'mara_base.mara_consumer': [
            'cli = mara_base.cli:register_something',
        ]
    },
    # [...]
)
```

`register_something` needs to be a function which takes a module and 
looks into that module for a special attribute (usually `MARA_SOMETHING`).

```python
_models = []
def register_something(self, module: types.ModuleType):
    models = getattr(module, 'MARA_SOMETHING')
    if not models:
        return
    assert (isinstance(models, typing.Iterable))
    # save it somewhere where you can handle them later
    # do not iterate over it, to make lazy loading possible
    _models.append(models)

def do_something():
    all_models = []
    for iterable in _models:
        all_models.extend(iterable)
    # do something with all_commands, e.g. do a database migration with all models
```

A contributing model now has to declare in `package.__init__.py` an iterable 
which returns all contributing functionality, e.g. in our example all 
sqlalachemy models. If instantiating has no side effects, this can simply be done in a list. If it has 
sideeffects, e.g. it takes some time. Use a generator.

```python
from .models import model1
MARA_SOMETHING = [model1]
#or in case it has sideeffects:
class _():
    def __iter__(self):
        return iter([long_running_process()])
MARA_SOMETHING = _()
```

## Mara config

Configuration system based on replaceable functions.

One side defines a replaceable function by decorating that 
functions with `@replaceable`. To change this config, 
decorate a replacement function with `@replace('orig_package.func')`.

  
### Example
 
```python
# in package which declares API
from mara_base.config import replaceable
@replaceable
def something(argument:str=None) -> str:
    return "x"

print(something())
print(something("ABC"))

# In downstream package which want's to overwrite the API
from mara_base.config import replace
@replace('<no_module>.something')
def replacement_for_something(argument:str=None) -> str:
    return argument or 'y'

print(something())
print(something("ABC"))
```

## Configs from Environment

If you call `mara_base.config.add_config_from_environment()`, 
this add replacement functions from environment variables.

This only works for config items which return either strings or numbers (floats).

Any environment variable (in lovercase) which starts 'mara_' is turned into
functions which returns the value. The rest of the environment variable name
has any '__' replaced by '.'. If the value is a valid float, it's returned
as a float. Otherwise it's returned as a string.

E.g. the following variable

    MARA_PACKAGENAME__CONFIG_ITEM=y

is equivalent to the following @replace call

```python
@replace('packagename.config_item')
def replacement():
     return 'y'
```

