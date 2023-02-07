'''
PES - Pandemic Experiment Scenario

Generate the initial sequences that are used for training for PES.

'''
import os,sys
import numpy as np
import pickle
from pickle import dumps, loads
import tensorflow as tf
from tensorflow.keras import optimizers
print(tf.__version__)


from PES.src.Agent import *
from PES.src.exp_utils import calculate_normalised_final_severity_performance_metric
from PES.src.exp_utils import get_updated_severity


from PES import VERBOSE
from PES import INPUTS_PATH
from PES import AVAILABLE_RESOURCES_PER_SEQUENCE

initial_resources = tf.constant(AVAILABLE_RESOURCES_PER_SEQUENCE-9, dtype=tf.float32)
trials_per_sequence = np.loadtxt(os.path.join( INPUTS_PATH,'sequence_lengths.csv'), delimiter=',')
all_severities = np.loadtxt(os.path.join( INPUTS_PATH, 'initial_severity.csv'), delimiter=',')
print(trials_per_sequence.shape, all_severities.shape, sum(trials_per_sequence))

val_cities, count_cities = np.unique(trials_per_sequence, return_counts=True)
val_severity, count_severity = np.unique(all_severities, return_counts=True)
number_cities_prob = np.asarray((val_cities, count_cities/len(trials_per_sequence))).T
severity_prob = np.asarray((val_severity, count_severity/len(all_severities))).T
print(number_cities_prob.T)
print(severity_prob.T)

import matplotlib.pyplot as plt

fig = plt.figure(figsize=(10,5))
plt.bar(val_cities, count_cities)
plt.ylabel('#')
plt.xlabel('Seq Lengths')
plt.xticks(val_cities)
plt.show()



fig = plt.figure(figsize=(10,5))
plt.bar(val_severity, count_severity)
plt.ylabel('# Cities')
plt.xlabel('Severities')
plt.show()

# The idea is generate 64 sequences, and verify how an average player performs.

number_cities = int(np.random.choice(number_cities_prob[:,0], p=(number_cities_prob[:,1])))
severities = np.random.choice(severity_prob[:,0], size=(number_cities,), p=severity_prob[:,1])

print(number_cities)
print(severities)


lengths = []
sevs = []

performances = []

# Get sequence lengths with random severities to sort out the easy from the toughs ones.
for i in range(1000):
    number_cities = int(np.random.choice(number_cities_prob[:,0], p=(number_cities_prob[:,1])))
    severities = np.random.choice(severity_prob[:,0], size=(number_cities,), p=severity_prob[:,1])
    allocations = np.ones((number_cities,))*5.

    lengths.append( number_cities )
    sevs.append( severities )

    final_severities = get_updated_severity(number_cities, allocations, severities)
    perf = calculate_normalised_final_severity_performance_metric( final_severities, severities)
    performances.append(perf[0])


fig = plt.figure(figsize=(10,5))
plt.plot(performances)
plt.ylabel('Normalised final severity performances')
plt.xlabel('Trial')
plt.show()

performances = np.asarray(performances)
lengths = np.asarray(lengths)
sevs = np.asarray(sevs)

resort = np.argsort( performances )

practice_lengths = lengths[ resort[ [ 1,1,180,181,-2,-1,-10,-10] ] ]
practice_severities = sevs[ resort[ [ 1,1,180,181,-2,-1,-10,-10] ] ]
print(practice_lengths)
print(practice_severities)


sevs_count = [len(s) for s in practice_severities]

print('Length sum: %03e' % np.sum(practice_lengths) )
print('Severities: %03e' % np.sum(sevs_count) )


assert np.sum(practice_lengths) == np.sum(sevs_count), 'Length should match.  Something went wrong.'

np.savetxt(os.path.join( INPUTS_PATH, 'practice_lengths.csv'), practice_lengths, fmt='%d',delimiter=',')
with open(os.path.join( INPUTS_PATH, 'practice_severity.csv'), 'w') as txt:
    txt.write('\n'.join(['\n'.join(str(s) for s in sev) for sev in practice_severities]))
    txt.write('\n')



