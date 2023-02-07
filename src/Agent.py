"""
PES - Pandemic Experiment Scenario

Agent.py 

This is a basic implementation of a MLP with sigmoid activation function that optimize the neural weights to solve the Pandemic Scenario problem.

* The seed is fixed through random package.
* Game: this class generates random individual sequences of severities that follow the a specific distributions of length (i.e. number of cities) and severity values.
* damage_city: This is the function that implements the dynamic of the pandemic, and it is used as the loss function to optimize. 
* Reported Confidence: the remaining functions are used to add noise to the Agent's responses and to measure that noise as metacogntive information.
"""

import os
import numpy
import pickle
from pickle import dumps, loads
import tensorflow as tf
#from tensorflow.keras import optimizers
#print(tf.__version__)
import random

from .. import INPUTS_PATH
from .. import RESPONSE_MULTIPLIER
from .. import SEVERITY_MULTIPLIER
from .. import MAX_ALLOCATABLE_RESOURCES
#from .. import AGENT_NOISE_VARIANCE

from PES.ext.tools import humanise_this_reported_confidence, pick_human_reported_confidence  


AGENT_NOISE_VARIANCE = 2.0


# I am fixing a random seed to the generation of random responses for the NN-Agent because otherwise we loose the ability of generate predictable responses.
import random
#seed = input()
# Use me if you want to test with differnt neural networks
#random.seed(seed)
#random.seed(383831)

randominstance = random.Random()

def initseed(seed, noise):
    randominstance.seed( seed )
    global AGENT_NOISE_VARIANCE 
    AGENT_NOISE_VARIANCE= noise 


class Game():

    def __init__(self, number_cities_prob, severity_prob):
        '''
        2-D vector with each number of cities(trials) and the probability of appeareance of that number of trials
        2-D vector with a set of different severities and the probabilities for each one of them.  The number of generated
        trials will be produced from the number decided by the number_cities_prob
        '''
        self.number_cities_prob = number_cities_prob
        self.severity_prob = severity_prob

    def __call__(self):
        number_cities = int(numpy.random.choice(self.number_cities_prob[:,0], p=self.number_cities_prob[:,1]))
        severities = numpy.random.choice(self.severity_prob[:,0], size=(number_cities,), p=self.severity_prob[:,1])
        return severities




# create the neural network
class Model():


    def __init__(self, hidden_layers_sizes, output_range):
        self.Ws = []
        self.bs = []
        self.Weights_tfFile = os.path.join( INPUTS_PATH, 'weights.tf' )
        size_in = 3 # [severity, city_number, resources_remaining]
        # Weights Ws and biases bs are randomly initialized
        for size_out in hidden_layers_sizes + [1]:
            self.Ws.append(tf.Variable(tf.random.truncated_normal([size_out, size_in], stddev=0.1)))
            self.bs.append(tf.Variable(tf.random.truncated_normal([size_out, 1], stddev=0.1)))
            size_in = size_out
        self.trainable_variables = self.Ws + self.bs # union
        self.output_range = tf.constant(output_range, dtype=tf.float32)

    @tf.function
    def __call__(self, severity, city_number, resources_remaining):
        x = tf.expand_dims(tf.stack([severity, city_number, resources_remaining]), 1)
        for W, b in zip(self.Ws, self.bs):
            x = tf.math.sigmoid(W @ x + b)
        return tf.squeeze(x) * self.output_range

    def save(self):

        with open( self.Weights_tfFile, 'wb') as f:
            pickle.dump(self.Ws, f)
            pickle.dump(self.bs, f)

    def load(self):
        with open( self.Weights_tfFile ,'rb') as f:
            self.Ws = pickle.load(f)
            self.bs = pickle.load(f)





@tf.function
def damage_city(severity, resources_allocated, time_damage_accumulates):
    # Not sure I interpreted correctly how damage is calculate, please check
    # option 1
    #damage = tf.math.maximum(0., severity - resources_allocated) * time_damage_accumulates
    # option 2
    #damage = tf.math.maximum(0., severity - resources_allocated) ** time_damage_accumulates
    # option 3 damage does not accumulate
    #damage = tf.math.maximum(0., severity - resources_allocated) ** 2
    # option 4 (revised based on experiment)
    α = RESPONSE_MULTIPLIER
    β = SEVERITY_MULTIPLIER
    ##damage = tf.math.maximum(0., (severity - resources_allocated) * (β)**time_damage_accumulates + resources_allocated)
    for i in range(time_damage_accumulates):
        severity = tf.math.maximum(0., (severity * (β) * 1-resources_allocated * (α)))
    damage = severity
    return damage

