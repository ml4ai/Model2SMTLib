from gromet2smtlib.translate import QueryableBilayer
from gromet2smtlib.simulator import query_simulator

from sim.CHIME.CHIME_SIR_sir_function import main as run_CHIME_SIR

import os
import unittest

RESOURCES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../resources")
BILAYER_FILE = os.path.join(RESOURCES, "CHIME_SIR_dynamics_BiLayer.json")

class Test_CHIME_SIR(unittest.TestCase):

    def compare_results(self, infected_threshold):
        """This function compares the simulator and FUNMAN reasoning about the CHIME SIR model.  The query_simulator function executes the simulator main() as run_CHIME_SIR, and answers the does_not_cross_threshold() query using the simulation reults.  The QueryableBilayer class constructs a model from the Bilayer file corresponding to the simulator, and answers a query with the model.  The query for both cases asks whether the number of infected exceed a specified threshold.  The test will succeed if the simulator and QueryableBilayer class agree on the response to the query.  
        
        Args:
            infected_threshold (int): The upper bound for the number of infected.      
        Returns:
            bool: Do the simulator and QueryableGromet results match?
        """

        # query the simulator
        def does_not_cross_threshold(sim_results):
            i = sim_results[1]
            return (i <= 5)
        q_sim = query_simulator(run_CHIME_SIR, does_not_cross_threshold)
        print("q_sim", q_sim)

        # query the gromet file
        q_bilayer = QueryableBilayer.query(f"(i <= 5)")
        print("q_bilayer", q_bilayer)

        # assert the both queries returned the same result
        return  q_sim == q_bilayer

    def test_query_false(self):
        """This test requires both methods to return False.
        """  
        # threshold for infected population
        infected_threshold = 100
        assert(self.compare_results(infected_threshold))

if __name__ == '__main__':
    unittest.main()
