import sys
import time
import os
import signal

def run():
    try:
        print("Running, pid =", os.getpid())
        time.sleep(10)
    finally:
        print("Finally block executed")

if __name__ == "__main__":
    run()
