"""
This is an alternative configuration file, which sets the experiment up for use
by an artificial agent PLAYING SOLO
"""

import sys
import os

# Import default config file
sys.path.append( os.path.join( os.path.dirname( __file__ ), '..' ) )
from CONFIG import *

#############
### Overrides
#############

DEBUG = True
PLAYER_TYPE = 'ai'
LOBBY_PLAYERS = 1
