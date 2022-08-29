import json
from automates.model_assembly.gromet.model.gromet_box_function import GrometBoxFunction
from automates.model_assembly.gromet.model.gromet_fn import GrometFN
from automates.model_assembly.gromet.model.gromet_port import GrometPort
from automates.model_assembly.gromet.model.literal_value import LiteralValue
from automates.model_assembly.gromet.model.typed_value import TypedValue
from automates.model_assembly.gromet.model.function_type import FunctionType
from pysmt.shortcuts import get_model, And, Or, Symbol, Equals, Int, Real, substitute, TRUE, FALSE, Iff, Plus, ForAll, LT
from pysmt.typing import INT, REAL, BOOL

from automates.model_assembly.gromet.model.gromet_fn_module import GrometFNModule

from automates.program_analysis.JSON2GroMEt.json2gromet import json_to_gromet

# TODO more descriptive name
class QueryableGromet(object):

    def __init__(self, gromet_fn) -> None:
        self._gromet_fn = gromet_fn
        self.gromet_encoding_handlers = {
            str(GrometFNModule) : self._gromet_fnmodule_to_smtlib,
            str(GrometFN) : self._gromet_fn_to_smtlib,
            str(TypedValue) : self._gromet_typed_value_to_smtlib,
            str(GrometPort) : self._gromet_port_to_smtlib,
            str(GrometBoxFunction): self._gromet_box_function_to_smtlib,
            str(LiteralValue): self._gromet_literal_value_to_smtlib,
        }

    def to_smtlib(self):
        """Convert the self._gromet_fn into a set of smtlib constraints.

        Returns:
            pysmt.Node: SMTLib object for constraints.
        """
        return self.gromet_encoding_handlers[str(self._gromet_fn.__class__)](self._gromet_fn, stack=[])

    def _to_smtlib(self, node, stack=[]):
        """Convert the node into a set of smtlib constraints.

        Returns:
            pysmt.Node: SMTLib object for constraints.
        """
        return self.gromet_encoding_handlers[str(node.__class__)](node, stack=stack)

    def _get_stack_identifier(self, stack):
        return ".".join([name for (name, x) in stack ])

    def _gromet_fnmodule_to_smtlib(self, node, stack=[]):
        stack.append((node.name, node))
        fn_constraints = self._to_smtlib(node.fn, stack=stack)
        # attr_constraints = And([self._to_smtlib(attr, stack=node) for attr in node.attributes])
        stack.pop()
        return And(fn_constraints 
        #, attr_constraints
        )
    
    def _gromet_fn_to_smtlib(self, node, stack=[]):
        """Convert a fn node into constraints.  The constraints state that:
        - The function output (pof) is equal to the output of the box function (bf)

        Args:
            node (GrometFN): the function to encode
            stack (GrometFNModule, optional): GrometFNModule defining node. Defaults to None.

        Returns:
            pysmt.Node: Constraints encoding node.
        """
        # fn.pof[i] = fn.bf[fn.pof[i].box-1]
        
        stack.append(("fn", node))
        outputs = []
        for i, pof in enumerate(node.pof):
            stack.append((f"pof[{i}]", pof))
            pof_head = self._to_smtlib(pof, stack=stack)
            stack.pop()
            stack.append((f"bf[{pof.box-1}]", node.bf[pof.box-1]))
            pof_body = self._to_smtlib(node.bf[pof.box-1], stack=stack)
            stack.pop()
            outputs.append(Equals(pof_head, pof_body))

        phi = And(outputs)
        stack.pop()
        return phi

    def _gromet_port_to_smtlib(self, node, stack=[]):
        stack.append((node.name, node))
        name = self._get_stack_identifier(stack)
        stack.pop()
        return Symbol(f"{name}", REAL)

    def _gromet_box_function_to_smtlib(self, node, stack=[]):
        phi = None
        if node.function_type == FunctionType.EXPRESSION:
            function_node = stack[0][1].attributes[node.contents-1]
            stack.append((f"fn", function_node))
            phi = self._to_smtlib(function_node, stack=stack)
            stack.pop()
        elif node.function_type == FunctionType.LITERAL:
            function_node = node.value
            stack.append((f"value", function_node))
            phi = self._to_smtlib(function_node, stack=stack)
        else:
            raise ValueError(f"node.function_type = {node.function_type} is not supported.")

        return phi

    def _gromet_typed_value_to_smtlib(self, node, stack=[]):
        phi = None
        if node.type == "FN": # FIXME find def for the string
            # define output ports
            # map i/o ports 
            #  wfopo
            stack.append((f"value", node.value))
            phi = self._to_smtlib(node.value, stack=stack)
            stack.pop()

        return phi

    def _gromet_literal_value_to_smtlib(self, node, stack=[]):
        value_type = node.value_type
        value = None
        value_enum = None

        if value_type == "Integer":
            value = Int(node.value)
            value_enum = INT
        else:
            raise ValueError(f"literal_value of type {value_type} not supported.")

        literal = Symbol(f"{self._get_stack_identifier(stack)}", value_enum)
        phi = Equals(literal, value)
        
        return phi

    # STUB This is where we will read in an process the gromet file
    def query(this, query_str):
        return True

    # STUB Read the gromet file into some object
    @staticmethod
    def from_gromet_file(gromet_path):
        return QueryableGromet(json_to_gromet(gromet_path))