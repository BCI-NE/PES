'''
PES - Pandemic Experiment Scenario

This is the Pandemic Scenario represented as a custom scenario of OpenAI's Gym environment.

Pandemic Class:
    This can be used to perform simulations on the game given the current parameters that it may have now.  
    It relies on 
        'calculate_normalised_final_severity_performance_metric' from exp_utils 
        'get_updated_severity' from exp_utils.
'''

from hashlib import new
import numpy
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
from PES.ext.tools import entropy_from_pdf 



class Pandemic(Env):
    def __init__(self):
        super(Pandemic, self).__init__()
        
        self.max_resources = AVAILABLE_RESOURCES_PER_SEQUENCE-9         # Number of available resources at the beginning (9 are preassigned)
        self.max_seq_length = 12        # Length of the longer possible sequence
        self.max_severity = 10          # Ten severities, from 0 to 10
        self.max_allocation = 10        # Ten is the max alloc, Eleven choices, from 0 to 10

        self.available_resources_states = self.max_resources + 1
        self.trial_no_states = self.max_seq_length+1
        self.severity_states = self.max_severity+1
        
        # Define a 3-D observation space
        self.observation_shape = (self.available_resources_states, self.trial_no_states, self.severity_states)
        self.observation_space = spaces.Box(low = numpy.zeros(self.observation_shape), 
                                            high = numpy.ones(self.observation_shape),
                                            dtype = numpy.float16)
    
        
        # Define an action space 
        self.action_space = spaces.Discrete(self.max_allocation+1,)
                        
        # Create a canvas to render the environment images upon 
        self.canvas = numpy.ones(self.observation_shape) * 1
        
        # Define elements present inside the environment
        self.elements = []

        self.verbose = True

        self.number_cities_prob = numpy.asarray([], dtype=numpy.float64)
        self.severity_prob = numpy.asarray([], dtype=numpy.float64)

    def random_sequence(self):
        if (self.number_cities_prob.shape[0] == 0):
            self.seq_length = random.randrange(int(3), int(self.max_seq_length))
            #print(f'Length:{self.seq_length}')
            self.allocations = [self.action_space.sample() for s in range(self.seq_length)]
            self.initial_severities = [random.randrange(int(0), int(self.max_severity)) for s in range(self.seq_length)]
        else:
            self.seq_length = int(numpy.random.choice(self.number_cities_prob[:,0], p=(self.number_cities_prob[:,1])))
            self.initial_severities = numpy.random.choice(self.severity_prob[:,0], size=(self.seq_length,), p=self.severity_prob[:,1])



    def set_fixed_sequence(self, length, init_severities, allocs=None):
        self.seq_length = int(length)
        #print(f'Length:{self.seq_length}')
        self.set_initial_severities(init_severities)

        if allocs is None:
            self.allocations = [self.action_space.sample() for s in range(self.seq_length)]
        else:
            self.set_fixed_allocations(allocs)
            

    def set_fixed_allocations(self, allocs):
        self.allocations = allocs 

    def set_initial_severities(self, init_severities):
        self.initial_severities = init_severities

    def new_city(self):
        return self.initial_severities[self.iteration]

    def sample(self):
        return self.allocations[self.iteration]

    def reset(self):
        # Reset the fuel consumed
        self.available_resources = self.max_resources

        # Reset the reward
        self.ep_return  = 0

        # City number
        self.iteration = 0

        # Length of the sequence
        #self.seq_length = random.randrange(int(3), int(self.max_seq_length))

        #self.initial_severities = []

        #self.allocations = []

        self.severities = []
        self.resources = []

        self.severity_evolution = numpy.zeros((len(self.initial_severities)+1, len(self.initial_severities)))
        self.severity_city_counter = 0

        self.done = False

        # Get a new city with its own severity, and keep going....
        new_severity = self.new_city()
        self.severities.append( new_severity )

        # return the observation
        return [self.available_resources, self.iteration, int(new_severity)] 

    def render(self, mode = "human"):
        if (self.done):
            print("--".format(self.iteration+1) , ':' , ":".join(["{:5.2f}".format(sev) for sev in self.severities]), '->', ' Done!')
        elif (len(self.resources)>0):
            print("{:02d}".format(self.iteration+1) , ':' , ":".join(["{:5.2f}".format(sev) for sev in self.severities]), '->', self.resources[-1])
        return self.canvas
        
    def close(self):
        pass


    def get_action_meanings(self):
        return {0: "0", 1:"1", 2:"2", 3:"3", 4:"4",5:"5", 6:"6", 7:"7",8:"8",9:"9", 10:"10"}


    def damage(self):
        return get_updated_severity(len(self.severities), self.resources, self.severities)


    def step(self, action):
        # Flag that marks the termination of an episode
        done = False
    
        # Assert that it is a valid action 
        assert self.action_space.contains(action), f'Invalid Action {action}'
        
        # Reward for executing a step.
        reward = 0  

        if ( (self.available_resources-action)<= 0):
            action = self.available_resources
            #reward += -100

        self.available_resources -= action
        self.resources.append( action )

        if (self.verbose): self.render()

        self.severity_evolution[self.severity_city_counter][:len(self.severities)] = self.severities 
        self.severities = get_updated_severity(len(self.severities), self.resources, self.severities)
        self.severity_city_counter=self.severity_city_counter+1


        # Increment the episodic return
        self.ep_return += 1
        self.iteration += 1 

        # Get a new city with its own severity, and keep going....
        reward = (-1) * numpy.sum(self.severities)


        # If the length of the sequence was achieved, stop
        if (self.iteration) == self.seq_length:
            done = True
            #reward = (-1) * numpy.sum(self.damage())
            new_severity = 0

            # Update the evolution of the severity one more time for the final severity of all the cities.
            self.severity_evolution[self.severity_city_counter][:len(self.severities)] = self.severities 
        else:
            new_severity = self.new_city()
            self.severities.append( new_severity )

        return [self.available_resources, self.iteration, int(new_severity)], reward, done, []


    def plot_severity_evolution(self, sev_evolution):
        fig = plt.figure(figsize=(8,6))

        for i in range(sev_evolution.shape[1]):
            # This is to allow one more step of the evolution by the end of the sequence, to allow the initial trial to start from 1, and to allow each city to start at their own trial location
            plt.plot(numpy.arange(sev_evolution.shape[0]-i)+i+1, sev_evolution[i:,i])

        plt.xlabel('Trial', fontsize=16)
        plt.xticks( list(range( sev_evolution.shape[0] )) )
        plt.ylabel('Severity', fontsize=16)
        plt.ylim([0,12])
        plt.title('City severities across trials', fontsize=16)
        plt.show()

        return plt


