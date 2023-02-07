'''
PES - Pandemic Experiment Scenario

Set of handy functions to deal with several calculations in the PES game.


'''

import numpy
import os,sys
import matplotlib.pyplot as plt


from statsmodels.distributions.empirical_distribution import ECDF
from scipy.stats import beta 
from scipy.stats import uniform

import pickle

import csv

from PES import INPUTS_PATH
from PES import AVAILABLE_RESOURCES_PER_SEQUENCE
from PES import MAX_ALLOCATABLE_RESOURCES, MIN_ALLOCATABLE_RESOURCES

from PES.src.exp_utils import get_array_of_sequence_severities_from_allocations
from PES.src.exp_utils import calculate_normalised_final_severity_performance_metric 
import statsmodels.api as sm

DATA_PATH = '.'

# Copy of the code from performanceCalculator
def calculate_sequence_performance( SeveritiesFromSequence, InitialSequenceSeverities ):

    FinalSequenceSeverity     = numpy.sum( SeveritiesFromSequence )
    BestCaseAllocations       = numpy.full_like( SeveritiesFromSequence, MAX_ALLOCATABLE_RESOURCES )
    WorstCaseAllocations      = numpy.full_like( SeveritiesFromSequence, MIN_ALLOCATABLE_RESOURCES )
    BestCaseSequenceSeverity  = numpy.asarray( get_sequence_severity_from_allocations( BestCaseAllocations , InitialSequenceSeverities ) )
    WorstCaseSequenceSeverity = numpy.asarray( get_sequence_severity_from_allocations( WorstCaseAllocations, InitialSequenceSeverities ) )
    Performance               = (WorstCaseSequenceSeverity - FinalSequenceSeverity) / (WorstCaseSequenceSeverity - BestCaseSequenceSeverity )

    return Performance


def calculate_trial_performances_for_sequence( SeveritiesFromSequence, InitialSequenceSeverities ):

    FinalSequenceSeverity     = SeveritiesFromSequence.copy()
    BestCaseAllocations       = numpy.full_like( SeveritiesFromSequence, MAX_ALLOCATABLE_RESOURCES )
    WorstCaseAllocations      = numpy.full_like( SeveritiesFromSequence, MIN_ALLOCATABLE_RESOURCES )
    BestCaseSequenceSeverity  = numpy.asarray( get_array_of_sequence_severities_from_allocations( BestCaseAllocations , InitialSequenceSeverities ) )
    WorstCaseSequenceSeverity = numpy.asarray( get_array_of_sequence_severities_from_allocations( WorstCaseAllocations, InitialSequenceSeverities ) )
    Performance               = (WorstCaseSequenceSeverity - FinalSequenceSeverity) / (WorstCaseSequenceSeverity - BestCaseSequenceSeverity )

    return Performance

def reg(x,y):
    ones = numpy.ones(len(x))
    X = sm.add_constant(numpy.column_stack((x, ones)))
    results = sm.OLS(y, X).fit()
    return results



def entropy_from_pdf(pdf):
    '''
    Return the entropy of the provided pdf (which can be a histogram).
    '''
    # Push all the values upwards for them to be all positive.
    pdf = pdf + numpy.abs(numpy.min( pdf ))

    # Normalize them to be numpy.sum(pdf) = 1  (probability)
    p =  pdf / numpy.sum(pdf)  # log(0)
    p[ p==0 ] += 0.000001       # Avoid zero value, by adding just a small epsilon
    H = -numpy.dot( p, numpy.log2( p ) )
    return H

def entropy(x, bins=None):
    '''
    Returns the entropy of the empiricial distribution of x
    '''

    N = x.shape

    if bins is None:   counts = numpy.bincount( x )
    else           :   counts = numpy.histogram( x, bins = bins )[ 0 ]   # Counts, probs

    p = counts[ numpy.nonzero( counts ) ] / N    # log(0)
    H = -numpy.dot( p, numpy.log2( p ) )

    return H


def convert_globalseq_to_seqs(sequence_map,seqin360):
    rsp = []
    offset = 0
    for seq in sequence_map:
        rsp.append( seqin360[offset:offset+int(seq)] )
        offset = offset + int(seq)
    return rsp



