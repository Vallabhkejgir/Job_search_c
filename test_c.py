import test_b
test_b.foo = lambda: "mocked"
print(test_b.call_foo())