def train_one_game(model, optimizer, severities, initial_resources, log=None):

    with tf.GradientTape(watch_accessed_variables=False) as tape:
        tape.watch(model.trainable_variables)
        damage = tf.Variable(0.)
        resources_remaining = tf.Variable(initial_resources, dtype=tf.float32)
        city_number = tf.Variable(1.)
        for k in range(len(severities)):
            severity = severities[k]
            resources_allocated = model(severity, city_number, resources_remaining)
            resources_effectively_allocated = tf.math.minimum(resources_allocated, resources_remaining)
            time_damage_accumulates = len(severities) + 1 - city_number
            damage = damage + damage_city(severity, resources_effectively_allocated, time_damage_accumulates)
            if log is not None:
                log.append([v.numpy() for v in [city_number, resources_remaining, severity, resources_allocated, resources_effectively_allocated, damage]])
            resources_remaining = resources_remaining - resources_effectively_allocated  # do not use assign_add here because it stops the gradient
            city_number = city_number + 1

    # compute gradient
    grads = tape.gradient(damage, model.trainable_variables)
    # update to weights
    optimizer.apply_gradients(zip(grads, model.trainable_variables))

    return damage

def agent_meta_cognitive(action, output_value_range, resources_left, response_timeout):
    # What are we doing here is mapping the distance to the boundary of each decision, as
    # the level of confidence that the NN-Agent has on this decision.
    # This can be done because the output of the NN-Agent is continuos.
    centers = [r for r in range(output_value_range)]
    center = numpy.asarray( centers, dtype=numpy.float32)

    closer = center-action
    closer = numpy.abs( closer )
    closervalue = center[numpy.argmin(closer)]

    action = numpy.clip(action, 1, resources_left)

    f = lambda x: x * (-2) + 1

    distance = numpy.clip(numpy.abs(closervalue-action),0,0.5)

    confidence = f( distance )

    response = int(round(action))

    mu, sigma = int(distance * 10), 3

    rt_hold = numpy.random.normal(mu, sigma, 1)[0]
    rt_release = rt_hold + numpy.random.normal(mu, 1, 1)[0]

    rt_hold = numpy.clip( rt_hold, 0, response_timeout/1000.0)
    rt_release = numpy.clip( rt_release, 0, response_timeout/1000.0)

    return response, confidence, rt_hold, rt_release

def adjust_response_decay( resp, decay, resources_left):
    
    rand = numpy.random.random(1)

    COIN_FLIPPING       = 1
    GAUSSIAN_VARIANCE   = 2
    NON_HUMANISED       = 3

    modality = GAUSSIAN_VARIANCE 

    if (modality == COIN_FLIPPING):
        if (rand > decay):
            resp = randominstance.randrange(0,MAX_ALLOCATABLE_RESOURCES+1)
            resp = numpy.clip( resp, 0, resources_left)

    if (modality == GAUSSIAN_VARIANCE):
        variance = 1.0-decay
        variance = int(variance*AGENT_NOISE_VARIANCE)
        #if (variance>1):
        delta = randominstance.gauss(resp, variance)
        resp = numpy.clip( delta, 0, min(resources_left, MAX_ALLOCATABLE_RESOURCES))
        #else:
            # 0 is a valid response (delegate response)
        #    delta = randominstance.uniform(-1,1+1)
        #    resp = numpy.clip( resp+delta, 0, min(resources_left, MAX_ALLOCATABLE_RESOURCES))
    
    return resp 

def boltzmann_decay( global_seq_no ):
    # 75 and 4.0 here are parameters that push the shape of the boltzmann decay (as function of temperature, the sequence number in this case).
    return numpy.exp( ( -75.0) / (4.0 * global_seq_no ) )

def get_random_confidence(value):
    return (randominstance.randrange(value)+1 )/10.0


def get_calibrated_reported_confidence( right_response, noisy_response):
    distance = numpy.clip( numpy.abs( right_response - noisy_response),0,MAX_ALLOCATABLE_RESOURCES)
    dist = distance
    distance = -distance
    confidence = (distance - (-(3.0))) / (3.0)

    confidence = numpy.clip( confidence, 0.0, 1.0 )

    return confidence, dist




def calibrated_metacognitive_response_from_agent(g_seq_no, right_response, resources_left):
    decay = boltzmann_decay( g_seq_no )
    noisy_response = adjust_response_decay( right_response, decay, resources_left)

    confidence = get_calibrated_reported_confidence( right_response, noisy_response)

    resp = noisy_response
    
    if (numpy.abs( noisy_response - right_response ) >3):
        resp = right_response - 3
        resp = numpy.clip( resp, 0, resources_left)

    if (resp == 0):
        confidence = -1.0

    resp = round(resp)

    return confidence, resp 





