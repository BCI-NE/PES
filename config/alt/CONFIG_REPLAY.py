"""
This is an alternative configuration file, which sets the experiment up to
replay an earlier player's allocation.
"""

import sys
import os

# Import default config file
sys.path.append( os.path.join( os.path.dirname( __file__ ), '..' ) )
from CONFIG import *

# Overrides
def get_OUTPUTS_PATH( PkgRoot ):   return os.path.join( '/', 'home', 'common', 'Experiment_3f_data' , '003_ct' )
PLAYER_TYPE = 'playback'; PLAYBACK_ID = '003'
