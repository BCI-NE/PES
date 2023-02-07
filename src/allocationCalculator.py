"""
PES - Pandemic Experiment Scenario

Contains functions relating to the calculation (group) allocation given
individual agents' allocations

Functions defined here:
 • adjust_sequence_for_overallocation
 • get_confidence_weighted_mean
 • get_fuzzy_weighted_mean
 • get_valid_responses_and_confidences_for_single_trial_over_all_subjects
"""


# ----------------
# external imports
# ----------------

import numpy

# ----------------
# internal imports
# ----------------

from .. import AVAILABLE_RESOURCES_PER_SEQUENCE



#############################
### General utility functions
#############################

def get_valid_responses_and_confidences_for_single_trial_over_all_subjects( ConfidencesPerSubject, AllocationsPerSubject, TrialIndex ):

    t = TrialIndex   # alias for conciseness in indexing

  # Get Responses and Confidences for the specified trial over all subjects
    AllocationsAtTrial = numpy.array( [i[t] for i in AllocationsPerSubject] )
    ConfidencesAtTrial = numpy.array( [i[t] for i in ConfidencesPerSubject] )

  # Handle 'invalid' confidence instances
    AllocationsAtTrial = AllocationsAtTrial [ ConfidencesAtTrial != -1 ]
    ConfidencesAtTrial = ConfidencesAtTrial [ ConfidencesAtTrial != -1 ]

    return AllocationsAtTrial, ConfidencesAtTrial




def get_confidence_weighted_mean( ConfidencesPerSubject, AllocationsPerSubject ):

    NumTrials = len( ConfidencesPerSubject[0] )
    AggregatedAllocations = []

    for t in range( NumTrials ):

      # Filter out allocation-confidence pairs with invalid confidences
        AllocationsAtTrial, ConfidencesAtTrial = get_valid_responses_and_confidences_for_single_trial_over_all_subjects( ConfidencesPerSubject, AllocationsPerSubject, t )

      # If no valid allocations / confidences exist at this trial
        if AllocationsAtTrial.size == 0:   AggregatedAllocations.append( 0 )
        else:
          # If overall confidence is 0, fallback to unweighted average to avoid division by zero errors.
            MarginalConfidence = numpy.sum( ConfidencesAtTrial )

            if MarginalConfidence == 0:   ConfidencesAtTrial = 1 / ConfidencesAtTrial.size
            else                      :   ConfidencesAtTrial = ConfidencesAtTrial / MarginalConfidence

          # Calculate weighted average
            ConfidenceWeightedMean = numpy.sum( ConfidencesAtTrial * AllocationsAtTrial )
            AggregatedAllocations.append( ConfidenceWeightedMean )

    return numpy.round( numpy.array( AggregatedAllocations ) )




def get_fuzzy_weighted_mean( ConfidencesPerSubject, ShapleyPerSubject, MMAPerSubject, AllocationsPerSubject,
                             And = lambda a,b: a * b,
                             Or  = lambda a,b: a + b - a * b  ):
    """
    Note: MMA = Measure of Metacognitive Accuracy
    """

    NumTrials = len( ConfidencesPerSubject[0] )
    AggregatedAllocations = []

    for t in range( NumTrials ):

      # Filter out allocation-confidence pairs with invalid confidences
        AllocationsAtTrial, ConfidencesAtTrial = get_valid_responses_and_confidences_for_single_trial_over_all_subjects( ConfidencesPerSubject, AllocationsPerSubject, t )
        ShapleysAtTrial   , ConfidencesAtTrial = get_valid_responses_and_confidences_for_single_trial_over_all_subjects( ConfidencesPerSubject, ShapleyPerSubject, t )
        MMAsAtTrial       , ConfidencesAtTrial = get_valid_responses_and_confidences_for_single_trial_over_all_subjects( ConfidencesPerSubject, MMAPerSubject, t )

      # If no valid allocations / confidences exist at this trial
        if AllocationsAtTrial.size == 0:   AggregatedAllocations.append( 0 )
        else:

          # If overall confidence is 0, fallback to unweighted average to avoid division by zero errors.
            MarginalConfidence = numpy.sum( ConfidencesAtTrial )
            if MarginalConfidence == 0:   ConfidencesAtTrial = 1 / ConfidencesAtTrial.size
            else                      :   ConfidencesAtTrial = ConfidencesAtTrial / MarginalConfidence

            MarginalShapley = numpy.sum( ShapleysAtTrial )
            if MarginalShapley == 0:   ShapleysAtTrial = 1 / ShapleysAtTrial.size
            else                   :   ShapleysAtTrial = ShapleysAtTrial / MarginalShapley

            MarginalMMA = numpy.sum( MMAsAtTrial )
            if MarginalMMA == 0:   MMAsAtTrial = 1 / MMAsAtTrial.size
            else               :   MMAsAtTrial = MMAsAtTrial / MarginalMMA

            FuzzyWeights = numpy.ones_like( AllocationsAtTrial )
            FuzzyWeights = And( FuzzyWeights, ShapleysAtTrial)
            FuzzyWeights = And( FuzzyWeights, MMAsAtTrial )
            FuzzyWeights = And( FuzzyWeights, ConfidencesAtTrial )

            MarginalFuzzyWeights = numpy.sum( FuzzyWeights )
            if MarginalFuzzyWeights == 0:   FuzzyWeights = 1 / FuzzyWeights.size
            else                        :   FuzzyWeights = FuzzyWeights / MarginalFuzzyWeights

          # Calculate weighted average
            FuzzyWeightedMean = numpy.sum( FuzzyWeights * AllocationsAtTrial )
            AggregatedAllocations.append( FuzzyWeightedMean )

    return numpy.round( numpy.array( AggregatedAllocations ) )


def debias( Allocations, Reference, method = 'subtract mean' ):

    if method == 'subtract mean':

        Bias                = (Allocations - Reference).mean()
        AdjustedAllocations = numpy.round( Allocations - Bias ).clip(0, 10)

    else:   raise ValueError('Invalid method specified')


    return AdjustedAllocations

def adjust_sequence_for_overallocation( TrialResponses ):

    ResourcesAvailable = AVAILABLE_RESOURCES_PER_SEQUENCE - 9   # The first 9 resources are consumed by the 'init' cities in the experiment!
    CorrectedResponses = []

    if sum( TrialResponses ) > ResourcesAvailable:   # Adjust for overallocation

        for i in TrialResponses:
            CorrectedResponse = min( i, ResourcesAvailable )
            CorrectedResponses.append( CorrectedResponse )
            ResourcesAvailable -= CorrectedResponse

        CorrectedResponses = numpy.array( CorrectedResponses )


    else: CorrectedResponses = TrialResponses.copy()


    return CorrectedResponses
