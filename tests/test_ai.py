import unittest, unittest.mock
import pygame
import glob
import math
import numpy
import tensorflow as tf



import sys, os

from PES.src.pygameMediator import entropy, calculate_agent_response_and_confidence
from PES.src.pygameMediator import convert_globalseq_to_seqs

from PES import VERBOSE
from PES import MAX_ALLOCATABLE_RESOURCES
from PES import MIN_ALLOCATABLE_RESOURCES
from PES import INPUTS_PATH
from PES import NUM_SEQUENCES
from PES.src.pygameMediator import Agent


# --------------------------------------------------------
# Print a nice header identifying the module under testing
# --------------------------------------------------------

class Test_( unittest.TestCase ):   # Note: the name 'Test_' guarantees
                                    # (alphabetically) this TestCase is run
                                    # before other TestCases in this module

    def setUpClass():
        print(                                                          )
        print( "******************************************************" )
        print( "*** Unit tests for packagename.src.ai module" )
        print( "******************************************************" )
        print(                                                          )
    def tearDownClass ():   print( )


  # add dummy test so that the testcase is picked up during discovery
    def test_( self ): 
        model = Agent.Model([4,4],10)
        model.load()

        resources_left = 40
        session_no = 0
        sequence_no = 0 
        trial_no = 0

        sequenceLengthCsv = os.path.join( INPUTS_PATH, 'sequence_lengths.csv')
        sequence_length = numpy.loadtxt( sequenceLengthCsv, delimiter=',')
        InitialSeverityCsv = os.path.join ( INPUTS_PATH, 'initial_severity.csv')
        first_severity = numpy.loadtxt( InitialSeverityCsv )

        sevs = convert_globalseq_to_seqs(sequence_length, first_severity)
        
        t_resources_remaining   = tf.Variable(resources_left, dtype=tf.float32)
        t_trial_no              = tf.Variable(trial_no, dtype=tf.float32)
        t_sevs                  = tf.Variable( sevs[session_no * NUM_SEQUENCES + sequence_no][trial_no], dtype=tf.float32)
        
        resp = model( t_sevs, t_trial_no, t_resources_remaining).numpy()
        confidence, resp = calculate_agent_response_and_confidence( model, sevs[session_no * NUM_SEQUENCES + sequence_no][trial_no], trial_no, resources_left) 

        resp = round(resp)

        rt_hold = 0.10
        rt_release = 0.23

        #pygame.time.wait(3000)

        movement = []


        print ( confidence )
        print( resp )
        print( rt_hold )
        print( rt_release )
        print( movement )


        print ( 'Done')


if __name__ == '__main__':
    t = Test_()
    t.test_()

