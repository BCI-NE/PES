'''
PES - Pandemic Experiment Scenario

Based on a previous recorded data, it generates a RL-Agent that tries to play as close as possible as a player had played in the game.
This can be used to generate artificial agents that, somehow, replicates what a real human would have done during a real game.

Output:
    player_q.npy - This file contains the trained Q-Table that can be used to decide what to do on a real game mimicking the participant.
'''

from hashlib import new
import numpy as np
import matplotlib.pyplot as plt
import PIL.Image as Image
import gym
import random
import os
import csv
from gym import Env, spaces

import time

DATA_PATH = ''

# @FIXME These functions are copy-pasted here.  They belong to Exp3c analysis code.
def getSubjectsData( DataPath = DATA_PATH, SubjectFiles='', SkipFirstLine=True  ):
    AllConfidences      = []
    AllAllocations      = []
    AllPressEvents      = []
    AllReleaseEvents    = []

    for SubjectFile in SubjectFiles:
            InitialSeverities, Confidences, Allocations, PressEvents, ReleaseEvents = getSubjectData( SubjectFile, SkipFirstLine = SkipFirstLine, DataPath = DataPath)

            AllConfidences.append(  Confidences )
            AllAllocations.append(  Allocations)
            AllPressEvents.append(  PressEvents)
            AllReleaseEvents.append(    ReleaseEvents)

    return InitialSeverities, AllConfidences, AllAllocations, AllPressEvents, AllReleaseEvents


def getSubjectData( SubjectFile, SkipFirstLine, DataPath = DATA_PATH):

    FullSubjectFile = os.path.abspath( os.path.join (DataPath, SubjectFile) )

    CsvFile     = open( FullSubjectFile, 'r')
    CsvReader   = csv.reader( CsvFile )
    RawData     = list( CsvReader )

    if SkipFirstLine:
        Headers     = RawData[0]
        RawData     = RawData[1:]

    OuterLen    =   len( RawData )
    InnerLen    =   len( RawData[0] )

    CsvFile.close()

    Data = []

    for i in range( OuterLen ):
        Data.append( [] )
        for j in range( InnerLen ):
            Data[i].append( float(  RawData[i][j] ))

    Data = np.array( Data )

    InitialSeverities       = Data[:,0]
    Confidences             = Data[:,2]
    Allocations             = Data[:,1]
    PressEvents             = Data[:,3]
    ReleaseEvents           = Data[:,4]

    return InitialSeverities, Confidences, Allocations, PressEvents, ReleaseEvents

# @FIXME Hardcoded the payerid
InitialSeverities, Confidences, Allocations, PressEvents, ReleaseEvents = getSubjectData('PES_full_responses_165.txt',SkipFirstLine=True, DataPath='PES/outputs/')

from pandemic import Pandemic
from pandemic import run_experiment
from pandemic import QLearning

from PES import VERBOSE
from PES import INPUTS_PATH
from PES import AVAILABLE_RESOURCES_PER_SEQUENCE


from PES.src.pygameMediator import convert_globalseq_to_seqs
from PES.src.exp_utils import calculate_normalised_final_severity_performance_metric
from PES.src.exp_utils import get_updated_severity

# Read the "cannonical" sequence of sequences.
trials_per_sequence = np.loadtxt(os.path.join( INPUTS_PATH,'sequence_lengths.csv'), delimiter=',')
all_severities = np.loadtxt(os.path.join( INPUTS_PATH, 'initial_severity.csv'), delimiter=',')
print(trials_per_sequence.shape, all_severities.shape, sum(trials_per_sequence))

sevs = convert_globalseq_to_seqs(trials_per_sequence, all_severities)

print(len(sevs))

# Get the distribution of the sequences in the cannonical configuration
val_cities, count_cities = np.unique(trials_per_sequence, return_counts=True)
val_severity, count_severity = np.unique(all_severities, return_counts=True)
number_cities_prob = np.asarray((val_cities, count_cities/len(trials_per_sequence))).T
severity_prob = np.asarray((val_severity, count_severity/len(all_severities))).T


# Let's train the RL-Agent based on the responses that the real Player provided.
env = Pandemic()

R = np.random.uniform(low = 0, high = 0, 
                        size = (    env.available_resources_states, 
                                    env.trial_no_states, 
                                    env.severity_states,
                                        env.action_space.n))

def qf(env, state):
    action = int(env.sample())
    R[state[0], state[1], state[2], action] = 100
    return action

# Allocations that the Player performed
allcs = convert_globalseq_to_seqs(trials_per_sequence, Allocations)

