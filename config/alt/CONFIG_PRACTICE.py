"""
This is an alternative configuration file, which sets the experiment up for use in practice mode.
"""

import sys
import os

# Import default config file
sys.path.append( os.path.join( os.path.dirname( __file__ ), '..' ) )
from CONFIG import *

#############
### Overrides
#############

INITIAL_SEVERITY_FILE = [
#                          'initial_severity.csv',    # Suggested value
                          'practice_severity.csv'   # Alternative, used for practice session
                        ][ 0 ]

LIVE_EXPERIMENT = False   # Suggested Value: False        ## If this is True, it means we are using this on an actual participant, and we will be generating a subject Id and asking about age, gender, etc. If False, we are simply testing, and therefore only test files will be generated.
LOBBY_PLAYERS = 1      # Suggested Value: 4

NUM_BLOCKS = 1                  # Suggested Value: 8       ## Number of Blocks in the Experiment (between 6 and 8 according to spec document)
NUM_SEQUENCES = 8               # Suggested Value: 8       ## Number of Sequences (i.e. 'maps') per Block (between 8 and 12 according to spec document)

PLAYER_TYPE = 'human'   ## Select kind of player. Uncomment as needed to choose between 'human', 'ai', or 'playback'. If the type is 'playback', also specify the Subject ID that will be played back.

SEQ_LENGTHS_FILE = [
#                     'sequence_lengths.csv',   # Suggested Value
                     'practice_lengths.csv'   # Alternative, used for practice session.
                   ][ 0 ]

