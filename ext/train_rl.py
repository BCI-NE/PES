'''
PES - Pandemic Experiment Scenario

This script can be used to train a Reinforcement Learning Agent that will try to optimize its own performance on the pandemic scenario.
It takes the parameters of the experiment directly from CONFIG.py 

The trained Q-Table and the log of the obtained rewards are stored into the INPUTS_PATH directory.  They can be used later to use the trained agent.
'''

from hashlib import new
import numpy
import cv2
import matplotlib.pyplot as plt
import PIL.Image as Image
import gym
import random
import os 
import tensorflow as tf

from gym import Env, spaces
import time


from PES import VERBOSE
from PES import INPUTS_PATH
from PES import AVAILABLE_RESOURCES_PER_SEQUENCE

from PES.src.pygameMediator import convert_globalseq_to_seqs
from PES.src.exp_utils import calculate_normalised_final_severity_performance_metric
from PES.src.exp_utils import get_updated_severity

from PES.src import Agent
from PES.src.Agent import agent_meta_cognitive
from PES.src.Agent import adjust_response_decay, boltzmann_decay
from PES.ext.pandemic import Pandemic, rl_agent_meta_cognitive, run_experiment, QLearning  
from PES.ext.tools import plot_confidences 
from PES.ext.tools import humanise_this_reported_confidence 

if __name__=='__main__':
        
    trials_per_sequence = numpy.loadtxt(os.path.join( INPUTS_PATH,'sequence_lengths.csv'), delimiter=',')
    all_severities = numpy.loadtxt(os.path.join( INPUTS_PATH, 'initial_severity.csv'), delimiter=',')
    print(trials_per_sequence.shape, all_severities.shape, sum(trials_per_sequence))

    sevs = convert_globalseq_to_seqs(trials_per_sequence, all_severities)

    val_cities, count_cities = numpy.unique(trials_per_sequence, return_counts=True)
    val_severity, count_severity = numpy.unique(all_severities, return_counts=True)
    number_cities_prob = numpy.asarray((val_cities, count_cities/len(trials_per_sequence))).T
    severity_prob = numpy.asarray((val_severity, count_severity/len(all_severities))).T

    env = Pandemic()

    def qf(env, state, seqid):
        return env.sample()

    seqs1, perfs1 = run_experiment(env, qf, False, trials_per_sequence,sevs)

    plt.plot(seqs1)
    plt.xlabel('Trial')
    plt.ylabel('Final severity achieved')
    plt.title('Performance on each sequence for a Random Player')
    #plt.savefig('rewards.pdf')     
    #plt.close()  
    plt.show()

    fig = plt.figure(figsize=(10,5))
    plt.plot(perfs1)
    plt.ylabel('Normalised final severity performances for a Random Player')
    plt.xlabel('Trial')
    plt.ylim(0,1)
    plt.show()


    env = Pandemic()

    env.number_cities_prob = number_cities_prob
    env.severity_prob = severity_prob
    env.verbose = False

    # Run Q-learning algorithm
    if os.path.isfile(os.path.join( INPUTS_PATH,'q3.npy')):
        Q = numpy.load(os.path.join( INPUTS_PATH,'q3.npy'))
        rewards = numpy.load(os.path.join( INPUTS_PATH,'rewards.npy'))
    else:
        rewards, Q, confsrl = QLearning(env, 0.2, 0.9, 0.8, 0, 10000000) # 100000000
        numpy.save( os.path.join( INPUTS_PATH,'q3.npy'), Q)
        numpy.save( os.path.join( INPUTS_PATH,'rewards3.npy'), rewards)


    # Plot Rewards
    plt.plot(100*(numpy.arange(len(rewards)) + 1), rewards)
    plt.xlabel('Episodes')
    plt.ylabel('Average Reward')
    plt.title('RL-Agent to minimize severity: Average Rewards vs Episodes')
    #plt.savefig('rewards.pdf')     
    #plt.close()  
    plt.show()


    if (False):
        confsrl = []

        def qf(env,state, seqid):
            response, confidence, rt_hold, rt_release = rl_agent_meta_cognitive(Q[state[0], state[1], int(state[2])], state[0], 10000)

            if (state[0]==0):
                confidence = -1.0
            
            confsrl.append( confidence )
            return response
            #return numpy.argmax(Q[state[0], state[1],int(state[2])])




        seqs, perfs = run_experiment(env,qf, False, trials_per_sequence,sevs)


        # Plot Rewards
        plt.plot(seqs, 'b', label='RL-Agent')
        plt.xlabel('Trial')
        plt.ylabel('Final severity achieved')
        plt.title('Performance on each sequence')
        plt.legend()
        #plt.savefig('rewards.pdf')     
        #plt.close()  
        plt.show()

        fig = plt.figure(figsize=(10,5))
        plt.plot(perfs, 'b', label='RL-Agent')
        plt.ylabel('Normalised final severity performances')
        plt.xlabel('Trial')
        plt.ylim(0,1)
        plt.xlim(0,64)
        plt.grid()
        plt.legend()
        plt.show()

        cumperfs  = numpy.cumsum(perfs)

        Domain = numpy.arange(1,1+64)
        fig = plt.figure(figsize=(10,5))
        plt.plot(cumperfs/Domain, 'b', label='RL-Agent')
        plt.ylabel('Cumulative normalised final severity performances')
        plt.xlabel('Trial')
        plt.grid()
        plt.legend()
        plt.ylim(0.5,1)
        plt.xlim(0,64)
        plt.show()


    if (True):
        fig = plt.figure(figsize=(16,4))
        plt.scatter(numpy.asarray(range(len(confsrl))), confsrl)
        plt.title('Reported confidences from the RLAgent')
        plt.ylim(-0.1,1.1)
        plt.xlim(0,360)
        plt.show()


        confsrl = numpy.asarray( confsrl, dtype=numpy.float32)

        val_confidences = numpy.arange(11, dtype=numpy.float32) / 10.0
        confsrl_hist = numpy.histogram( confsrl, bins = val_confidences)


        plot_confidences(confsrl, 'Confidences')

        numpy.save( os.path.join( INPUTS_PATH, 'confsrl.npy'), confsrl )

        confsrl = confsrl [ confsrl != -1 ]


        print ( confsrl)

        I = confsrl 
        rescaled = (I - numpy.min(I) )* (  (1.0 - 0.0) / ( numpy.max(I) - numpy.min(I)) ) + 0.0
        remapconfrl= numpy.clip( rescaled, 0.0, 1.0)



        print (remapconfrl.shape )


        fig = plt.figure(figsize=(16,4))
        plt.scatter(numpy.asarray(range(remapconfrl.shape[0])), remapconfrl)
        plt.ylabel('Confidences')
        plt.xlabel('Trials')
        plt.ylim(-0.1,1.1)
        plt.xlim(0,360)
        plt.show()

        plot_confidences(remapconfrl, 'Remapped Confidences')


