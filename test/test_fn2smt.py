from tkinter import Variable
from pysmt.shortcuts import get_model, And, Symbol, FunctionType, Function, Equals, Int, Real, substitute, TRUE, FALSE, Iff, Plus, ForAll
from pysmt.typing import INT, REAL, BOOL
import unittest

class TestCompilation(unittest.TestCase):
    def test_toy(self):
        s1 = Symbol("infected")
        model = get_model(And(s1))
        print(model)

    def test_simple_chime(self):
        num_timepoints = 10
        # timepoints = [Symbol(t, INT) for t in range(num_timepoints)]

        # Function Definition for Time indexed symbols
        # I -> R
        const_t = FunctionType(REAL, [INT])
        
        # Function symbol for I(t)
        infected_sym = Symbol("I", const_t)

        # Declare I(0) function
        i_0 = Function(infected_sym, [Int(0)])
        # i_1 = Function(infected_sym, [Int(1)])


        # Assert I(0) = 1.0
        init = Equals(i_0, Real(1.0))

        # Dynamics for I: T(I(t), I(t+1))
        # (I->R) x (I->R) -> B
        trans_func_type = FunctionType(BOOL, [REAL, REAL])
        # T: (I->R) x (I->R) -> B
        trans_func_sym = Symbol("T", trans_func_type)
        # t: -> I
        t_sym = Symbol("t", INT)
        # t+1: -> I 
        tp1_sym = Symbol("t+1", INT)
        # I(t)
        i_t = Function(infected_sym, [t_sym])
        # I(t+1)
        i_tp1 = Function(infected_sym, [tp1_sym])        
        # T(I(t), I(t+1))
        trans_func = Function(trans_func_sym, [i_t, i_tp1])

        transf_func_eq = Iff(trans_func, 
            Equals(i_tp1, Plus(i_t, Real(1.0)))
        )

        subs = {
            t_sym: Int(0),
            tp1_sym: Int(1),
        }

        # Forall t, t+1. 
        #   T(I(t), I(t+1)) && 
        #   t+1 = t + 1     && 
        #   T(I(t), I(t+1)) <-> I(t+1) = I(t) + 1.0
        trans_func_def = ForAll(
            [t_sym, tp1_sym], 
            And(trans_func, Equals(tp1_sym, Plus(t_sym, Int(1))), transf_func_eq)) 
            # substitute(transf_func_eq, subs))
        
        # I(1) = 2.0
        query = Equals(Function(infected_sym, [Int(1)]), Real(2.0))


        # phi = init
        phi = And(init, trans_func_def, query)

        # Solve phi
        model = get_model(phi)
        print(model)


if __name__ == '__main__':
    unittest.main()