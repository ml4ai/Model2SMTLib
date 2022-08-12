from pysmt.shortcuts import get_model, And, Symbol
from pysmt.typing import INT, REAL
import unittest

class TestCompilation(unittest.TestCase):
    def test_toy(self):
        s1 = Symbol("infected")
        model = get_model(And(s1))
        print(model)

if __name__ == '__main__':
    unittest.main()