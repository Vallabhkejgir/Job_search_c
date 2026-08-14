# module_a
def foo(): return "original"

# module_b
from test_mock import foo
def call_foo(): return foo()

# test
import sys
sys.modules['test_mock'] = sys.modules[__name__]
foo = foo
def call_foo(): return foo()

# actually let's use separate files
