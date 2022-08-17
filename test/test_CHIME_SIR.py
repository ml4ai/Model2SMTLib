from gromet2smtlib.translate import QueryableGromet
from gromet2smtlib.simulator import query_simulator

from sim.CHIME_SIR import main as run_CHIME_SIR

import os
import unittest

RESOURCES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../resources")

class Test_CHIME_SIR(unittest.TestCase):
    def test_query(self):
        # threshold for infected population
        infected_threshold = 130

        # query the simulator
        def does_not_cross_threshold(sim_results):
            i = sim_results[2]
            return all(i_t <= infected_threshold for i_t in i)
        q_sim = query_simulator(run_CHIME_SIR, does_not_cross_threshold)

        # query the gromet file
        gromet = QueryableGromet.from_gromet_file(os.path.join(RESOURCES, "CHIME_SIR_while_loop--Gromet-FN-auto.json"))
        q_gromet = gromet.query(f"(forall ((t Int)) (<= (I t) {infected_threshold}))")

        # assert the both queries returned the same result
        assert  q_sim == q_gromet

if __name__ == '__main__':
    unittest.main()
