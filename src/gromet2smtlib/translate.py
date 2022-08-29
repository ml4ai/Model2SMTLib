import json
from automates.model_assembly.gromet.model.gromet_box_function import GrometBoxFunction
from automates.model_assembly.gromet.model.gromet_fn import GrometFN
from automates.model_assembly.gromet.model.gromet_port import GrometPort
from automates.model_assembly.gromet.model.typed_value import TypedValue
from pysmt.shortcuts import get_model, And, Or, Symbol, FunctionType, Function, Equals, Int, Real, substitute, TRUE, FALSE, Iff, Plus, ForAll, LT
from pysmt.typing import INT, REAL, BOOL

from automates.model_assembly.gromet.model.gromet_fn_module import GrometFNModule

from automates.program_analysis.JSON2GroMEt.json2gromet import json_to_gromet

# TODO more descriptive name
class QueryableGromet(object):

    def __init__(self, gromet_fn) -> None:
        self._gromet_fn = gromet_fn
        self.gromet_encoding_handlers = {
            str(GrometFNModule) : self._gromet_fnmodel_to_smtlib,
            str(GrometFN) : self._gromet_fn_to_smtlib,
            str(TypedValue) : self._gromet_typed_value_to_smtlib,
            str(GrometPort) : self._gromet_port_to_smtlib,
            str(GrometBoxFunction): self._gromet_box_function_to_smtlib,
        }

    def to_smtlib(self):
        """Convert the self._gromet_fn into a set of smtlib constraints.

        Returns:
            pysmt.Node: SMTLib object for constraints.
        """
        return self.gromet_encoding_handlers[str(self._gromet_fn.__class__)](self._gromet_fn)

    def _to_smtlib(self, node, parent=None):
        """Convert the node into a set of smtlib constraints.

        Returns:
            pysmt.Node: SMTLib object for constraints.
        """
        return self.gromet_encoding_handlers[str(node.__class__)](node, parent=parent)

    def _gromet_fnmodel_to_smtlib(self, node, parent=None):
        fn_constraints = self._to_smtlib(node.fn, parent=node)
        # attr_constraints = And([self._to_smtlib(attr, parent=node) for attr in node.attributes])
        return And(fn_constraints 
        #, attr_constraints
        )
    
    def _gromet_fn_to_smtlib(self, node, parent=None):
        """Convert a fn node into constraints.  The constraints state that:
        - The function output (pof) is equal to the output of the box function (bf)

        Args:
            node (GrometFN): the function to encode
            parent (GrometFNModule, optional): GrometFNModule defining node. Defaults to None.

        Returns:
            pysmt.Node: Constraints encoding node.
        """
        # fn.pof[i] = fn.bf[fn.pof[i].box-1]
        phi = And([
            Equals(
                self._to_smtlib(pof, parent=node), 
                self._to_smtlib(node.bf[pof.box-1], parent=node)
            )
            for pof in node.pof
        ])
        return phi

    def _gromet_port_to_smtlib(self, node, parent=None):
        return Symbol(f"port_{node.name}", REAL)

    def _gromet_box_function_to_smtlib(self, node, parent=None):
        
        return Real(2.0) # FIXME

    def _gromet_typed_value_to_smtlib(self, node, parent=None):
        return And([])

    # STUB This is where we will read in an process the gromet file
    def query(this, query_str):
        return True

    # STUB Read the gromet file into some object
    @staticmethod
    def from_gromet_file(gromet_path):
        return QueryableGromet(json_to_gromet(gromet_path))