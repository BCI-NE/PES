
import unittest, unittest.mock
import pygame
import glob
import math
import numpy 
import tensorflow as tf



import sys, os

from PES.src.pygameMediator import entropy, calculate_agent_response_and_confidence
from PES.src.pygameMediator import convert_globalseq_to_seqs

from PES.src import lobbyManager
from PES.src import exp_utils

from PES.src import log_utils

from PES import printinfo, printstatus


from PES import VERBOSE
from PES import MAX_ALLOCATABLE_RESOURCES
from PES import MIN_ALLOCATABLE_RESOURCES
from PES import INPUTS_PATH
from PES import NUM_SEQUENCES
from PES import LOBBY_PLAYERS
from PES.src.pygameMediator import Agent

from PES import ANSI


# --------------------------------------------------------
# Print a nice header identifying the module under testing
# --------------------------------------------------------

class Test_( unittest.TestCase ):   # Note: the name 'Test_' guarantees
                                    # (alphabetically) this TestCase is run
                                    # before other TestCases in this module

    def setUpClass():
        print(                                                          )
        print( "******************************************************" )
        print( "*** Unit tests for packagename.src.ai module" )
        print( "******************************************************" )
        print(                                                          )
    def tearDownClass ():   print( )


  # add dummy test so that the testcase is picked up during discovery
    def test_( self ): 
        # Set Subject id automatically in 'minimum three digit' format (e.g. '001')
        MySubjectId = exp_utils.create_random_subject_id()
        if VERBOSE:   printinfo( "__main__: Creating lobby ... ", end = '', flush = True )
        lobbyManager.set_up_lobby( MySubjectId )
        if VERBOSE:   printstatus( 'Done', ANSI.GREEN )

        log_utils.create_ConsoleLog_filehandle_singleton( MySubjectId )

        firstPlayer = True
        
        Players = lobbyManager.Lobby
        for PlayerAddr, PlayerId in Players.items():
            if int(PlayerId[:3]) < int(MySubjectId[:3]): 
                firstPlayer = False
            if PlayerId == MySubjectId:
                printinfo( f'{ANSI.ORANGE} • Player {PlayerId} -- {PlayerAddr}{ANSI.RESET} <-- active player' )
            else:
                printinfo( f'{ANSI.ORANGE} • Player {PlayerId} -- {PlayerAddr}{ANSI.RESET}' )

        NumPlayers = len( Players )

        lobbyManager.set_up_TCP_server()

        assert True, 'stop'


        import time
        import random
        random.seed()
        time.sleep(10)


        CurrentBlockIndex = 0
        CurrentSequenceIndex = 0
        for TrialId in range(360):
            printinfo(f'Trial {TrialId} ----------------------------------------------------------')

            seq_length = (TrialId % 12) + 3
            SeveritiesOfCurrentlyVisibleCities = numpy.random.random((seq_length+2,))

            response = numpy.random.random((1,1,seq_length))
            confidence = numpy.random.random((1,1,seq_length))

            circle_radius = numpy.random.random((seq_length+2,))

            # Send a message to all other players (contains response, confidence, and final severities).
            MyMessage = numpy.c_ [ response   [ CurrentBlockIndex ][ CurrentSequenceIndex ],
                        confidence [ CurrentBlockIndex ][ CurrentSequenceIndex ],
                        SeveritiesOfCurrentlyVisibleCities[ 2 : ],
                        circle_radius [ 2 : ]
                        ]

            if (firstPlayer):
                time.sleep(random.randrange(1,10)+20)
            else:
                time.sleep(random.randrange(1,10))

            # Collect your own response and that of all the other players
            PlayerIds, PlayerMessages = lobbyManager.send_and_request_stream(TrialId, MyMessage)
            AllPlayerIds = [ MySubjectId ] + PlayerIds
            AllMessages  = [ MyMessage   ] + PlayerMessages

            printinfo( f'Number of available responses:{len(AllMessages)}')

            #print(AllMessages)

    def test_1( self ): 
        # Set Subject id automatically in 'minimum three digit' format (e.g. '001')
        MySubjectId = exp_utils.create_random_subject_id()
        if VERBOSE:   printinfo( "__main__: Creating lobby ... ", end = '', flush = True )
        lobbyManager.set_up_lobby( MySubjectId )
        if VERBOSE:   printstatus( 'Done', ANSI.GREEN )

        log_utils.create_ConsoleLog_filehandle_singleton( MySubjectId )

        firstPlayer = True
        
        Players = lobbyManager.Lobby
        for PlayerAddr, PlayerId in Players.items():
            if int(PlayerId[:3]) < int(MySubjectId[:3]): 
                firstPlayer = False
            if PlayerId == MySubjectId:
                printinfo( f'{ANSI.ORANGE} • Player {PlayerId} -- {PlayerAddr}{ANSI.RESET} <-- active player' )
            else:
                printinfo( f'{ANSI.ORANGE} • Player {PlayerId} -- {PlayerAddr}{ANSI.RESET}' )

        NumPlayers = len( Players )

        lobbyManager.set_up_UDP_server()


        import time
        import random
        random.seed()
        time.sleep(10)


        CurrentBlockIndex = 0
        CurrentSequenceIndex = 0
        for TrialId in range(360):
            printinfo(f'Trial {TrialId} ----------------------------------------------------------')

            seq_length = (TrialId % 12) + 3
            SeveritiesOfCurrentlyVisibleCities = numpy.random.random((seq_length+2,))

            response = numpy.random.random((1,1,seq_length))
            confidence = numpy.random.random((1,1,seq_length))

            circle_radius = numpy.random.random((seq_length+2,))

            # Send a message to all other players (contains response, confidence, and final severities).
            MyMessage = numpy.c_ [ response   [ CurrentBlockIndex ][ CurrentSequenceIndex ],
                        confidence [ CurrentBlockIndex ][ CurrentSequenceIndex ],
                        SeveritiesOfCurrentlyVisibleCities[ 2 : ],
                        circle_radius [ 2 : ]
                        ]

            if (firstPlayer):
                time.sleep(random.randrange(1,10)+20)
            else:
                time.sleep(random.randrange(1,10))

            # Collect your own response and that of all the other players
            PlayerIds, PlayerMessages = lobbyManager.send_data_and_request_data_from_players(TrialId, MyMessage)
            AllPlayerIds = [ MySubjectId ] + PlayerIds
            AllMessages  = [ MyMessage   ] + PlayerMessages

            printinfo( f'Number of available responses:{len(AllMessages)}')

            #print(AllMessages)



if __name__ == '__main__':
    t = Test_()
    t.test_()