def adjust_unrealistic_responses_wrt_actual_resources( TrialResponses ):
    ResourcesAvailable = AVAILABLE_RESOURCES_PER_SEQUENCE - 9   # The first 9 resources are consumed by the 'init' cities in the experiment!
    CorrectedResponses = []

    if sum( TrialResponses ) > ResourcesAvailable:   # Adjust for overallocation

        for i in TrialResponses:
            CorrectedResponse = min( i, ResourcesAvailable )
            CorrectedResponses.append( CorrectedResponse )
            ResourcesAvailable -= CorrectedResponse
        CorrectedResponses = numpy.array( CorrectedResponses )


    elif sum( TrialResponses ) < ResourcesAvailable:   # Adjust for UNINTENTIONAL underallocation

        IndexOfFirstZero = numpy.cumsum( TrialResponses ).tolist().index( TrialResponses.sum() )   # Returns the index of the first 0 in a terminal sequence of 0s, or the last index

        if TrialResponses[-1] != 0:   IndexOfFirstZero += 1   # Do not adjust explicit underallocation of the last trial unless zero

        for i in range( IndexOfFirstZero ):
            CorrectedResponses.append( TrialResponses[ i ] )
            ResourcesAvailable -= TrialResponses[ i ]

        for i in range( IndexOfFirstZero, TrialResponses.size ):
            CorrectedResponse = min( ResourcesAvailable, MAX_ALLOCATABLE_RESOURCES )
            CorrectedResponses.append( CorrectedResponse )
            ResourcesAvailable -= CorrectedResponse

        CorrectedResponses = numpy.array( CorrectedResponses )


    else: CorrectedResponses = TrialResponses.copy()

    return CorrectedResponses


def get_remaining_resources_sequence(sequence_length, responses, initial_severities, num_seq=48):
    '''
    Get the sequence of remaining resources that could have been used to generate these responses
    '''
    rs = convert_globalseq_to_seqs( sequence_length, responses )
    rr_seq = []
    for seqindex, seq in enumerate(initial_severities):
        rr_perseq = numpy.cumsum( rs[seqindex] )
        rr_perseq = AVAILABLE_RESOURCES_PER_SEQUENCE-9-rr_perseq
        rr_seq.extend( rr_perseq )

    return rr_seq


#
# This function returns the performance backtracked to each trial (assumming a sequence of length 1).
#
# # DO NOT USE ME.
# 
def get_normalised_performance_per_subject_per_trial(sequence_length, response, initial_severities):
    perfs = []
    seqlen = sequence_length
    rs = convert_globalseq_to_seqs( seqlen, response[:] )
    init_severities = initial_severities 
    for seqindex, seq in enumerate(init_severities):
        sevs_in_seq = init_severities[seqindex]
        responses_for_city = rs[seqindex]
        for city_no, city_severity in enumerate(sevs_in_seq):
            
            rsp = responses_for_city[:city_no+1]
            print( rsp )
            final_severities = get_array_of_sequence_severities_from_allocations( rsp, sevs_in_seq[:city_no+1] )

            perf, _, _ = calculate_normalised_final_severity_performance_metric( final_severities, sevs_in_seq[:city_no+1])
            perfs.append( perf )

    return perfs 



#
#
# Returns the performance on each trial based on how the city that appears on that trial ends up at the end of the sequence.
# This effectively checks the outcome of the individual decision on each city.
#
#
def get_normalised_performance_for_each_individual_trial(sequence_length, response, initial_severities):
    perfs = []
    seqlen = sequence_length
    rs = convert_globalseq_to_seqs( seqlen, response[:] )
    init_severities = initial_severities 
    for seqindex, seq in enumerate(init_severities):
        sevs_in_seq = init_severities[seqindex]
        responses_for_city = rs[seqindex]

        final_severities = get_array_of_sequence_severities_from_allocations( responses_for_city, sevs_in_seq )
        
        print ( final_severities )
        print( sevs_in_seq )
        
        perf = calculate_trial_performances_for_sequence( final_severities, sevs_in_seq )

        for i in perf:
            perfs.append( i )

    return perfs

