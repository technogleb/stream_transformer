"""Just a simple timer using context manager."""
from contextlib import contextmanager
import time


class SimpleTimer:
    """Timer put in a form of context manager."""
    def __enter__(self):
        self.start = time.time()

    def __exit__(self, type, values, traceback):
        print("It took {}".format(time.time() - self.start))


# or using contextlib package
@contextmanager
def timer():
    start = time.time()
    yield start
    end = time.time()
    print("It took {}".format(end-start))
