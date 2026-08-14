import os

try:
    os.kill(999999, 0)
except Exception as e:
    print(type(e))
