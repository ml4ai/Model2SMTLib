import json
from typing import Dict, List, Union
from funman.model import Model, Parameter, QueryLE, QueryTrue
from funman.model.bilayer import Bilayer, BilayerMeasurement, BilayerModel
from funman.search_utils import Box
from model2smtlib import QueryableModel
from model2smtlib.translate import Encoder, Encoding, EncodingOptions
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

import logging

l = logging.Logger(__name__)


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


class BilayerEncodingOptions(EncodingOptions):
    def __init__(self, step_size=1, max_steps=2) -> None:
        super().__init__(max_steps)
        self.step_size = step_size
        self.max_steps = max_steps


class BilayerEncoder(Encoder):
    def __init__(
        self, config: BilayerEncodingOptions = BilayerEncodingOptions()
    ) -> None:
        super().__init__(config)

    def encode_model(self, model: BilayerModel):
        state_timepoints = range(
            0,
            self.config.max_steps + 1,
            self.config.step_size,
        )

        if len(list(state_timepoints)) == 0:
            raise Exception(
                f"Could not identify timepoints from step_size = {self.config.step_size} and max_steps = {self.config.max_steps}"
            )

        transition_timepoints = range(
            0, self.config.max_steps, self.config.step_size
        )

        init = And(
            [
                Equals(
                    node.to_smtlib(0), Real(model.init_values[node.parameter])
                )
                for idx, node in model.bilayer.state.items()
            ]
        )

        encoding = model.bilayer.to_smtlib(state_timepoints)

        if model.parameter_bounds:
            parameters = [
                Parameter(
                    node.parameter,
                    lb=model.parameter_bounds[node.parameter][0],
                    ub=model.parameter_bounds[node.parameter][1],
                )
                for _, node in model.bilayer.flux.items()
                if node.parameter in model.parameter_bounds
                and model.parameter_bounds[node.parameter]
            ]
            if model.measurements:
                parameters += [
                    Parameter(
                        node.parameter,
                        lb=model.parameter_bounds[node.parameter][0],
                        ub=model.parameter_bounds[node.parameter][1],
                    )
                    for _, node in model.measurements.flux.items()
                    if node.parameter in model.parameter_bounds
                    and model.parameter_bounds[node.parameter]
                ]
            for p in parameters:
                self.untimed_symbols.add(p.name)
            # print(f"Untimed Symbols: {self.untimed_symbols}")
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

        measurements = self._encode_measurements(
            model.measurements, state_timepoints
        )

        ## Assume that all parameters are constant
        measurement_params_eq = And([])
        measurement_params_ident_eq = And([])
        if model.measurements:
            measurement_params_eq = self._set_parameters_constant(
                [v.parameter for v in model.measurements.flux.values()],
                measurements,
            )
            measurement_params_ident_eq = self._set_identical_parameters_equal(
                model.identical_parameters, measurements
            )
            # print(measurement_params_eq)
            # print(measurement_params_ident_eq)

        parameter_equality = self._set_parameters_constant(
            [v.parameter for v in model.bilayer.flux.values()],
            parameter_constraints,
        )
        parameter_ident_eq = self._set_identical_parameters_equal(
            model.identical_parameters, parameter_equality
        )

        # print(measurement_params_ident_eq)
        parameter_constraints = And(
            parameter_constraints,
            parameter_equality,
            measurement_params_eq,
            parameter_ident_eq,
            measurement_params_ident_eq,
        )
        # for p in [init, parameter_constraints, encoding, measurements]:
        #     print(p.get_free_variables())
        formula = And(init, parameter_constraints, encoding, measurements)

        symbols = self._symbols(formula)
        # print(f"Encoding symbols: {symbols}")
        # print(f"Untimed symbols: {self.untimed_symbols}")
        return Encoding(formula=formula, symbols=symbols)

    def _encode_measurements(
        self, measurements: BilayerMeasurement, timepoints
    ):
        ans = And(
            [
                self._encode_measurements_timepoint(measurements, timepoints[i])
                for i in range(len(timepoints))
            ]
        )
        return ans

    def _encode_measurements_timepoint(self, measurements, t):
        observations = []
        if measurements:
            observations = [
                Equals(
                    o.to_smtlib(t), self._observable_defn(measurements, o, t)
                )
                for o in measurements.observable.values()
            ]

        observable_defs = And(observations)
        return observable_defs

    def _observable_defn(self, measurements, obs, t):
        # flux * incoming1 * incoming2 ...
        obs_in_edges = measurements.node_incoming_edges[obs]
        result = Real(0.0)
        for src in obs_in_edges:
            # src is a flux
            f_t = src.to_smtlib(t)
            src_srcs = [
                s.to_smtlib(t) for s in measurements.node_incoming_edges[src]
            ]
            result = Plus(result, Times([f_t] + src_srcs)).simplify()
        # flux = next([measurements.output_edges])
        # print(result)
        return result

    def _set_parameters_constant(self, parameters, formula):
        params = {
            parameter: Symbol(parameter, REAL) for parameter in parameters
        }
        # vars = list(formula.get_free_variables())
        # symbols = {v.symbol_name(): v for v in vars}
        # vars = list(formula.get_free_variables())
        # print(formula)
        symbols = self._symbols(formula)
        # print(
        #     And(
        #         [
        #             And([Equals(params[p], s) for t, s in symbols[p].items()])
        #             for p in params
        #         ]
        #     )
        # )
        all_equal = And(
            [
                And([Equals(params[p], s) for t, s in symbols[p].items()])
                for p in params
            ]
        )
        return all_equal

    def _set_identical_parameters_equal(self, identical_parameters, formula):
        constraints = []
        # print(formula)
        vars = list(formula.get_free_variables())
        symbols = {v.symbol_name(): v for v in vars}
        for idp in identical_parameters:
            idp_symbols = [symbols[p] for p in idp if p in symbols]
            pairs = [
                Equals(p1, p2)
                for p1 in idp_symbols
                for p2 in idp_symbols
                if p1 != p2
            ]
            constraints.append(And(pairs))
        # print(constraints)
        return And(constraints)

    def _split_symbol(self, symbol):
        if "_" in symbol.symbol_name():
            return symbol.symbol_name().rsplit("_", 1)
        else:
            return symbol.symbol_name(), None

    def symbol_values(self, model_encoding, pysmtModel):
        vars = model_encoding.symbols
        # print(f"Vars: {vars}")
        vals = {}
        for var in vars:
            vals[var] = {}
            for t in vars[var]:
                try:
                    symbol = vars[var][t]
                    vals[var][t] = float(
                        pysmtModel.get_py_value(symbol)
                    )  # pysmtModel[symbol].constant_value()
                except OverflowError as e:
                    l.warn(e)
                    pass
        return vals

    def parameter_values(
        self, model, pysmtModel: pysmt.solvers.solver.Model
    ) -> Dict[str, List[Union[float, None]]]:
        try:
            parameters = {
                node.parameter: pysmtModel[Symbol(node.parameter, REAL)]
                for _, node in model.bilayer.flux.items()
            }
            return parameters
        except OverflowError as e:
            l.warn(e)
            return {}

    def symbol_timeseries(
        self, model_encoding, pysmtModel: pysmt.solvers.solver.Model
    ) -> Dict[str, List[Union[float, None]]]:
        """
        Generate a symbol (str) to timeseries (list) of values

        Parameters
        ----------
        pysmtModel : pysmt.solvers.solver.Model
            variable assignment
        """
        series = self.symbol_values(model_encoding, pysmtModel)
        # print(series)
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
