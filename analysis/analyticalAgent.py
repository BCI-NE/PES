"""
PES - Pandemic Experiment Scenario

This is an analytical approach to obtain the optimal allocation of resources.

This relies on the fact that the final severity of a city for a given initial
severity 'I', allocation 'x', pandemic parameter 'α', and "turns remaining" 'n',
is given by:

    (1+α)ⁿI + [1 - (1+α)ⁿ]x

Solving for x and applying appropriate clipping and ceiling effects provides an
analytical solution for the optimal allocation, in the sense of allocating the
right amount to each successive city so that it reaches zero by the end of the
(known) sequence.
"""

import numpy


def get_analytical_solution (initial_severities, PandemicParameter, ResourcesAvailable, MinAlloc, MaxAlloc ):
    responses = []
    for seqindex, severities_in_sequence in enumerate(initial_severities):
        resp = get_analytical_solution_for_sequence( severities_in_sequence,PandemicParameter, ResourcesAvailable, MinAlloc, MaxAlloc)
        responses.extend( resp )
        
    return numpy.asarray( responses, dtype=numpy.float64)


def get_analytical_solution_for_sequence( InitialSeverities, PandemicParameter, ResourcesAvailable, MinAlloc, MaxAlloc ):

    assert isinstance( InitialSeverities, numpy.ndarray ) and InitialSeverities.ndim == 1,   "InitialSeverities needs to be a 1D numpy array"

  # Math symbolic aliases
    I = InitialSeverities
    n = numpy.arange( I.size, 0, -1 )   # i.e. countdown from N to 1, where N is the number of cities in the sequence
    α = PandemicParameter

  # Get analytical solution
    x  = (1 + α) ** n * I
    x /= (1 + α) ** n - 1

  # Apply clippings and ceilings
    Allocations = []

    for i in numpy.ceil( x ):
        Corrected = min( i, ResourcesAvailable )
        Corrected = min( Corrected, MaxAlloc )
        Corrected = max( Corrected, 0 )
        ResourcesAvailable -= Corrected
        Allocations.append( Corrected )


    return numpy.array( Allocations )




def get_analytical_solution_for_given_lengths( InitialSeverities, CorrespondingLengths, PandemicParameter, MinAlloc, MaxAlloc ):

    return numpy.ceil( get_raw_analytical_solution_for_given_lengths(InitialSeverities, CorrespondingLengths, PandemicParameter, MinAlloc, MaxAlloc )).clip(0,10)

def get_raw_analytical_solution_for_given_lengths( InitialSeverities, CorrespondingLengths, PandemicParameter, MinAlloc, MaxAlloc):

    assert isinstance( InitialSeverities   , numpy.ndarray ) and InitialSeverities    . ndim == 1,   "InitialSeverities needs to be a 1D numpy array"
    assert isinstance( CorrespondingLengths, numpy.ndarray ) and CorrespondingLengths . ndim == 1,   "CorrespondingLengths needs to be a 1D numpy array"
    assert InitialSeverities.size == CorrespondingLengths.size,   "InitialSeverities and CorrespondingLengths must be arrays of the same size"

  # Math symbolic aliases
    I = InitialSeverities
    n = CorrespondingLengths
    α = PandemicParameter

  # Get analytical solution
    x  = (1 + α) ** n * I
    x /= (1 + α) ** n - 1

    return x
