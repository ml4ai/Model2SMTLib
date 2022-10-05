import json
from pysmt.shortcuts import get_model, And, Symbol, FunctionType, Function, Equals, Int, Real, substitute, TRUE, FALSE, Iff, Plus, Times, ForAll, LT, simplify
from pysmt.typing import INT, REAL, BOOL
import numpy as np
import matplotlib.pyplot as plt
#filepath = './data/epidemiology/CHIME/CHIME_SIR_model/gromet/BL_1.0/CHIME_SIR_dynamics_BiLayer.json' ## filepath within the GroMEt data Google Drive
filepath = './data/CHIME_SIR_dynamics_BiLayer.json'
f = open(filepath)
data = json.load(f)

def output_variables(jsondata):
    """Finds output variables of BiLayer model."""
    params_list = [list(i.values())[0] for i in data['Qout']]
    result = [Symbol(f"{param}",REAL) for param in params_list]
    return result

def input_variables(jsondata):
    """Finds input variables of BiLayer model."""
    params_list = [list(i.values())[0] for i in data['Qin']]
    result = [Symbol(f"{param}",REAL) for param in params_list]
    return result

def input_variables_timepoints(jsondata, num_timepoints):
    """Finds input variables of BiLayer model and creates an array of them for a specified number of iterations/timepoints"""
    result = []
    params_list = [list(i.values())[0] for i in data['Qin']]
    for param in params_list:
        param_timepoints = [Symbol(f"{param}_{t}",REAL) for t in range(num_timepoints)]
        Equals(param_timepoints[0], Real(10.0)) ## added manually for implementation; delete later
        result.append(param_timepoints)
    return result

def input_variables_timepoints_n(jsondata, num_timepoints):
    """Finds input variables of BiLayer model and creates an array of them for a specified number of iterations/timepoints"""
    result = []
    params_list = [list(i.values())[0] for i in data['Qin']]
    for param in params_list:
        param_timepoints = [Symbol(f"{param}_n_{t}",REAL) for t in range(num_timepoints)]
        result.append(param_timepoints)
    return result

def parameters(jsondata):
    """Finds parameters of BiLayer model."""
    params_list = [list(i.values())[0] for i in data['Box']]
    result = [Symbol(f"{param}",REAL) for param in params_list]
    return result

def win_by_parameter(jsondata, index):
    """Gives the [arg, call] list(s) for the indexed parameter."""
    return [list(i.values()) for i in data['Win'] if list(i.values())[1]==(index)]

def win_by_variable(jsondata, index):
    """Gives the [arg, call] list(s) for the indexed parameter."""
    return [list(i.values()) for i in data['Win'] if list(i.values())[0]==(index)]

def influx(jsondata, index):
    """Gives the [influx, infusion] list for the indexed variable."""
    return [list(i.values()) for i in data['Wa'] if list(i.values())[1]==(index)]

def efflux(jsondata, index):
    """Gives the [efflux, effusion] list for the indexed variable."""
    return [list(i.values()) for i in data['Wn'] if list(i.values())[1]==(index)]

def combine_efflux(jsondata):
    n_timepoints = 10
    inputs = input_variables(jsondata)## returns a list of SMT Symbol() objects, one per variable
    inputs_timepoints = input_variables_timepoints(jsondata, n_timepoints)
    inputs_timepoints_n = input_variables_timepoints_n(jsondata, n_timepoints)
    scale = [Symbol(f"scale_{t}", REAL) for t in range(n_timepoints)] ## added manually - not part of bilayer 
    for s in scale:
        Equals(s, Real(1))### temporary for implementation; added manually
    n = Symbol(f"n", REAL) ## added manually - not part of bilayer
    outputs = output_variables(jsondata) ## returns a list of SMT Symbol() objects, one per parameter
    params = parameters(jsondata) ## returns a list of SMT Symbol() objects, one per parameter
    for param in params:
        Equals(param, Real(0.01))### temporary for implementation; added manually
    influxes = [influx(data,i+1) for i in range(len(outputs))]
    effluxes = [efflux(data,i+1) for i in range(len(outputs))]
    vars_to_change_timepoints = []
    derivative_eqns = []
    dyn_eqns = []
### beginning additional indent. add loop over time points.
    for t in range(n_timepoints - 1):
        for i in range(len(outputs)): ## loop over the different variables
            influx_vars = []
            efflux_vars = []
            output_var = outputs[i]
            output_var_timepoints = inputs_timepoints_n[i]
            var_to_change_timepoints = inputs_timepoints[i] ## variable that we're taking derivative of
            vars_to_change_timepoints.append(var_to_change_timepoints)
            derivative_eqn = 0 # initialization
            for j in range(len(influxes[i])): ## influxes correspond to added (+) changes
                influx_index = ((influxes[i])[j])[0] ## index of the parameter 
                influx_param = params[influx_index-1] ## relevant parameter for influx term    
                win_by_param = win_by_parameter(data, influx_index) ## finding variable(s) to be multiplied by the influx parameter
                for k in range(len(win_by_param)):
                    win_input_variable_index = (win_by_param[k])[0]
                    input_var_timepoints = inputs_timepoints[win_input_variable_index - 1]
                    influx_vars.append(input_var_timepoints)
    #            print('result:', f'+{influx_param}{influx_vars}')
                influx_expression = influx_param
                for var in influx_vars:
                    influx_expression = Times(influx_expression, var[t]) ## change var[0] to var[t] for t ranging over the timepoints
    #            print(influx_expression)
                derivative_eqn = derivative_eqn + influx_expression
            for j in range(len(effluxes[i])): ## effluxes correspond to subtracted (-) changes
                efflux_index = ((effluxes[i])[j])[0]
                efflux_param = params[efflux_index-1]
                win_by_param = win_by_parameter(data, efflux_index)
                for k in range(len(win_by_param)):
                    win_input_variable_index = (win_by_param[k])[0]
                    input_var_timepoints = inputs_timepoints[win_input_variable_index - 1]
                    efflux_vars.append(input_var_timepoints)
    #            print('result:', f'-{efflux_param}{efflux_vars}')
                efflux_expression = efflux_param
                for var in efflux_vars:
                    efflux_expression = Times(efflux_expression, var[t])
    #            print(efflux_expression)
                derivative_eqn = derivative_eqn - efflux_expression
            dyn_eqn = simplify(Equals(output_var_timepoints[t+1], var_to_change_timepoints[t] + derivative_eqn))
            scale_eqn = simplify(Equals(var_to_change_timepoints[t+1], scale[t+1]*output_var_timepoints[t+1]))
            print(dyn_eqn)
            print(scale_eqn)
            derivative_eqns.append(derivative_eqn)
            dyn_eqns.append(dyn_eqn)
            dyn_eqns.append(scale_eqn)
            print("")
    ### end of loop over timepoints
    ### Manually adding initialization and scale - not sure if there's a way to automate this...
    n = Symbol(f"n", REAL) 
    return dyn_eqns

print(combine_efflux(data))

    
   

f.close()