def rl_agent_meta_cognitive(options, resources_left, response_timeout):
    

    # Min entropy from a univalue distribution (0)
    m_entropy = numpy.zeros((11,),)
    m_entropy[0] = 1 

    # Max entropy from a uniform distribution (3.55....)
    M_entropy = numpy.ones((11,),)

    # Options are the available choices from the Q Table
    #print ( f'Options:{options}')

    entrp1 = entropy_from_pdf(options)

    o = [i for i in range(len(options))]
    o = numpy.asarray(o, dtype=numpy.float32)

    # @FIXME 
    #options[o>resources_left] = 0.00001

    #print ( f'Feasible Options:{options}')

    # available resources, trial, severity
    dec_entropy = entropy_from_pdf(options)
    M_entropy = entropy_from_pdf(M_entropy)
    m_entropy = entropy_from_pdf(m_entropy)

    #print( f'High:{M_entropy}' )
    #print( f'Low: {m_entropy}' )
    #print( f'Entropy of response: {dec_entropy}')

    confidence = (1./(m_entropy-M_entropy)) * (dec_entropy - M_entropy)

    response = numpy.argmax(options)

    map_to_response_time = lambda x: x * (-2) + 1
    
    mu, sigma = int(map_to_response_time(confidence) * 10), 3

    rt_hold = numpy.random.normal(mu, sigma, 1)[0]
    rt_release = rt_hold + numpy.random.normal(mu, 1, 1)[0]

    rt_hold = numpy.clip( rt_hold, 0, response_timeout/1000.0)
    rt_release = numpy.clip( rt_release, 0, response_timeout/1000.0)

    return response, confidence, rt_hold, rt_release

