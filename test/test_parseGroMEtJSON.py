from model2smtlib.gromet.translate import QueryableGromet
import os
import unittest

RESOURCES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../resources")

class TestCompilation(unittest.TestCase):

    def test_parseGroMEt(self):
        gFile = os.path.join(RESOURCES, "gromet", "CHIME_SIR_while_loop--Gromet-FN-auto.json")
        fn = QueryableGromet.from_gromet_file(gFile)


if __name__ == '__main__':
    unittest.main()