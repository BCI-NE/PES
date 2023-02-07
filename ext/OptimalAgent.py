"""
PES - Pandemic Experiment Scenario

(Quasi)Optimal Agent

The pandemic experiments has a damage function for each city which is a dynamical map.  The task of any agent is to solve the integer partition problem for the number of MAX_ALLOCATABLE_RESOURCES, in units of AVAILABLE_RESOURCES_PER_SEQUENCE.
But this must be done in a way that the severity of each city, governed by the dynamical map, arrives to zero as close as possible by the end of the sequence.

Hence, a ground-truth solution can be approximated for this problem if we first find the zeros of the dynamical map, and then use the responses that can cause exactly that (as close as possible).

This code does exactly that, and stores the deciding function p[state][remaining sequence length] in optimal.pkl

THIS AGENT WORKS BY KNOWING THE SEQUENCE LENGTH.

"""

from PES import VERBOSE
from PES import INPUTS_PATH
from PES import AVAILABLE_RESOURCES_PER_SEQUENCE
from PES import MAX_ALLOCATABLE_RESOURCES

from PES.src.pygameMediator import convert_globalseq_to_seqs
from PES.ext.pandemic import Pandemic
import numpy
import os
import pickle



def get_agent_function():

    #inport pdb; pdb.set_trace()
    MAX_SEQ_LENGTH = 11
    MAX_SEVERITY = 10
    MIN_SEVERITY = 1

    ITERATION_STEPS = 20


    # Find the zeros numerically.
    f = numpy.zeros((MAX_SEVERITY+1,MAX_ALLOCATABLE_RESOURCES+1))
    for s in range(MIN_SEVERITY,MAX_SEVERITY+1):
        severities = numpy.zeros((ITERATION_STEPS,))
        severities[0]=s

        for a in range(1,11):
            allocations = numpy.ones((ITERATION_STEPS,), dtype=numpy.int32)
            allocations[0] = a


            env = Pandemic()
            env.set_fixed_sequence(len(severities),severities,allocations)
            state = env.reset()

            done = False
            count = 0

            count = count + 1

            while not done:
                response = env.sample()
                state2, reward, done, info = env.step(response)
                
                if (env.severities[0] <= 0):
                    # Register the length where the severity reaches zero (the zero of the dynamical map)
                    f[s][a] = count
                    done = True
                
                if done==True:
                    env.done = True
                    #env.severities = env.damage()
                    env.render()
                    
                count = count + 1


    print( f )
 
    # Invert the function, so that we can get length = f(severity, allocation) --> allocation = p(severity, length)
    p = numpy.zeros((MAX_SEVERITY+1,MAX_SEQ_LENGTH))
    for s in range(MIN_SEVERITY,MAX_SEVERITY+1):
        for l in range(0,MAX_SEQ_LENGTH):
            for a in range(0,MAX_ALLOCATABLE_RESOURCES+1):
                if (f[s][a] == l):
                    p[s][l] = a
                    break

    # For all the remaining lengths just use the response that achieves the reaching to zero as slowly as possible (saving resources)
    for s in range(MIN_SEVERITY, MAX_SEVERITY+1):
        for l in range(0,MAX_SEQ_LENGTH):
            if ( p[s][l] == 0):
                p[s][l] = p[s][l-1]


    # Finally, for all the other values (where it is not possible to achieve zero) just use the biggest value possible to do it as fast as you can.    
    for s in range(MIN_SEVERITY,MAX_SEVERITY+1):
        for l in range(MAX_SEQ_LENGTH-2,0,-1):
            if ( p[s][l] == 0):
                p[s][l] = p[s][l+1]

    # Regardless of the length, just pick 10 for cities with severity 10 so that they do not increase.
    p[10][1:] = 10
    
    
    print ( p )



    with open( os.path.join( INPUTS_PATH, 'optimal.pkl') ,'wb') as f:
        pickle.dump( p, f)

get_agent_function()


