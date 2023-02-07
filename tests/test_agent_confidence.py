import unittest, unittest.mock
import pygame
import glob
import math
import numpy 
import tensorflow as tf

import sys, os

from PES.src.pygameMediator import calculate_agent_response_and_confidence
from PES.src.pygameMediator import convert_globalseq_to_seqs

from PES.src import lobbyManager
from PES.src import exp_utils

from PES.src import log_utils

from PES import RESPONSE_TIMEOUT, printinfo, printstatus


from PES import VERBOSE
from PES import MAX_ALLOCATABLE_RESOURCES
from PES import MIN_ALLOCATABLE_RESOURCES
from PES import INPUTS_PATH
from PES import NUM_SEQUENCES
from PES import LOBBY_PLAYERS
from PES.src.pygameMediator import Agent
from PES.ext.pandemic import Pandemic, rl_agent_meta_cognitive
from PES.src.Agent import agent_meta_cognitive
from PES.ext.tools import entropy, entropy_from_pdf


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
        print( "*** Unit tests for packagename.src.ai module" )
        print( "******************************************************" )
        print(                                                          )
    def tearDownClass ():   print( )


    def test_( self ): 
        model = Agent.Model([4,4],10)
        model.load()

        severity = 8
        city_number = 4
        resources_left = 2

        resources_remaining = tf.Variable( resources_left, dtype=tf.float32)

        action = model( severity, city_number, resources_remaining).numpy()

        print( f'Original Decision:{action}')

        response, confidence, rt_hold, rt_release = agent_meta_cognitive(action, MAX_ALLOCATABLE_RESOURCES+1, resources_left,RESPONSE_TIMEOUT)

        print( f'Response:{response}')
        print( f'Confidence:{confidence}')
        print( f'Response Time Hold:{rt_hold}')
        print( f'Response Time Release:{rt_release}')

        assert response>=0 and response <= MAX_ALLOCATABLE_RESOURCES, 'Invalid Response value for current configuration'
        assert confidence>=0 and confidence <=1, 'Invalid reported confidence'
        assert rt_release > rt_hold, 'Release time must be bigger than hold time'
        assert rt_release <= RESPONSE_TIMEOUT and rt_hold <= RESPONSE_TIMEOUT, 'The response values cannot be greater than the response timeout'



    def test_1(self):
        Q = numpy.load( os.path.join( INPUTS_PATH, 'player_q.npy'))
        rewards = numpy.load( os.path.join( INPUTS_PATH, 'player_rewards.npy'))


        ##print( numpy.linspace(MIN_ALLOCATABLE_RESOURCES,MAX_ALLOCATABLE_RESOURCES, 11) )
        #print( numpy.ones((11,) ) )
        #M_entropy = entropy(numpy.linspace(MIN_ALLOCATABLE_RESOURCES,MAX_ALLOCATABLE_RESOURCES, 11), bins=MAX_ALLOCATABLE_RESOURCES-MIN_ALLOCATABLE_RESOURCES+1)
        #m_entropy = entropy(numpy.ones((11,)), bins=MAX_ALLOCATABLE_RESOURCES-MIN_ALLOCATABLE_RESOURCES+1)
         
        #print( f'High:{M_entropy}' )
        #print( f'Low: {m_entropy}' )

        severity = 8
        city_number = 2
        resources_left = 2

        response, confidence, rt_hold, rt_release = rl_agent_meta_cognitive(Q[resources_left, city_number,int(severity)],resources_left,RESPONSE_TIMEOUT)

        #op = [0.045, 0.035, 0.03,  0.032, 0.029, 0.031, 0.03,  0.033, 0.03,  0.032, 0.033]
        #entrp = ent( op )
        options = Q[resources_left, city_number,int(severity)]
        print( f'Response:{response}')
        print( f'Confidence:{confidence}')
        print( f'Response Time Hold:{rt_hold}')
        print( f'Response Time Release:{rt_release}')

        assert response>=0 and response <= MAX_ALLOCATABLE_RESOURCES, 'Invalid Response value for current configuration'
        assert confidence>=0 and confidence <=1, 'Invalid reported confidence'
        assert rt_release > rt_hold, 'Release time must be bigger than hold time'
        assert rt_release <= RESPONSE_TIMEOUT and rt_hold <= RESPONSE_TIMEOUT, 'The response values cannot be greater than the response timeout'


    def test_2(self):
        Q = numpy.load( os.path.join( INPUTS_PATH, 'q.npy'))
        rewards = numpy.load( os.path.join( INPUTS_PATH, 'rewards.npy'))


        u_dist = numpy.zeros((11,),)
        u_dist[0] = 1
        print( f'Monotonical increasing distribution: {numpy.linspace(MIN_ALLOCATABLE_RESOURCES,MAX_ALLOCATABLE_RESOURCES, 11)}' )
        print( f'Uniform Distribution: {numpy.ones((11,) )}' )
        print( f'Univaluated Distribution: {u_dist}')
        M_entropy = entropy(numpy.linspace(MIN_ALLOCATABLE_RESOURCES,MAX_ALLOCATABLE_RESOURCES, 11), bins=MAX_ALLOCATABLE_RESOURCES-MIN_ALLOCATABLE_RESOURCES+1)
        m_entropy = entropy(numpy.ones((11,)), bins=MAX_ALLOCATABLE_RESOURCES-MIN_ALLOCATABLE_RESOURCES+1)
        u_entropy  = entropy(u_dist, bins=MAX_ALLOCATABLE_RESOURCES-MIN_ALLOCATABLE_RESOURCES+1)

        print( f'Lowest:{u_entropy}')
        print( f'Middle:{M_entropy}' )
        print( f'Highest: {m_entropy}' )



    def test_3(self):

        Q = numpy.load( os.path.join( INPUTS_PATH, 'q.npy'))
        rewards = numpy.load( os.path.join( INPUTS_PATH, 'rewards.npy'))


        u_dist = numpy.zeros((11,),)
        u_dist[0] = 1
        print( f'Monotonical increasing distribution: {numpy.linspace(MIN_ALLOCATABLE_RESOURCES,MAX_ALLOCATABLE_RESOURCES, 11)}' )
        print( f'Uniform Distribution: {numpy.ones((11,) )}' )
        print( f'Univaluated Distribution: {u_dist}')
        M_entropy = entropy(numpy.linspace(MIN_ALLOCATABLE_RESOURCES,MAX_ALLOCATABLE_RESOURCES, 11), bins=MAX_ALLOCATABLE_RESOURCES-MIN_ALLOCATABLE_RESOURCES+1)

        print( f'Lowest :{ entropy_from_pdf( u_dist ) }')
        print( f'Middle :{ entropy_from_pdf( numpy.linspace( MIN_ALLOCATABLE_RESOURCES, MAX_ALLOCATABLE_RESOURCES, 11) ) }')
        print (f'Highest:{ entropy_from_pdf( numpy.ones((11,)) ) }')

        print('---------')

        M_entropy = entropy_from_pdf( numpy.ones((11,)) )
        m_entropy = entropy_from_pdf( numpy.linspace( MIN_ALLOCATABLE_RESOURCES, MAX_ALLOCATABLE_RESOURCES, 11) )
        u_entropy = entropy_from_pdf( u_dist )



        assert M_entropy > m_entropy > u_entropy, 'Entropy calculation went wrong.'

        severity = 8
        city_number = 2
        resources_left = 2

        response, confidence, rt_hold, rt_release = rl_agent_meta_cognitive(Q[resources_left, city_number,int(severity)],resources_left,RESPONSE_TIMEOUT)

        #op = [0.045, 0.035, 0.03,  0.032, 0.029, 0.031, 0.03,  0.033, 0.03,  0.032, 0.033]
        #entrp = ent( op )
        options = Q[resources_left, city_number,int(severity)]
        print( f'Response:{response}')
        print( f'Confidence:{confidence}')
        print( f'Response Time Hold:{rt_hold}')
        print( f'Response Time Release:{rt_release}')

        assert response>=0 and response <= MAX_ALLOCATABLE_RESOURCES, 'Invalid Response value for current configuration'
        assert confidence>=0 and confidence <=1, 'Invalid reported confidence'
        assert rt_release > rt_hold, 'Release time must be bigger than hold time'
        assert rt_release <= RESPONSE_TIMEOUT and rt_hold <= RESPONSE_TIMEOUT, 'The response values cannot be greater than the response timeout'

    def test_4(self):

        Q = numpy.load( os.path.join( INPUTS_PATH, 'q.npy'))
        rewards = numpy.load( os.path.join( INPUTS_PATH, 'rewards.npy'))


        u_dist = numpy.zeros((11,),)
        u_dist[0] = 1
        print( f'Monotonical increasing distribution: {numpy.linspace(MIN_ALLOCATABLE_RESOURCES,MAX_ALLOCATABLE_RESOURCES, 11)}' )
        print( f'Uniform Distribution: {numpy.ones((11,) )}' )
        print( f'Univaluated Distribution: {u_dist}')
        M_entropy = entropy(numpy.linspace(MIN_ALLOCATABLE_RESOURCES,MAX_ALLOCATABLE_RESOURCES, 11), bins=MAX_ALLOCATABLE_RESOURCES-MIN_ALLOCATABLE_RESOURCES+1)

        print( f'Lowest :{ entropy_from_pdf( u_dist ) }')
        print( f'Middle :{ entropy_from_pdf( numpy.linspace( MIN_ALLOCATABLE_RESOURCES, MAX_ALLOCATABLE_RESOURCES, 11) ) }')
        print (f'Highest:{ entropy_from_pdf( numpy.ones((11,)) ) }')

        print('---------')

        M_entropy = entropy_from_pdf( numpy.ones((11,)) )
        m_entropy = entropy_from_pdf( numpy.linspace( MIN_ALLOCATABLE_RESOURCES, MAX_ALLOCATABLE_RESOURCES, 11) )
        u_entropy = entropy_from_pdf( u_dist )



        assert M_entropy > m_entropy > u_entropy, 'Entropy calculation went wrong.'

        severity = 8
        city_number = 2
        resources_left = 10

        response, confidence, rt_hold, rt_release = rl_agent_meta_cognitive(Q[resources_left, city_number,int(severity)],resources_left,RESPONSE_TIMEOUT)
        confidence1 = confidence 
        #op = [0.045, 0.035, 0.03,  0.032, 0.029, 0.031, 0.03,  0.033, 0.03,  0.032, 0.033]
        #entrp = ent( op )
        options = Q[resources_left, city_number,int(severity)]


        print( f'Feasible options: {options}' )
        print( f'Response:{response}')
        print( f'Confidence:{confidence}')
        print( f'Response Time Hold:{rt_hold}')
        print( f'Response Time Release:{rt_release}')

        import matplotlib.pyplot as plt
        plt.bar(numpy.arange(11), options+numpy.abs(numpy.min(options)))
        plt.show()



        Q = numpy.load( os.path.join( INPUTS_PATH, 'q2.npy'))
 

        response, confidence, rt_hold, rt_release = rl_agent_meta_cognitive(Q[resources_left, city_number,int(severity)],resources_left,RESPONSE_TIMEOUT)
        confidence2 = confidence 
        #op = [0.045, 0.035, 0.03,  0.032, 0.029, 0.031, 0.03,  0.033, 0.03,  0.032, 0.033]
        #entrp = ent( op )
        options = Q[resources_left, city_number,int(severity)]


        print( f'Feasible options: {options}' )
        print( f'Response:{response}')
        print( f'Confidence:{confidence}')
        print( f'Response Time Hold:{rt_hold}')
        print( f'Response Time Release:{rt_release}')


        import matplotlib.pyplot as plt
        plt.bar(numpy.arange(11),options + numpy.abs( numpy.min(options) ) )
        plt.show()



        assert confidence2 < confidence1, 'As the second Q table is less trained, their reported confidence should be lower.'
        assert response>=0 and response <= MAX_ALLOCATABLE_RESOURCES, 'Invalid Response value for current configuration'
        assert confidence>=0 and confidence <=1, 'Invalid reported confidence'
        assert rt_release >= rt_hold, 'Release time must be bigger than hold time'
        assert rt_release <= RESPONSE_TIMEOUT and rt_hold <= RESPONSE_TIMEOUT, 'The response values cannot be greater than the response timeout'




if __name__ == '__main__':
    t = Test_()
    t.test_()
    t.test_1()
    t.test_3()
    t.test_4()
