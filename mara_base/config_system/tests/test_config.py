from .. import replace, replaceable, add_config_from_environment, _reset_config
import pytest


# this dance with orig_something and so on is needed so 'something' is actually decorated by the fixture
# and the config can be cleaned up
def something(argument: str = None) -> str:
    "Test API function"
    return "x"


orig_something = something

def without_args() -> str:
    "Test without arguments"
    return "x"

orig_without_args = without_args

@pytest.fixture()
def setup_config():
    """Setup a clean config and insert a single API"""
    _reset_config()
    global something
    global without_args
    something = replaceable(orig_something)
    without_args = replaceable(orig_without_args)
    yield setup_config
    _reset_config()


# use it in every tests in this file
pytestmark = pytest.mark.usefixtures("setup_config")


def test_replaceable_decorator():
    @replaceable
    def _tester(argument: str = None) -> str:
        return "x"

    # unreplaced
    assert 'x' == _tester()
    assert 'x' == _tester("ABC")


def test_replace_decorator_without_function_pointer():
    # In downstream package which want's to overwrite the API
    @replace('mara_base.config.tests.test_config.something')
    def replacement_for_something(argument: str = None) -> str:
        return argument or 'y'

    assert 'y' == something()
    assert 'ABC' == something("ABC")


def test_replace_decorator_with_function_pointer():
    # In downstream package which want's to overwrite the API
    @replace('mara_base.config.tests.test_config.something', include_original_function=True)
    def replacement_for_something(argument: str = None, original_function=None) -> str:
        assert callable(original_function)
        tmp = original_function(argument)
        return tmp + (argument or 'y')

    assert 'xy' == something()
    assert 'xABC' == something("ABC")


def test_replace_function():
    def replacement_for_something(argument: str = None) -> str:
        return argument or 'y'

    replace('mara_base.config.tests.test_config.something', function=replacement_for_something)

    assert 'y' == something()
    assert 'ABC' == something("ABC")


def test_replace_function_with_non_function():
    with pytest.raises(AssertionError):
        replace('mara_base.config.tests.test_config.something', function="something")


def test_warn_on_use_replace_decorator_twice():
    # In downstream package which want's to overwrite the API
    @replace('mara_base.config.tests.test_config.something')
    def replacement_for_something(argument: str = None) -> str:
        return argument or 'y'

    with pytest.warns(RuntimeWarning) as record:
        @replace('mara_base.config.tests.test_config.something')
        def replacement_for_something2(argument: str = None) -> str:
            return 'z'

    assert len(record) == 1
    assert "Replacing already replaced function for API" in record[0].message.args[0]

    assert 'z' == something()
    assert 'z' == something("ABC")


def test_add_config_from_environment():
    import os
    os.environ['mara_mara_base__config__tests__test_configuration__without_args'] = 'y'

    assert 'x' == without_args()

    add_config_from_environment()

    assert 'y' == without_args()
