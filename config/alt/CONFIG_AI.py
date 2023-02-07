"""
This is an alternative configuration file, which sets the experiment up for use
by an artificial agent.
"""

import sys
import os

# Import default config file
sys.path.append( os.path.join( os.path.dirname( __file__ ), '..' ) )
from CONFIG import *

#############
### Overrides
#############

PLAYER_TYPE = 'ai'