# Rerun the pandemic scenario using the responses from the player
#  Use that info to create the 'R' reward matriz 
seqs, perfs = run_experiment(env, qf, False, trials_per_sequence,sevs, True,allocs=allcs)

env.number_cities_prob = number_cities_prob
env.severity_prob = severity_prob
env.verbose = False

# Use now the Reward matrix R, to provide rewards the agent randomly selects the SAME decision
#  that the player actually made.
if os.path.isfile( os.path.join( INPUTS_PATH,'player_q.npy')):
    Q = np.load( os.path.join( INPUTS_PATH, 'player_q.npy'))
    rewards = np.load( os.path.join( INPUTS_PATH, 'player_rewards.npy'))
else:
    rewards, Q = QLearning(env, 0.2, 0.9, 0.8, 0, 500000,True,R)
    np.save( os.path.join ( INPUTS_PATH, 'player_q.npy'), Q)
    np.save( os.path.join ( INPUTS_PATH, 'player_rewards.npy'), rewards)



# Plot Rewards
plt.plot(100*(np.arange(len(rewards)) + 1), rewards)
plt.xlabel('Episodes')
plt.ylabel('Average Reward')
plt.title('Average Reward vs Episodes')
#plt.savefig('rewards.pdf')     
#plt.close()  
plt.show()

def qf2(env,state):
    return np.argmax(Q[state[0], state[1],int(state[2])])

seqs2, perfs2 = run_experiment(env, qf2, False, trials_per_sequence,sevs)

# Plot Rewards
plt.plot(seqs, 'g')
plt.plot(seqs2, 'r')
plt.xlabel('Trial')
plt.ylabel('Final severity achieved')
plt.title('Performance on each sequence')
#plt.savefig('rewards.pdf')     
#plt.close()  
plt.show()

fig = plt.figure(figsize=(10,5))
plt.plot(perfs, 'g', label='Player')
plt.plot(perfs2, 'r', label='RL-Agent')
plt.ylabel('Normalised final severity performances')
plt.xlabel('Trial')
plt.ylim(0,1.05)
plt.xlim(0,64)
plt.grid()
plt.legend()
plt.show()

cumperfs1 = np.cumsum(perfs)
cumperfs2 = np.cumsum(perfs2)


fig = plt.figure(figsize=(10,5))
plt.plot(cumperfs1, 'g', label='Payer')
plt.plot(cumperfs2, 'r', label='RL-Agent')
plt.ylabel('Cumulative normalised final severity performances')
plt.xlabel('Trial')
plt.grid()
plt.legend()
plt.ylim(0,64)
plt.xlim(0,64)
plt.show()

# Now let's check how the RL-Agent performs in a random set of sequences.
env = Pandemic()

env.number_cities_prob = number_cities_prob
env.severity_prob = severity_prob

def qf3(env,state):
    return np.argmax(Q[state[0], state[1],int(state[2])])

seqs_rl_agent, perfs_rl_agent = run_experiment(env, qf3, True)


# Plot Rewards
plt.plot(seqs, 'g', label='Player')
plt.plot(seqs_rl_agent, 'r')
plt.xlabel('Trial')
plt.ylabel('Final severity achieved')
plt.title('Performance on each sequence on a Random set of Sequences')
#plt.savefig('rewards.pdf')     
#plt.close()  
plt.show()

fig = plt.figure(figsize=(10,5))
plt.plot(perfs, 'g', label='Player')
plt.plot(perfs_rl_agent, 'r', label='RL-Agent')
plt.ylabel('Normalised final severity performances')
plt.xlabel('Trial')
plt.ylim(0,1.0)
plt.xlim(0,64)
plt.grid()
plt.legend()
plt.show()

cumperfs1 = np.cumsum(perfs)
cumperfs2 = np.cumsum(perfs_rl_agent)


fig = plt.figure(figsize=(10,5))
plt.plot(cumperfs1, 'g', label='Player')
plt.plot(cumperfs2, 'r', label='RL-Agent')
plt.ylabel('Cumulative normalised final severity performances')
plt.xlabel('Trial')
plt.grid()
plt.legend()
plt.ylim(0,64)
plt.xlim(0,64)
plt.show()

# Allocations that the Player performed
confs = convert_globalseq_to_seqs(trials_per_sequence, Confidences)


fig = plt.figure(figsize=(10,5))
plt.plot(Confidences, 'g', label='Confidences')
plt.ylabel('Confidences')
plt.xlabel('Trial')
plt.grid()
plt.legend()
plt.ylim(0,1)
plt.xlim(0,360)
plt.show()
