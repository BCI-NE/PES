"""
This is an alternative configuration file, which sets the experiment up for use by a human connected to a biosemi.
"""

import sys
import os

# Import default config file
sys.path.append( os.path.join( os.path.dirname( __file__ ), '..' ) )
from CONFIG import *

#############
### Overrides
#############

# Note: The product of MOVEMENT_REFRESH_RATE and CONFIDENCE_UPDATE_AMOUNT should ideally be between 0.05 and 0.1. See below at the MOVEMENT_REFRESH_RATE entry for details.

#CONFIDENCE_UPDATE_AMOUNT= 0.05  # Suggested Value: 0.01 for online, 0.05 for biosemi on cseebcipenguin.  ## Determines by how much confidence is increased per pygame event (e.g. mousewheel)

DEBUG = True                   # Suggested Value: False        ## Set to True to test the experimental setup without having to go through entire experiment Set to False to conduct a proper experiment, without the ability to escape.
BIOSEMI_CONNECTED = False        # Whether or not the biosemi device is connected.

INITIAL_SEVERITY_FILE = [
                          'initial_severity.csv',    # Suggested value
#                          'practice_severity.csv'   # Alternative, used for practice session
                        ][ 0 ]

LIVE_EXPERIMENT = False   # Suggested Value: False        ## If this is True, it means we are using this on an actual participant, and we will be generating a subject Id and asking about age, gender, etc. If False, we are simply testing, and therefore only test files will be generated.
LOBBY_PLAYERS = 2      # Suggested Value: 4

#MOVEMENT_REFRESH_RATE = 1      # Suggested Value: 10 for online, 1 for biosemi on cseebcipenguin ## Determines every how many mouse movement events a screen redraw instruction will be honoured

PLAYER_TYPE = 'human'   ## Select kind of player. Uncomment as needed to choose between 'human', 'ai', or 'playback'. If the type is 'playback', also specify the Subject ID that will be played back.

SEQ_LENGTHS_FILE = [
                     'sequence_lengths.csv',   # Suggested Value
#                     'practice_lengths.csv'   # Alternative, used for practice session.
                   ][ 0 ]