def get_normalised_performance_for_subject(sequence_length, response, initial_severities, num_seq = 48, EnableRealisticAssumption = False):
    '''
    Get the sequence of sequences on sequence_length and for each one of it calculates the normalised severity obtained at the end of the sequence
    given the initial_severities and the provided responses.

    All the lists must contain the same number of elements and all of them are a list of lists.
    '''
    
    perfs = []
    seqlen = sequence_length[:num_seq]
    rs = convert_globalseq_to_seqs( seqlen, response[:] )
    init_severities = initial_severities[:num_seq]
    for seqindex, seq in enumerate(init_severities):
        
        # Adjust the responses assumming a more realistic approach on the decision.  This is a caveat to solve the problem of the broken causality in the replay when each player play by itself.
        if (EnableRealisticAssumption): rs[seqindex] = adjust_unrealistic_responses_wrt_actual_resources( rs[seqindex] )
        final_severities = get_array_of_sequence_severities_from_allocations( rs[seqindex], init_severities[seqindex] )

        perf, _, _ = calculate_normalised_final_severity_performance_metric( final_severities, init_severities[seqindex])
        perfs.append( perf )

    return perfs 

def movingaverage(interval, window_size):
    window = numpy.ones( int(window_size)) / float(window_size)
    return numpy.convolve( numpy.concatenate( [interval,interval, interval] ), window, 'same')[len(interval):2*len(interval)]



def plot_response_times(number_of_trials, sequence_length, PressEvents, ReleaseEvents,Title='Response Times'):
    
    plt.figure(figsize=(20, 8))
    plt.subplot(2, 1, 1)
    vline_sev = 0
    plt.plot(numpy.arange(1, number_of_trials+1), PressEvents, 
            color='red', marker='o', linestyle = 'None', label='Press Button Response Times')
    plt.xlim(-0.5, number_of_trials+1)
    plt.ylim(1, 11)
    plt.yticks(numpy.linspace(0.0,11.0,6), 
            ("0", "2", "4", "6", "8", "10"))
    plt.ylabel('Time (s)')
    plt.xlabel('Trials')
    for seq in sequence_length:
        vline_sev += seq
        plt.vlines(vline_sev, -1,11, color = 'k')
    plt.title(Title)
    plt.subplot(2,1,2)
    vline_res = 0
    plt.plot(numpy.arange(1, number_of_trials+1), ReleaseEvents,
            color='blue', marker='*', linestyle = 'None', label='Press Button Release Times')
    plt.xlim(-0.5, number_of_trials+1)
    plt.ylim(-1,11)
    plt.yticks(numpy.linspace(0.0,11.0,6),
            ("0","2","4","6","8","10"))
    plt.ylabel('Time (s)')
    for seq in sequence_length:
        vline_res += seq
        plt.vlines(vline_res, -1, 11, color='k')
    y_av = movingaverage( ReleaseEvents, 40)
    plt.plot( numpy.arange(1, number_of_trials+1), y_av, color='green')
    #plt.savefig('../../analysis/resource_allocated_per_subj%d.pdf'%subject)
    plt.show()






def plot_all_data(number_of_trials, sequence_length, InitialSeverities, Confidences, Allocations,Title='Responses'):
    
    plt.figure(figsize=(20, 8))
    plt.subplot(3, 1, 1)
    vline_sev = 0
    plt.plot(numpy.arange(1, number_of_trials+1), InitialSeverities, 
            color='red', marker='o', linestyle = 'None', label='Severity')
    plt.xlim(-0.5, number_of_trials+1)
    plt.ylim(1, 11)
    plt.yticks(numpy.linspace(0.0,11.0,6), 
            ("0", "2", "4", "6", "8", "10"))
    plt.ylabel('Severity')
    plt.xlabel('Trials')
    for seq in sequence_length:
        vline_sev += seq
        plt.vlines(vline_sev, -1,11, color = 'k')
    plt.title(Title)
    plt.subplot(3,1,2)
    vline_res = 0
    plt.plot(numpy.arange(1, number_of_trials+1), Allocations,
            color='blue', marker='*', linestyle = 'None', label='Resources Allocated')
    plt.xlim(-0.5, number_of_trials+1)
    plt.ylim(-1,11)
    plt.yticks(numpy.linspace(0.0,11.0,6),
            ("0","2","4","6","8","10"))
    plt.ylabel('Resources Allocated')
    for seq in sequence_length:
        vline_res += seq
        plt.vlines(vline_res, -1, 11, color='k')
    plt.subplot(3,1,3)
    vline_res = 0
    plt.plot(numpy.arange(1, number_of_trials+1), Confidences,
            color='green', marker='+', linestyle='None', label='Resources Allocated')
    plt.xlim(-0.5, number_of_trials+1)
    plt.ylim(-.1, 1.1)
    plt.yticks(numpy.linspace(0.0, 1.0,6),
            ("0","0.2","0.4", "0.6", "0.8", "1.0"))
    plt.ylabel('Confidence reported')
    y_av = movingaverage( Confidences, 40)
    plt.plot( numpy.arange(1, number_of_trials+1), y_av, color='green')
    for seq in sequence_length:
        vline_res += seq
        plt.vlines(vline_res, -1, 11, color = 'k')
    #plt.savefig('../../analysis/resource_allocated_per_subj%d.pdf'%subject)
    plt.show()




