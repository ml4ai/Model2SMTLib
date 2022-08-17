from pysmt.shortcuts import get_model, And, Symbol
from pysmt.typing import INT, REAL
import unittest
import os

RESOURCES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../resources")

class TestCompilation(unittest.TestCase):

    def test_parseGroMEt(self):
        gFile = os.path.join(RESOURCES, "CHIME_SIR_while_loop--Gromet-FN-auto.json")
        # forall t I_t <= tau === I_0 <= tau and I_1 ...

if __name__ == '__main__':
    unittest.main()