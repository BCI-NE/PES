'''
Test the decay function to imitate a NN that humanly fail.
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
import random

from PES import VERBOSE
from PES import MAX_ALLOCATABLE_RESOURCES
from PES import MIN_ALLOCATABLE_RESOURCES
from PES import AVAILABLE_RESOURCES_PER_SEQUENCE
from PES import INPUTS_PATH
from PES import NUM_SEQUENCES
from PES import LOBBY_PLAYERS
from PES.src.pygameMediator import Agent
from PES.ext.pandemic import Pandemic

from PES.src.exp_utils import calculate_normalised_final_severity_performance_metric,get_sequence_severity_from_allocations
from PES.src.exp_utils import get_updated_severity,get_sequence_severity_from_allocations

from PES.src.Agent import adjust_response_decay, boltzmann_decay 

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


        s = numpy.loadtxt( os.path.join( INPUTS_PATH, 'sequence_lengths.csv'), delimiter = ',' )


        decays = []

        for i in range(64):
            g_seq_no = i + 1 
            decay = boltzmann_decay( g_seq_no )

            decays.append( decay )

            for trials in range(int(s[i])):
                
                resp = random.randrange(MAX_ALLOCATABLE_RESOURCES+1)
                resources_left = random.randrange(AVAILABLE_RESOURCES_PER_SEQUENCE)
                printinfo ( f'-->Current Response {resp}')
                resp = adjust_response_decay( resp, decay, resources_left )
                printinfo ( f'New Adjusted Response {resp}')

                assert resp>=0 and resp<=MAX_ALLOCATABLE_RESOURCES, "Calculated Adjusted Response is out of bounds."
                

        plt.plot( numpy.arange( 64 ), decays )
        plt.show()


if __name__ == '__main__':
    t = Test_()
    t.test_()