def plot_confidences( ConfidencesPerSubject, title, Show=True, ExcludeUnanswered=True ):

    ConfidencesPerSubject = numpy.asarray( ConfidencesPerSubject ) 
    
    #ConfidencesPerSubject =  ConfidencesPerSubject[1:]
    
    confidences = ConfidencesPerSubject.flatten()

    # Unanswered responses are considered as zero for the voting mechanism. 
    if (ExcludeUnanswered):
        confidences = confidences[confidences != -1.0]
    else:
        confidences[confidences == -1.0] = 0.0

    val_confidences = numpy.arange(10.0 + 2.0, dtype=numpy.float32) / 10.0 - 0.05

    print( val_confidences) 

    conf_hist = numpy.histogram( confidences, bins = val_confidences )

    plt.hist( confidences, bins=val_confidences )
    plt.title( title )
    if (Show): plt.show()

    return confidences




def plotconfidence(confidences):

    val_confidences = numpy.arange(12, dtype=numpy.float32) / 10.0 - 0.05


    fig = plt.figure(figsize=(10,5))
    plt.hist(confidences, bins=val_confidences )
    plt.ylabel('#')
    plt.xlabel('Confidences')
    plt.legend()
    plt.show()



def histogram_equalization(confidences):
    rlagents = numpy.round( confidences, 1 )

    values = list(range(11))
    keys = numpy.arange(11, dtype=numpy.float32) / 10.0
    keys = list(keys)

    rlagents = rlagents[ rlagents != -1.0 ]


    t =  dict(zip( keys, values ))

    val_confidences = numpy.arange(11, dtype=numpy.float32) / 10.0
    rlagents_hist = numpy.histogram( rlagents, bins=val_confidences)[0]
    T = numpy.cumsum( rlagents_hist  ) / numpy.sum( rlagents_hist )


    n_rlagents = numpy.copy ( rlagents )

    n_rlagents = [   ( T[t[conf]] - numpy.min( T )) / (1 - numpy.min(T)) for conf in rlagents ]

    return n_rlagents 



def remap(confidences):
    samples = plot_confidences()
    fitted, alpha, beta = estimate_beta( samples )

    xx = numpy.linspace(0, 1.0, len(confidences))
    pdf1 = fitted(xx, alpha, beta)
    pdf1 = numpy.sort( pdf1 )
    f1 = numpy.cumsum(  pdf1 ) / numpy.sum( pdf1 )

    pdf2 = numpy.sort(confidences)
    f2 = numpy.cumsum( pdf2 ) / numpy.sum( pdf2 )

    plt.plot(pdf1, f1, 'r', label='Beta to fit')
    plt.plot(pdf2, f2, 'b', label='Real Distribution')
    plt.legend()
    plt.show()


    T = numpy.zeros((len(confidences),2))
    for i,g1 in enumerate(xx):
        g2 = f2.flat[numpy.abs(f2-f1[i]).argmin()]
        T[i,:] = [g1,g2]

    print( T )

    remapconf = numpy.copy( confidences )
    for i, confvalue in enumerate(confidences):
        remapconf[i] = T[:,0].flat[numpy.abs(T[:,0] - confvalue).argmin()]

    return remapconf


