import json
from typing import Dict
from model2smtlib import QueryableModel
from pysmt.shortcuts import get_model, And, Symbol, FunctionType, Function, Equals, Int, Real, substitute, TRUE, FALSE, Iff, Plus, Times, ForAll, simplify, LT, LE, GT, GE
from pysmt.typing import INT, REAL, BOOL

class QueryableBilayer(QueryableModel):
    def __init__(self):
        pass

    # STUB This is where we will read in and process the bilayer file
    def query(query_str):
        return False

    # STUB Read the bilayer file into some object
    @staticmethod
    def from_bilayer_file(bilayer_path):

        return QueryableBilayer(Bilayer.from_json(bilayer_path))


class BilayerNode(object):
    def __init__(self, index, parameter):
        self.index = index
        self.parameter = parameter


class BilayerStateNode(BilayerNode):
    def to_smtlib(self, timepoint):
        param = self.parameter
        ans = Symbol(f"{param}_{timepoint}", REAL)
        print(ans)
        return ans


class BilayerFluxNode(BilayerNode):
    def to_smtlib(self, timepoint):
        param = self.parameter
        ans = Symbol(f"{param}_{timepoint}", REAL) 
        print(ans)
        return ans


class BilayerEdge(object):
    def __init__(self, src, tgt):
        self.src = src
        self.tgt = tgt

    def to_smtlib(self, timepoint):
        pass


class BilayerPositiveEdge(BilayerEdge):
    def to_smtlib(self, timepoint):
        return "+"


class BilayerNegativeEdge(BilayerEdge):
    def to_smtlib(self, timepoint):
        return "-"


class Bilayer(object):
    def __init__(self):
        self.tangent: Dict[
            int, BilayerStateNode
        ] = {}  # Output layer variables, defined in Qout
        self.flux: Dict[
            int, BilayerFluxNode
        ] = {}  # Functions, defined in Box, one param per flux
        self.state: Dict[
            int, BilayerStateNode
        ] = {}  # Input layer variables, defined in Qin
        self.input_edges: BilayerEdge = []  # Input to flux, defined in Win
        self.output_edges: BilayerEdge = []  # Flux to Output, defined in Wa,Wn

    def from_json(bilayer_path):
        bilayer = Bilayer()

        with open(bilayer_path, "r") as f:
            data = json.load(f)

        # Get the input state variable nodes
        bilayer._get_json_to_statenodes(data)

        # Get the output state variable nodes (tangent)
        bilayer._get_json_to_tangents(data)

        # Get the flux nodes
        bilayer._get_json_to_flux(data)

        # Get the input edges
        bilayer._get_json_to_input_edges(data)

        # Get the output edges
        bilayer._get_json_to_output_edges(data)

        return bilayer

    def _get_json_node(self, node_dict, node_type, node_list, node_name):
        for indx, i in enumerate(node_list):
            node_dict[indx + 1] = node_type(indx + 1, i[node_name])

    def _get_json_to_statenodes(self, data):
        self._get_json_node(
            self.state, BilayerStateNode, data["Qin"], "variable"
        )

    def _get_json_to_tangents(self, data):
        self._get_json_node(
            self.tangent, BilayerStateNode, data["Qout"], "tanvar"
        )

    def _get_json_to_flux(self, data):
        self._get_json_node(
            self.flux, BilayerFluxNode, data["Box"], "parameter"
        )

    def _get_json_edge(
        self, edge_type, edge_list, src, src_nodes, tgt, tgt_nodes
    ):
        return [
            edge_type(src_nodes[json_edge[src]], tgt_nodes[json_edge[tgt]])
            for json_edge in edge_list
        ]

    def _get_json_to_input_edges(self, data):
        self.input_edges += self._get_json_edge(
            BilayerEdge, data["Win"], "arg", self.state, "call", self.flux
        )

    def _get_json_to_output_edges(self, data):
        self.output_edges += self._get_json_edge(
            BilayerPositiveEdge,
            data["Wa"],
            "influx",
            self.flux,
            "infusion",
            self.tangent,
        )
        self.output_edges += self._get_json_edge(
            BilayerNegativeEdge,
            data["Wn"],
            "efflux",
            self.flux,
            "effusion",
            self.tangent,
        )

    def to_smtlib(self, timepoints):
        return And([self.to_smtlib_timepoint(t) for t in range(timepoints)])

    def to_smtlib_timepoint(self, timepoint): ## TODO remove prints
        for t in self.tangent:
            derivative_expr = 0
            print('index:', t)
            tanvar = self.tangent[t].parameter
            tanvar_smt = self.tangent[t].to_smtlib(2)
#            print('tangent variable:', tanvar)
            for output_edge in self.output_edges:
                if output_edge.tgt.parameter == tanvar:
                    param = output_edge.src.parameter
                    print(output_edge.to_smtlib(2))
#                    print('parameter:',param)
                    for t3 in self.flux:
                        if self.flux[t3].parameter == param:
                            flux_term = self.flux[t3]
                            expr = flux_term.to_smtlib(2)
                    for input_edge in self.input_edges:
                        if input_edge.tgt.parameter == param:
                            state_var = input_edge.src.parameter
                            for t2 in self.state:
                                if self.state[t2].parameter == state_var:
#                                    print(self.state[t2].parameter)
                                    expr = Times(expr, self.state[t2].to_smtlib(2))
                    derivative_expr += expr 
                    print('expr:', expr)
            print('tan var:', tanvar_smt)
            print('derivative_expr:', simplify(derivative_expr))
            Equals(tanvar_smt, derivative_expr)
#                            print('state variable:',input_edge.src.parameter)
##        return And([t.to_smtlib(timepoint) for t in self.tangent])
