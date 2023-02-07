'''
01 :  8.00 -> 0
02 :  9.60: 3.00 -> 1
03 : 11.52: 3.40: 4.00 -> 5
04 : 13.82: 3.88: 3.80: 8.00 -> 3
05 : 16.59: 4.46: 3.56: 9.00: 8.00 -> 0
06 : 19.91: 5.15: 3.27:10.20: 9.60: 6.00 -> 6
-- : 28.67: 6.97: 2.51:13.37:13.82: 6.00 ->  Done!

'''


import unittest, unittest.mock
import pygame
import glob
import math
import numpy 
import tensorflow as tf

import sys, os

from PES.src.pygameMediator import entropy, calculate_agent_response_and_confidence
from PES.src.pygameMediator import convert_globalseq_to_seqs

from PES.src import lobbyManager
from PES.src import exp_utils

from PES.src import log_utils

from PES import printinfo, printstatus

import matplotlib.pyplot as plt; plt.style.use('ggplot')

from PES import VERBOSE
from PES import MAX_ALLOCATABLE_RESOURCES
from PES import MIN_ALLOCATABLE_RESOURCES
from PES import INPUTS_PATH
from PES import NUM_SEQUENCES
from PES import LOBBY_PLAYERS
from PES.src.pygameMediator import Agent
from PES.ext.pandemic import Pandemic

from PES.src.exp_utils import calculate_normalised_final_severity_performance_metric,get_sequence_severity_from_allocations
from PES.src.exp_utils import get_updated_severity,get_sequence_severity_from_allocations

from PES import ANSI


# --------------------------------------------------------
# Print a nice header identifying the module under testing
# --------------------------------------------------------

class Test_( unittest.TestCase ):   # Note: the name 'Test_' guarantees
                                    # (alphabetically) this TestCase is run
                                    # before other TestCases in this module

    def setUpClass():
        print(                                                          )
        print( "******************************************************" )
        print( "*** Unit tests for module" )
        print( "******************************************************" )
        print(                                                          )
    def tearDownClass ():   print( )

    def test_( self ): 
        severities = [8,3,4,8,8,6]
        allocations =[0,1,5,3,0,6] 

        severities = [1,2,3]
        allocations = [0,0,0]

        severities = [3,4,8]
        allocations = [5,6,4]

        #inport pdb; pdb.set_trace()

        env = Pandemic()
        env.set_fixed_sequence(len(severities),severities,allocations)
        state = env.reset()

        done = False
        count = 0

        count = count + 1

        while not done:
            response = env.sample()
            state2, reward, done, info = env.step(response)
            if done==True:
                env.done = True
                #env.severities = env.damage()
                env.render()
                
            count = count + 1


        print ( env.severity_evolution )

        env.plot_severity_evolution().show()

        perf, worst,best = calculate_normalised_final_severity_performance_metric( env.severities, env.initial_severities)

        print(f'Final Severity:{numpy.sum(env.severities)}')
        print(f'Worst:{worst}')
        print(f'Best:{best}')
        print(f'Normalised Performance:{perf}')

        f = get_sequence_severity_from_allocations(allocations, severities)

        print(f)

        assert perf>=0, "The normalised performance cannot be negative."
        assert f== numpy.sum( env.severities)


if __name__ == '__main__':
    t = Test_()
    t.test_()
