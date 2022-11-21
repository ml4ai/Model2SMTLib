import json
from typing import Dict, List, Union
from funman.model import Model, Parameter
from funman.search_utils import Box
from model2smtlib import QueryableModel
import pysmt
from pysmt.shortcuts import (
    get_model,
    And,
    Symbol,
    FunctionType,
    Function,
    Equals,
    Int,
    Real,
    substitute,
    TRUE,
    FALSE,
    Iff,
    Plus,
    Times,
    ForAll,
    simplify,
    LT,
    LE,
    GT,
    GE,
)
from pysmt.typing import INT, REAL, BOOL
import graphviz

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

    def to_dot(self, dot):
        return dot.node(self.parameter)


class BilayerStateNode(BilayerNode):
    def to_smtlib(self, timepoint):
        param = self.parameter
        ans = Symbol(f"{param}_{timepoint}", REAL)
        return ans


class BilayerFluxNode(BilayerNode):
    def to_smtlib(self, timepoint):
        param = self.parameter
        ans = Symbol(f"{param}_{timepoint}", REAL)
        return ans


class BilayerEdge(object):
    def __init__(self, src, tgt):
        self.src = src
        self.tgt = tgt

    def to_smtlib(self, timepoint):
        pass

    def to_dot(self, dot):
        dot.edge(self.src.parameter, self.tgt.parameter)


class BilayerPositiveEdge(BilayerEdge):
    def to_smtlib(self, timepoint):
        return "positive"


class BilayerNegativeEdge(BilayerEdge):
    def to_smtlib(self, timepoint):
        return "negative"

    def to_dot(self, dot):
        dot.edge(self.src.parameter, self.tgt.parameter, style="dashed")


class BilayerEncodingOptions(object):
    def __init__(self, step_size=1, max_steps=2) -> None:
        self.step_size = step_size
        self.max_steps = max_steps


