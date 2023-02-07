"""
PES - Pandemic Experiment Scenario

OracleAgentCalibrator

This code contains a NN-Agent that given a FIXED set of allocations, and a set 
of other different allocations and reported confidences (provided by somebody 
else) it provides the OPTIMAL reported confidence that MAXIMIZES the performance 
of a group of two players working together on the Pandemic Scenario (with weighting average).

"""
import os
import numpy
import pickle
from pickle import dumps, loads
import tensorflow as tf
#from tensorflow.keras import optimizers
#print(tf.__version__)

from .. import INPUTS_PATH
from .. import RESPONSE_MULTIPLIER
from .. import SEVERITY_MULTIPLIER



# create the neural network
class Calibrator():


    def __init__(self, hidden_layers_sizes, output_range):
        self.Ws = []
        self.bs = []
        self.Weights_tfFile = os.path.join( INPUTS_PATH, 'superagent_weights.tf' )
        size_in = 6 # [severity, city_number, resources_remaining]
        # Weights Ws and biases bs are randomly initialized
        for size_out in hidden_layers_sizes + [1]:
            self.Ws.append(tf.Variable(tf.random.truncated_normal([size_out, size_in], stddev=0.1)))
            self.bs.append(tf.Variable(tf.random.truncated_normal([size_out, 1], stddev=0.1)))
            size_in = size_out
        self.trainable_variables = self.Ws + self.bs # union
        self.output_range = tf.constant(output_range, dtype=tf.float32)

    @tf.function
    def __call__(self, severity, city_number, resources_remaining, allocation, tpaired_allocation, tpaired_confidence):
        x = tf.expand_dims(tf.stack([severity, city_number, resources_remaining, allocation, tpaired_allocation, tpaired_confidence]), 1)
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

def train_one_joint_game(calibrator, optimizer, severities, initial_resources, allocations, paired_allocations, paired_confidences, log=None):

    with tf.GradientTape(watch_accessed_variables=False) as tape:
        tape.watch(calibrator.trainable_variables)
        damage = tf.Variable(0.)
        resources_remaining = tf.Variable(initial_resources, dtype=tf.float32)
        trialId = 0
        city_number = tf.Variable(1.)
        for k in range(len(severities)):
            severity = severities[k]

            tallocation = tf.Variable( allocations[trialId], dtype=tf.float32)
            tpaired_allocation = tf.Variable( paired_allocations[trialId], dtype=tf.float32)
            tpaired_confidence = tf.Variable( paired_confidences[trialId], dtype=tf.float32) 

            reported_confidence = calibrator( severity, city_number, resources_remaining, tallocation, tpaired_allocation, tpaired_confidence) 

            tc = numpy.asarray( [ paired_confidences[trialId], reported_confidence ] )
            tr = numpy.asarray( [ paired_allocations[trialId] ,allocations[trialId] ] )

            if (numpy.sum( tc ) ==0):
                reported_confidence = 1.0
                tpaired_confidence = tf.Variable( 1.0, dtype=tf.float32)

            #resources_allocated = numpy.round( ConfidenceWeightedMean )
            resources_allocated =  tallocation * reported_confidence + tpaired_allocation * tpaired_confidence  
            #resources_allocated = calibrator( severity, city_number, resources_remaining, tallocation, tpaired_allocation, tpaired_confidence)
            resources_effectively_allocated = tf.math.minimum(resources_allocated, resources_remaining)
            time_damage_accumulates = len(severities) + 1 - city_number
            damage = damage + damage_city(severity, resources_effectively_allocated, time_damage_accumulates)
            #if log is not None:
            #    log.append([v.numpy() for v in [city_number, resources_remaining, severity, resources_allocated, resources_effectively_allocated, damage]])
            resources_remaining = resources_remaining - resources_effectively_allocated  # do not use assign_add here because it stops the gradient
            city_number = city_number + 1
            trialId = trialId + 1


    # compute gradient
    grads = tape.gradient(damage, calibrator.trainable_variables)
    # update to weights
    optimizer.apply_gradients(zip(grads, calibrator.trainable_variables))

    return damage

