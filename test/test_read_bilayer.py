import os
import unittest
from model2smtlib.bilayer.translate import Bilayer

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../data")


class TestCompilation(unittest.TestCase):
    def test_read_bilayer(self):
        bilayer_json_file = os.path.join(
            DATA, "CHIME_SIR_dynamics_BiLayer.json"
        )
        bilayer = Bilayer.from_json(bilayer_json_file)
        assert bilayer


if __name__ == "__main__":
    unittest.main()
