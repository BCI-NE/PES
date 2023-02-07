'''
PES - Pandemic Experiment Scenario

Train the Neural Network Agent that is used for the PES experiments, to provide online responses and confidence values.
'''
import os,sys
import numpy as np
import pickle
from pickle import dumps, loads
import tensorflow as tf
from tensorflow.keras import optimizers
print(tf.__version__)


from PES.src.Agent import *

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

# Use the empirical distributions of the archetypal game to generate others with the same distributions.
game = Game(number_cities_prob, severity_prob)
model = Model([4,4],10)
optimizer = optimizers.Adam()

games = 20000

log=[]
damage = np.zeros((games,))
for i in range(games):
    severities = tf.constant(game(), dtype=tf.float32)
    damage[i] = train_one_game(model, optimizer, severities, initial_resources, log=log)

model.save()
print('Model Saved in weights file.')

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