class BilayerModel(Model):
    def __init__(
        self,
        bilayer,
        init_values=None,
        parameter_bounds=None,
        encoding_options=None,
    ) -> None:
        super().__init__(None)
        self.bilayer = bilayer
        self.init_values = init_values
        self.parameter_bounds = parameter_bounds
        self.encoding_options = encoding_options
        self.formula = self._encode()
        self.symbols = self._symbols(self.formula)

    def _split_symbol(self, symbol):
        if "_" in symbol.symbol_name():
            return symbol.symbol_name().rsplit("_", 1)
        else:
            return symbol.symbol_name(), None

    def _symbols(self, formula):
        symbols = {}
        vars = list(formula.get_free_variables())
        # vars.sort(key=lambda x: x.symbol_name())
        for var in vars:
            var_name, timepoint = self._split_symbol(var)
            if timepoint:
                if var_name not in symbols:
                    symbols[var_name] = {}
                symbols[var_name][timepoint] = var
        return symbols

    def symbol_values(self, pysmtModel):
        vars = self.scenario.model.symbols
        vals = {}
        for var in vars:
            vals[var] = {}
            for t in vars[var]:
                vals[var][t] = float(pysmtModel.get_py_value(vars[var][t]))
        return vals

    def symbol_timeseries(
        self, pysmtModel: pysmt.solvers.solver.Model
    ) -> Dict[str, List[Union[float, None]]]:
        """
        Generate a symbol (str) to timeseries (list) of values

        Parameters
        ----------
        pysmtModel : pysmt.solvers.solver.Model
            variable assignment
        """
        series = self.symbol_values(pysmtModel)
        a_series = {}  # timeseries as array/list
        max_t = max(
            [max([int(k) for k in tps.keys()]) for _, tps in series.items()]
        )
        a_series["index"] = list(range(0, max_t + 1))
        for var, tps in series.items():

            vals = [None] * (int(max_t) + 1)
            for t, v in tps.items():
                vals[int(t)] = v
            a_series[var] = vals
        return a_series

    def _encode(self):
        state_timepoints = range(
            0,
            self.encoding_options.max_steps + 1,
            self.encoding_options.step_size,
        )
        transition_timepoints = range(
            0, self.encoding_options.max_steps, self.encoding_options.step_size
        )

        init = And(
            [
                Equals(
                    node.to_smtlib(0), Real(self.init_values[node.parameter])
                )
                for idx, node in self.bilayer.state.items()
            ]
        )

        encoding = self.bilayer.to_smtlib(state_timepoints)

        if self.parameter_bounds:
            parameters = [
                Parameter(
                    node.parameter,
                    lb=self.parameter_bounds[node.parameter][0],
                    ub=self.parameter_bounds[node.parameter][1],
                )
                for _, node in self.bilayer.flux.items()
            ]

            timed_parameters = [
                p.timed_copy(timepoint)
                for p in parameters
                for timepoint in transition_timepoints
            ]
            parameter_box = Box(timed_parameters)
            parameter_constraints = parameter_box.to_smt(
                closed_upper_bound=True
            )
        else:
            parameter_constraints = TRUE()

        ## Assume that all parameters are constant
        parameter_constraints = And(
            parameter_constraints, self._set_parameters_constant(encoding)
        )

        return And(init, parameter_constraints, encoding)

    def _set_parameters_constant(self, formula):
        parameters = {
            node.parameter: Symbol(node.parameter, REAL)
            for _, node in self.bilayer.flux.items()
        }
        symbols = self._symbols(formula)
        all_equal = And(
            [
                And([Equals(parameters[p], s) for t, s in symbols[p].items()])
                for p in parameters
            ]
        )
        return all_equal


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

    def from_json(bilayer_src):
        bilayer = Bilayer()

        if isinstance(bilayer_src, dict):
            data = bilayer_src
        else:
            with open(bilayer_src, "r") as f:
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

    def to_dot(self):
        dot = graphviz.Digraph(
            name=f"bilayer",
            graph_attr={
                #    'label': self.name,
                "shape": "box"
            },
        )
        for n in (
            list(self.tangent.values())
            + list(self.flux.values())
            + list(self.state.values())
        ):
            n.to_dot(dot)
        for e in self.input_edges + self.output_edges:
            e.to_dot(dot)
        return dot

    def to_smtlib(self, timepoints):
        #        ans = simplify(And([self.to_smtlib_timepoint(t) for t in timepoints]))
        ans = simplify(
            And(
                [
                    self.to_smtlib_timepoint(timepoints[i], timepoints[i + 1])
                    for i in range(len(timepoints) - 1)
                ]
            )
        )
        # print(ans)
        return ans

    def to_smtlib_timepoint(
        self, timepoint, next_timepoint
    ):  ## TODO remove prints
        ## Calculate time step size
        time_step_size = next_timepoint - timepoint
        # print("timestep size:", time_step_size)
        eqns = (
            []
        )  ## List of SMT equations for a given timepoint. These will be joined by an "And" command and returned
        for t in self.tangent:  ## Loop over tangents (derivatives)
            derivative_expr = 0
            ## Get tangent variable and translate it to SMT form tanvar_smt
            tanvar = self.tangent[t].parameter
            tanvar_smt = self.tangent[t].to_smtlib(timepoint)
            state_var_next_step = self.state[t].parameter
            state_var_smt = self.state[t].to_smtlib(timepoint)
            state_var_next_step_smt = self.state[t].to_smtlib(next_timepoint)
            #            state_var_next_step_smt = self.state[t].to_smtlib(timepoint + 1)
            relevant_output_edges = [
                (val, val.src.index)
                for val in self.output_edges
                if val.tgt.index == self.tangent[t].index
            ]
            for flux_sign_index in relevant_output_edges:
                flux_term = self.flux[flux_sign_index[1]]
                output_edge = self.output_edges[flux_sign_index[1]]
                expr = flux_term.to_smtlib(timepoint)
                ## Check which state vars go to that param
                relevant_input_edges = [
                    self.state[val2.src.index].to_smtlib(timepoint)
                    for val2 in self.input_edges
                    if val2.tgt.index == flux_sign_index[1]
                ]
                for state_var in relevant_input_edges:
                    expr = Times(expr, state_var)
                if flux_sign_index[0].to_smtlib(timepoint) == "positive":
                    derivative_expr += expr
                elif flux_sign_index[0].to_smtlib(timepoint) == "negative":
                    derivative_expr -= expr
            ## Assemble into equation of the form f(t + delta t) approximately = f(t) + (delta t) f'(t)
            eqn = simplify(
                Equals(
                    state_var_next_step_smt,
                    Plus(state_var_smt, time_step_size * derivative_expr),
                )
            )
            # print(eqn)
            eqns.append(eqn)
        return And(eqns)