def run_experiment(env,actionfunction,RandomSequences=True, trials_per_sequence=None, sevs=None, AssignumpyreAllocations=False, allocs=None, NumberOfIterations=64):
    #env.set_fixed_sequence(3,[10,10,10],[10,10,10])
    seqid = 0
    if (RandomSequences):
        env.random_sequence()
    elif (AssignumpyreAllocations):    
        env.set_fixed_sequence(trials_per_sequence[seqid],sevs[seqid], allocs[seqid])
    else:                   
        env.set_fixed_sequence(trials_per_sequence[seqid],sevs[seqid])
    state = env.reset()
    seqs = []
    perfs = []
    seq_ev=[]
    ITERATIONS=NumberOfIterations
    while seqid<ITERATIONS:
        print(f'State: {state}')
        action = actionfunction(env,state, seqid) 
        state2, reward, done, info = env.step(action)

        if done==True:
            env.done = True
            env.render()
            seqs.append(  numpy.sum(env.severities) )
            perf = calculate_normalised_final_severity_performance_metric( env.severities, env.initial_severities)
            perfs.append( perf[0] )
            seq_ev.append( env.severity_evolution )
            seqid = seqid+1
            if seqid<ITERATIONS: 
                if (RandomSequences):
                    env.random_sequence()
                elif (AssignumpyreAllocations): 
                    env.set_fixed_sequence(trials_per_sequence[seqid],sevs[seqid], allocs[seqid])
                else:               
                    env.set_fixed_sequence(trials_per_sequence[seqid],sevs[seqid])
            state2 = env.reset()

        state = state2

    print( seqs )
    env.close()

    return seqs, perfs, seq_ev

# Define Q-learning function
def QLearning(env, learning, discount, epsilon, min_eps, episodes, UsePreloadedReward=False, R=None):

    # Initialize Q table
    Q = numpy.random.uniform(low = -1, high = 1, 
                        size = (  env.available_resources_states, 
                                    env.trial_no_states, 
                                    env.severity_states,
                                            env.action_space.n))
    
    # Initialize variables to track rewards
    reward_list = []
    ave_reward_list = []
    conf_list = []


    # Calculate episodic reduction in epsilon
    reduction = (epsilon - min_eps)/episodes
    
    # Run Q learning algorithm
    for i in range(episodes):
        # Initialize parameters
        done = False
        tot_reward, reward = 0,0
        env.random_sequence()
        state = env.reset()
    
    
        while done != True:   
            # Render environment for last twenty episodes
            #if i >= (episodes - 20):
            #    env.dorender()
                
            # Determine next action - epsilon greedy strategy
            if numpy.random.random() < 1 - epsilon and state[0] != None:
                action = numpy.argmax(Q[state[0], state[1],state[2]]) 
            else:
                action = numpy.random.randint(0, env.action_space.n)

            _, confidence, _,_ = rl_agent_meta_cognitive( Q[state[0], state[1], int(state[2])], state[0], 10000)
            conf_list.append( confidence )

            # Get next state and reward
            state2, reward, done, info = env.step(action) 

            if (UsePreloadedReward):
                reward = R[state[0], state[1], state[2], action]
            
            #Allow for terminal states
            if done:
                Q[state[0], state[1], state[2], action] = reward
                
            # Adjust Q value for current state
            else:
                delta = learning*(reward + 
                                discount*numpy.max(Q[state2[0], 
                                                state2[1],
                                                state2[2]]) - 
                                Q[state[0], state[1],state[2],action])
                Q[state[0], state[1],state[2], action] += delta
                                    
            # Update variables
            tot_reward += reward
            state = state2
        
        # Decay epsilon
        if epsilon > min_eps:
            epsilon -= reduction
        
        # Track rewards
        reward_list.append(tot_reward)
        
        if (i+1) % 10000 == 0:
            ave_reward = numpy.mean(reward_list)
            ave_reward_list.append(ave_reward)
            reward_list = []
            
        if (i+1) % 10000 == 0:    
            print('Episode {} Average Reward: {}'.format(i+1, ave_reward))
            
    env.close()
    
    return ave_reward_list, Q, conf_list


