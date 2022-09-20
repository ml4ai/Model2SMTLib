import json
from pysmt.shortcuts import get_model, And, Symbol, FunctionType, Function, Equals, Int, Real, substitute, TRUE, FALSE, Iff, Plus, ForAll, LT, simplify
from pysmt.typing import INT, REAL, BOOL

filepath = './data/epidemiology/CHIME/CHIME_SIR_model/gromet/BL_1.0/CHIME_SIR_dynamics_BiLayer.json'
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
    inputs = input_variables(jsondata)## returns a list of SMT Symbol() objects, one per variable
    outputs = output_variables(jsondata) ## returns a list of SMT Symbol() objects, one per parameter
    params = parameters(jsondata) ## returns a list of SMT Symbol() objects, one per parameter
    influxes = [influx(data,i+1) for i in range(len(outputs))]
    effluxes = [efflux(data,i+1) for i in range(len(outputs))]
    for i in range(len(outputs)):
        influx_vars = []
        efflux_vars = []
        print('output variable:',outputs[i]) ## this gives the change in the current variable.  example: S', I', and R'
        for j in range(len(influxes[i])): ## influxes correspond to added (+) changes
            influx_index = ((influxes[i])[j])[0] ## index of the parameter 
            influx_param = params[influx_index-1] ## relevant parameter for influx term    
            win_by_param = win_by_parameter(data, influx_index) ## finding variable(s) to be multiplied by the influx parameter
            for k in range(len(win_by_param)):
                win_input_variable_index = (win_by_param[k])[0]
                input_var = inputs[win_input_variable_index - 1]
                influx_vars.append(input_var)
            print('result:', f'+{influx_param}{influx_vars}')
        for j in range(len(effluxes[i])): ## effluxes correspond to subtracted (-) changes
            efflux_index = ((effluxes[i])[j])[0]
            efflux_param = params[efflux_index-1]
            win_by_param = win_by_parameter(data, efflux_index)
            for k in range(len(win_by_param)):
                win_input_variable_index = (win_by_param[k])[0]
                input_var = inputs[win_input_variable_index - 1]
                efflux_vars.append(input_var)
            print('result:', f'-{efflux_param}{efflux_vars}')
        print("")

print(combine_efflux(data))

f.close()
