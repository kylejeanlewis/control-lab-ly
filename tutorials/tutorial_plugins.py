# %%
import time
import random
from typing import NamedTuple, Iterable

OtherData = NamedTuple('OtherData', [('strdata', str),('intdata', int),('floatdata', float),('booldata', bool)])
OTHER_FORMAT = '{strdata};{intdata};{floatdata};{booldata}\n'

def generate_sample_data():
    return f'test_output;{random.randint(0,1000)};{random.random():.5};{bool(random.randint(0,1))}\n'

class MockConnection:
    def __init__(self):
        self._open = False
        self._waiting = False
        self.count = 0
    def __enter__(self):
        self.open()
        return self
    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return
    def open(self):
        self._open = True
    def close(self):
        self._open = False
    def is_open(self) -> bool:
        return self._open
    def in_waiting(self) -> bool:
        return self._waiting
    def write(self, data:Iterable) -> int|None:
        if not self._open:
            raise ConnectionError
        return len(data) if data is not None else None
    def read(self) -> bytes:
        if not self._open:
            raise ConnectionError
        time.sleep(0.01)
        return generate_sample_data().encode()
    def read_all(self) -> bytes:
        if not self._open:
            raise ConnectionError
        try:
            return next(self._read_all())
        except StopIteration:
            return b''
    def _read_all(self):
        while self.count < 5:
            time.sleep(0.01)
            self._waiting = True
            self.count += 1
            yield generate_sample_data().encode()
        self._waiting = False
        self.count = 0
        return
    