def confidence_calibrations():
    nnagent_confidences = numpy.load( os.path.join( INPUTS_PATH,  'confs.npy') )
    rlagent_confidences = numpy.load( os.path.join( INPUTS_PATH, 'confsrl.npy') )


    samples = plot_confidences()

    plotconfidence(nnagent_confidences)
    plotconfidence(rlagent_confidences)


    I = rlagent_confidences
    rescaled = (I - numpy.min(I) )* (  (1.0 - 0.0) / ( numpy.max(I) - numpy.min(I)) ) + 0.0

    plotconfidence(rescaled)


    val_confidences = numpy.arange(12, dtype=numpy.float32) / 10.0 - 0.05


    eqconfidences = histogram_equalization( rlagent_confidences )



    reampconf = remap(rlagent_confidences)

    fig,axx = plt.subplots(2,2)
    ax = axx[0,0]
    ax.hist(rlagent_confidences, bins=val_confidences )
    ax.set_ylabel('#')
    ax.set_xlabel('Confidences')

    ax = axx[1,0]
    ax.hist(rescaled)
    ax.set_ylabel('#')
    ax.set_xlabel('Scaled Confidences')

    ax = axx[0,1]
    ax.hist(eqconfidences)
    ax.set_ylabel('#')
    ax.set_xlabel('Histogram eq')

    ax = axx[1,1]
    ax.hist(reampconf)
    ax.set_ylabel('#')
    ax.set_xlabel('Histogram matching')


    plt.show()



def calibrate_confidence(confidences, uniform_pdf = False, a=0.5, b=0.5):
    ecdf = ECDF( confidences )

    if uniform_pdf:
        MappedConfidences = uniform.ppf( ecdf( confidences)) 
    else:
        MappedConfidences = beta.ppf( ecdf(confidences), a, b )  

    MappedConfidences = (MappedConfidences - min(MappedConfidences))/(max(MappedConfidences) - min(MappedConfidences))

    return MappedConfidences


def setup_human_reported_confidence( Allocations1, Confidences1, Allocations2, Confidences2, Allocations3, Confidences3):


    lookuptable = {}

    for alloc in range(11):
        lookuptable[alloc] = []

    for i in range(len(Allocations1)):
        allocation = Allocations1[i]
        for alloc in range(11):
            filtered_confidences = Confidences1[i][allocation==alloc]
            lookuptable[alloc].extend( filtered_confidences )

    for i in range(len(Allocations2)):
        allocation = Allocations2[i]
        for alloc in range(11):
            filtered_confidences = Confidences2[i][allocation==alloc]
            lookuptable[alloc].extend( filtered_confidences )


    for i in range(len(Allocations3)):
        allocation = Allocations3[i]
        for alloc in range(11):
            filtered_confidences = Confidences3[i][allocation==alloc]
            lookuptable[alloc].extend( filtered_confidences )

    with open( os.path.join( INPUTS_PATH, 'reported_confidence_lookuptable.pickle'), 'wb') as output:
        pickle.dump( lookuptable, output )



def pick_human_reported_confidence(allocation):

    assert allocation >= 0 and allocation <= 10, 'Provided allocation is out of bounds.'

    with open( os.path.join( INPUTS_PATH, 'reported_confidence_lookuptable.pickle'), 'rb') as input:
        lookuptable = pickle.load(input)

    return lookuptable[allocation][numpy.random.randint(len(lookuptable[allocation]))]


def setup_humanise_reported_confidence(confidences):

    with open( os.path.join( INPUTS_PATH, 'reported_confidences.pickle'), 'wb') as output:
        pickle.dump( confidences, output) 

    ecdf = ECDF( confidences )

    MappedConfidences = beta.ppf( ecdf(confidences), 5.0, 1.8 )  


    I = MappedConfidences
    rescaled = (I - numpy.min(I) )* (  (1.2 - 0.0) / ( numpy.max(I) - numpy.min(I)) ) + 0.0
    MappedConfidences = numpy.clip( rescaled, 0.0, 1.0)

    #MappedConfidences[MappedConfidences > 0.85] = 1.0

    return MappedConfidences

