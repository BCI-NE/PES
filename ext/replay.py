'''
PES - Pandemic Experiment Scenario

Replay any previous PES game
'''

from hashlib import new
import numpy as np
import cv2
import matplotlib.pyplot as plt; plt.style.use('ggplot')
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

    AllAgentAllocations = []
    AllAgentConfidences = []

    for SubjectFile in SubjectFiles:
            InitialSeverities, Confidences, Allocations, PressEvents, ReleaseEvents, AgentAllocations, AgentConfidences = getSubjectData( SubjectFile, SkipFirstLine = SkipFirstLine, DataPath = DataPath)

            AllConfidences.append(  Confidences )
            AllAllocations.append(  Allocations)
            AllPressEvents.append(  PressEvents)
            AllReleaseEvents.append(    ReleaseEvents)

            AgentAllocations.append( AgentAllocations )
            AgentConfidences.append( AgentConfidences )

    return InitialSeverities, AllConfidences, AllAllocations, AllPressEvents, AllReleaseEvents, AllAgentAllocations, AllAgentConfidences


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

    InitialSeverities       = Data[:,1]
    Confidences             = Data[:,3]
    Allocations             = Data[:,2]
    PressEvents             = Data[:,4]
    ReleaseEvents           = Data[:,5]

    AgentAllocations        = Data[:,6]
    AgentConfidences        = Data[:,7]

    return InitialSeverities, Confidences, Allocations, PressEvents, ReleaseEvents, AgentAllocations, AgentConfidences

# @FIXME Hardcoded the player id
InitialSeverities, Confidences, Allocations, PressEvents, ReleaseEvents, AgentAllocations, AgentConfidences = getSubjectData('003_responses.txt',SkipFirstLine=True, DataPath='PES/outputs/')

from pandemic import Pandemic
from pandemic import run_experiment
from pandemic import QLearning

from PES import VERBOSE
from PES import INPUTS_PATH


from PES.src.pygameMediator import convert_globalseq_to_seqs
from PES.src.exp_utils import calculate_normalised_final_severity_performance_metric
from PES.src.exp_utils import get_updated_severity

# Read the "cannonical" sequence of sequences.
trials_per_sequence = np.loadtxt(os.path.join( INPUTS_PATH,'sequence_lengths.csv'), delimiter=',')
all_severities = np.loadtxt(os.path.join( INPUTS_PATH, 'initial_severity.csv'), delimiter=',')

sevs = convert_globalseq_to_seqs(trials_per_sequence, all_severities)

# Let's train the RL-Agent based on the responses that the real Player provided.
env = Pandemic()

# Just picking the provided value for the allocation.
def qf(env, state):
    action = int(env.sample())
    return action


Confidences[Confidences == -1] = 0.0
AgentConfidences[AgentConfidences == -1] = 0.0

TrialConfidences    = np.c_[Confidences, AgentConfidences]
Allocs              = np.c_[Allocations, AgentAllocations]
JointAllocations = np.mean( Allocs, axis=1 )
nzRowIndices = (TrialConfidences != 0).any( axis = 1) 
JointAllocations[ nzRowIndices ] = np.average( Allocs[ nzRowIndices, : ], weights = TrialConfidences[ nzRowIndices, : ] , axis=1)

# Allocations that the Player performed
allcs = convert_globalseq_to_seqs(trials_per_sequence, Allocations)
agentallcs = convert_globalseq_to_seqs(trials_per_sequence, AgentAllocations)
jointallcs = convert_globalseq_to_seqs(trials_per_sequence, JointAllocations)

# Rerun the pandemic scenario using the responses from the player
#  Use that info to create the 'R' reward matriz 
seqs, perfs             = run_experiment(env, qf, False, trials_per_sequence,sevs, True,allocs=allcs)
seqs_nn, perfs_nn       = run_experiment(env, qf, False, trials_per_sequence, sevs, True, allocs=agentallcs)
seqs_joint, perfs_joint = run_experiment(env, qf, False, trials_per_sequence,sevs, True,allocs=jointallcs)

#seqs2 = seqs
#perfs2 = perfs


# Plot Raw Severities (i.e. death people)
fig = plt.figure(figsize=(8,6))
plt.plot(seqs, 'g', label='Human')
plt.plot(seqs_nn, 'r', label='AI')
plt.plot(seqs_joint, 'b', label='Joint')
plt.xlabel('Trial', fontsize=16)
plt.ylabel('Final severity achieved', fontsize=16)
plt.title('Performance on each sequence', fontsize=16)
plt.legend(fontsize=16)
plt.savefig('rawperformance.pdf')     
#plt.close()  
plt.show()

fig = plt.figure(figsize=(8,6))
plt.plot(perfs, 'g', label='Human')
plt.plot(perfs_nn, 'r', label='AI')
plt.plot(perfs_joint, 'b', label='Joint')
plt.ylabel('Performance', fontsize=16)
plt.xlabel('Trial', fontsize=16)
plt.ylim(0,1.05)
plt.xlim(0,64)
#plt.grid()
plt.legend(fontsize=16)
plt.savefig('performance.pdf')
plt.show()

cumperfs_human  = np.cumsum(perfs)
cumperfs_nn     = np.cumsum(perfs_nn)
cumperfs_joint  = np.cumsum(perfs_joint)


fig = plt.figure(figsize=(8,6))
plt.plot(cumperfs_human, 'g', label='Human')
plt.plot(cumperfs_nn, 'r', label='AI')
plt.plot(cumperfs_joint, 'b', label='Joint')
plt.ylabel('Cumulative Performance', fontsize=16)
plt.xlabel('Trial', fontsize=16)
#plt.grid()
plt.legend(fontsize=16)
plt.ylim(0,64)
plt.xlim(0,64)
plt.savefig('cumulative.pdf')
plt.show()
