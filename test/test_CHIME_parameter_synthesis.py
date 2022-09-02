from multiprocessing.heap import Arena
from gromet2smtlib.parameter_space import ParameterSpace
from gromet2smtlib.translate import QueryableGromet

import sim.CHIME.substitutions as CHIME_substitutions

import os
import unittest

RESOURCES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../resources")
GROMET_FILE = os.path.join(RESOURCES, "CHIME_SIR_while_loop--Gromet-FN-auto.json")

class Test_CHIME_SIR(unittest.TestCase):

    def test_parameter_synthesis(self):
        """
        This test constructs two formulations of the CHIME model:
           - the original model where Beta is a epoch-dependent constant over three epochs (i.e., a triple of parameters)
           - a modified variant of the original model using a single constant Beta over the entire simulation (akin to a single epoch).

        It then compares the models by determining that the respective spaces of feasible parameter values intersect.
        """
        # read in the gromet file
        gromet_org = QueryableGromet.from_gromet_file(GROMET_FILE)
        # identify the GrometBox we want to replace
        beta_fn_org = gromet_org.get_box("get_beta")
        # construct a GrometBox to use as a substitution
        beta_fn_sub = CHIME_substitutions.constant_beta()
        # substitute the constant beta box in place of the original
        gromet_sub = gromet_org.substitute_box(beta_fn_org, beta_fn_sub)
        # get parameter space for the original (3 epochs)
        ps_b1_b2_b3 = gromet_org.synthesize_parameters()
        # get parameter space for the constant beta variant
        ps_bc = gromet_sub.synthesize_parameters()
        # construct special parameter space where parameters are equal
        ps_eq = ParameterSpace.construct_all_equal(ps_b1_b2_b3)
        # intersect the original parameter space with the ps_eq to get the
        # valid parameter space where (b1 == b2 == b3)
        ps = ParameterSpace.intersect(ps_b1_b2_b3, ps_eq)
        # assert the parameters spaces for the original and the constant beta
        # variant are the same
        assert(ParameterSpace.compare(ps_bc, ps))

if __name__ == '__main__':
    unittest.main()
