from importlib import resources
from pysmt.shortcuts import get_model, And, Symbol
from pysmt.typing import INT, REAL
import unittest
import os

class TestCompilation(unittest.TestCase):
    resources = os.path.join(os.path.curdir, "../resources")

    def test_parseGroMEt(self):
        gFile = os.path.join(resources, "CHIME_SIR_while_loop--Gromet-FN-auto.json")
        

if __name__ == '__main__':
    unittest.main()