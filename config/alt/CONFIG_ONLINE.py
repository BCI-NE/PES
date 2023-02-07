"""
This is an alternative configuration file, which sets the experiment up for use by a human (playing remotely)
"""

import sys
import os

# Import default config file
sys.path.append( os.path.join( os.path.dirname( __file__ ), '..' ) )
from CONFIG import *

#############
### Overrides
#############

BIOSEMI_CONNECTED = False        # Whether or not the biosemi device is connected.
PLAYER_TYPE = 'human'   ## Select kind of player. Uncomment as needed to choose between 'human', 'ai', or 'playback'. If the type is 'playback', also specify the Subject ID that will be played back.