def humanise_this_reported_confidence(reported_confidence):
    with open( os.path.join( INPUTS_PATH,'reported_confidences.pickle'),'rb') as input:
        confidences = pickle.load(input)

    confidences = numpy.concatenate( ([ confidences, reported_confidence]), axis=0 )

    ecdf = ECDF( confidences )

    MappedConfidences = beta.ppf( ecdf(confidences), 5.0, 1.8 )  

    I = MappedConfidences
    rescaled = (I - numpy.min(I) )* (  (1.0 - 0.0) / ( numpy.max(I) - numpy.min(I)) ) + 0.0
    MappedConfidences = numpy.clip( rescaled, 0.0, 1.0)

    return MappedConfidences[-reported_confidence.shape[0]:]



def plot_confidence_calibration_schemes(agent_confidences, title):
    fig, axx = plt.subplots(5,1)

    val_confidences = numpy.arange(12, dtype=numpy.float32) / 10.0 - 0.05

    val_confidences = numpy.arange(11, dtype=numpy.float32) / 10.0 

    ax = axx[0]
    ax.hist(agent_confidences, bins=val_confidences, label='Agent output' )
    ax.set_ylabel('#')
    ax.set_xticks([])
    ax.legend()

    confidences = calibrate_confidence(agent_confidences, False, 2.0,2.0)
    ax = axx[1]
    ax.hist(confidences, bins=val_confidences, label='Hesitant Guy' )
    ax.set_ylabel('#')
    ax.set_xticks([])
    ax.legend()

    confidences = calibrate_confidence(agent_confidences, False, 2.0,5.0)
    ax = axx[2]
    ax.hist(confidences, bins=val_confidences , label='Underconfident')
    ax.set_ylabel('#')
    ax.set_xticks([])
    ax.legend()

    confidences = calibrate_confidence(agent_confidences, False, 5.0,1.8)
    ax = axx[3]
    ax.hist(confidences, bins=val_confidences , label='Overconfident')
    ax.set_ylabel('#')
    ax.set_xticks([])
    ax.legend()

    confidences = calibrate_confidence(agent_confidences, True, 0.0, 0.0)
    ax = axx[4]
    ax.hist(confidences, bins=val_confidences, label='Uniform distributed' )
    ax.set_ylabel('#')
    ax.set_xlabel(f'{title}')
    ax.legend()

    plt.show()



def getSubjectsData( DataPath = DATA_PATH, SubjectFiles='', SkipFirstLine=True, format_v2 = True  ):
    AllConfidences      = []
    AllAllocations      = []
    AllPressEvents      = []
    AllReleaseEvents    = []

    AllAgentAllocations = []
    AllAgentConfidences = []

    for SubjectFile in SubjectFiles:
            InitialSeverities, Confidences, Allocations, PressEvents, ReleaseEvents, AgentAllocations, AgentConfidences = getSubjectData( SubjectFile, SkipFirstLine = SkipFirstLine, DataPath = DataPath, format_v2 = format_v2)

            AllConfidences.append(  Confidences )
            AllAllocations.append(  Allocations)
            AllPressEvents.append(  PressEvents)
            AllReleaseEvents.append(    ReleaseEvents)

            AllAgentAllocations.append( AgentAllocations )
            AllAgentConfidences.append( AgentConfidences )

    return InitialSeverities, AllConfidences, AllAllocations, AllPressEvents, AllReleaseEvents, AllAgentAllocations, AllAgentConfidences


def getSubjectData( SubjectFile, SkipFirstLine, DataPath = DATA_PATH, format_v2 = True):

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

    Data = numpy.array( Data )

    if (format_v2):
        initialvalue = 1
    else:
        initialvalue = 0

    InitialSeverities       = Data[:,initialvalue+0]
    Confidences             = Data[:,initialvalue+2]
    Allocations             = Data[:,initialvalue+1]
    PressEvents             = Data[:,initialvalue+3]
    ReleaseEvents           = Data[:,initialvalue+4]
    
    if (format_v2):
        AgentAllocations        = Data[:,initialvalue+5]
        AgentConfidences        = Data[:,initialvalue+6]
    else:
        AgentAllocations        = []
        AgentConfidences        = []

    return InitialSeverities, Confidences, Allocations, PressEvents, ReleaseEvents, AgentAllocations, AgentConfidences




