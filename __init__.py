# Package initialisation file.
#
# This file's role is to grab the relevant configuration preferences from
# /config/CONFIG.py and initialise the package.
#
# Do not add variables here that would be considered configuration parameters;
# only use this file to load the relevant configuration preferences from the
# CONFIG.py file, and to make them available to the other modules.

# To actually add/edit configuration options, edit the /config/CONFIG.py file
# directly (using normal python syntax), and then import / export here as
# needed.



#################################################################
### Initial imports and sanity checks required for initialization
#################################################################

import os
import sys
import numpy
import importlib

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame

# Check if --config was specified. If not, load the default CONFIG.py file.
if '--config' in sys.argv:
    ConfigParam  = sys.argv[ sys.argv.index( '--config' ) + 1 ]
    ConfigPath   = os.path.abspath( os.path.dirname( ConfigParam ) )
    ConfigModule = os.path.basename( ConfigParam )
    assert ConfigModule.endswith('py'), "The specified config file needs to be a valid python module"
    ConfigModule = ConfigModule[ : -3 ]
    sys.path.append( ConfigPath )
    CONFIG = importlib.import_module( ConfigModule )
else:
    from . config import CONFIG


# Detect package directory, and use to create standard paths relative to package
# root.

PKG_ROOT           = os.path.abspath( os.path.dirname(  __file__ ) )
CONFIG_FILE        = CONFIG.__file__
DOCUMENTATION_PATH = os.path.join( PKG_ROOT, 'doc' )
RESOURCES_PATH     = os.path.join( PKG_ROOT, 'res' )

# ANSI colour escape codes (for use in logging/debug messages)
class ANSI:
    BOLD   = '\033[1m'
    RED    = '\033[91m'
    GREEN  = '\033[92m'
    ORANGE = '\033[93m'
    BLUE   = '\033[94m'
    PURPLE = '\033[95m'
    RESET  = '\033[0m'


# Check that we are running in the context of a python virtual env, to ensure
# consistency/reproducibility between runs, in terms of what python
# packages/versions are installed and used in the experiment.

if not os.getenv( 'VIRTUAL_ENV' ):
    print(
f"""{ANSI.PURPLE}

Warning: No suitable VIRTUAL_ENV environmental variable detected.

In order to ensure consistency / reproducibility between runs, you might want to
consider always running this experiment from within a suitable python virtual
environment, containing the python package versions specified in the package's
requirements.txt file.

Press ENTER if you'd like to continue regardless (or Ctrl-C to abort).

{ANSI.RESET}""" )
    try                     : input()   # i.e. press Enter
    except KeyboardInterrupt: print( '\n\nExiting...' ); exit()



###################################
### Process selected CONFIG.py file
###################################

# Import all configuration constants
AGGREGATION_METHOD                          = CONFIG.AGGREGATION_METHOD
ALLOCATION_TYPE                             = CONFIG.ALLOCATION_TYPE
AVAILABLE_RESOURCES_PER_SEQUENCE            = CONFIG.AVAILABLE_RESOURCES_PER_SEQUENCE
AVATAR_ICONS_SET                            = CONFIG.AVATAR_ICONS_SET
BIOSEMI_CONNECTED                           = CONFIG.BIOSEMI_CONNECTED
BLOCK_MODE_INDICES                          = CONFIG.BLOCK_MODE_INDICES
CITY_RADIUS_REFLECTS_SEVERITY               = CONFIG.CITY_RADIUS_REFLECTS_SEVERITY
COLORS                                      = CONFIG.COLORS
CONFIDENCE_TIMEOUT                          = CONFIG.CONFIDENCE_TIMEOUT
CONFIDENCE_UPDATE_AMOUNT                    = CONFIG.CONFIDENCE_UPDATE_AMOUNT
DEBUG                                       = CONFIG.DEBUG
DEBUG_RESOLUTION                            = CONFIG.DEBUG_RESOLUTION
DETECT_USER_RESOLUTION                      = CONFIG.DETECT_USER_RESOLUTION
DISPLAY_FEEDBACK                            = CONFIG.DISPLAY_FEEDBACK
FALLBACK_RESOLUTION                         = CONFIG.FALLBACK_RESOLUTION
FEEDBACK_SHOW_COMBINED_ALLOCATIONS          = CONFIG.FEEDBACK_SHOW_COMBINED_ALLOCATIONS
FEEDBACK_SHOW_GROUP_PERFORMANCE             = CONFIG.FEEDBACK_SHOW_GROUP_PERFORMANCE
FEEDBACK_SHOW_INDIVIDUAL_PERFORMANCES       = CONFIG.FEEDBACK_SHOW_INDIVIDUAL_PERFORMANCES
FORCE_MOUSEWHEEL_SCROLL_CONFIDENCE          = CONFIG.FORCE_MOUSEWHEEL_SCROLL_CONFIDENCE
INIT_NO_OF_CITIES                           = CONFIG.INIT_NO_OF_CITIES
INITIAL_SEVERITY_FILE                       = CONFIG.INITIAL_SEVERITY_FILE
INPUTS_PATH                                 = CONFIG.get_INPUTS_PATH( PKG_ROOT )
LIVE_EXPERIMENT                             = CONFIG.LIVE_EXPERIMENT
LOBBY_PLAYERS                               = CONFIG.LOBBY_PLAYERS
LOBBY_TIMEOUT                               = CONFIG.LOBBY_TIMEOUT
MAX_ALLOCATABLE_RESOURCES                   = CONFIG.MAX_ALLOCATABLE_RESOURCES
MAX_INIT_RESOURCES                          = CONFIG.MAX_INIT_RESOURCES
MAX_INIT_SEVERITY                           = CONFIG.MAX_INIT_SEVERITY
MIN_ALLOCATABLE_RESOURCES                   = CONFIG.MIN_ALLOCATABLE_RESOURCES
MIN_INIT_RESOURCES                          = CONFIG.MIN_INIT_RESOURCES
MIN_INIT_SEVERITY                           = CONFIG.MIN_INIT_SEVERITY
MOVEMENT_REFRESH_RATE                       = CONFIG.MOVEMENT_REFRESH_RATE
NUM_ATTEMPTS_TO_ASSIGN_SEQ                  = CONFIG.NUM_ATTEMPTS_TO_ASSIGN_SEQ
NUM_BLOCKS                                  = CONFIG.NUM_BLOCKS
NUM_MAX_TRIALS                              = CONFIG.NUM_MAX_TRIALS
NUM_MIN_TRIALS                              = CONFIG.NUM_MIN_TRIALS
NUM_PREDEFINED_CITY_COORDS                  = CONFIG.NUM_PREDEFINED_CITY_COORDS
NUM_SEQUENCES                               = CONFIG.NUM_SEQUENCES
OUTPUT_FILE_PREFIX                          = CONFIG.OUTPUT_FILE_PREFIX
OUTPUTS_PATH                                = CONFIG.get_OUTPUTS_PATH( PKG_ROOT )
PANDEMIC_PARAMETER                          = CONFIG.PANDEMIC_PARAMETER
PLAYER_TYPE                                 = CONFIG.PLAYER_TYPE
RANDOM_INITIAL_SEVERITY                     = CONFIG.RANDOM_INITIAL_SEVERITY
RESPONSE_TIMEOUT                            = CONFIG.RESPONSE_TIMEOUT
SAVE_INITIAL_SEVERITY_TO_FILE               = CONFIG.SAVE_INITIAL_SEVERITY_TO_FILE
SAVE_RESULTS                                = CONFIG.SAVE_RESULTS
SEQ_LENGTHS_FILE                            = CONFIG.SEQ_LENGTHS_FILE
SHOW_BEFORE_AND_AFTER_MAP                   = CONFIG.SHOW_BEFORE_AND_AFTER_MAP
SHOW_PYGAME_IF_NONHUMAN_PLAYER              = CONFIG.SHOW_PYGAME_IF_NONHUMAN_PLAYER
STARTING_BLOCK_INDEX                        = CONFIG.STARTING_BLOCK_INDEX
STARTING_SEQ_INDEX                          = CONFIG.STARTING_SEQ_INDEX
TOTAL_NUM_TRIALS_IN_BLOCK                   = CONFIG.TOTAL_NUM_TRIALS_IN_BLOCK
TRUST_MAX                                   = CONFIG.TRUST_MAX
USE_FIXED_BLOCK_SEQUENCES                   = CONFIG.USE_FIXED_BLOCK_SEQUENCES
VERBOSE                                     = CONFIG.VERBOSE
AGENT_NOISE_VARIANCE                        = CONFIG.AGENT_NOISE_VARIANCE
AGENT_WAIT                                  = CONFIG.AGENT_WAIT


##########################################
### Process imported configuration options
##########################################

if PLAYER_TYPE == 'playback':   PLAYBACK_ID = CONFIG.PLAYBACK_ID
else                        :   PLAYBACK_ID = 'N/A'

RESPONSE_MULTIPLIER = PANDEMIC_PARAMETER
SEVERITY_MULTIPLIER = 1 + PANDEMIC_PARAMETER



##################################################################
### Continue with non-configuration-related package initialization
##################################################################

# Let's define some some quick utility functions for logging purposes
def printcolor ( Str, AnsiColor, *args, **kwargs ):   print( f"{AnsiColor}{Str}{ANSI.RESET}", *args, **kwargs )
def printstatus( Str, AnsiColor, *args, **kwargs ):   print( f"{AnsiColor}[{ANSI.RESET}{Str}{AnsiColor}]{ANSI.RESET}", *args, **kwargs )
def printinfo ( Str, *args, **kwargs )            :   printcolor( Str , ANSI.BLUE, *args, **kwargs )
def printconfig( Varname, Var, SuggestedValue = None )   :
    if SuggestedValue is None or Var == SuggestedValue:
        printinfo( f"__init__: Setting { Varname } to { ANSI.ORANGE }{ Var }" )
    else:
        printinfo( f"__init__: Setting { Varname } to { ANSI.BOLD + ANSI.RED }{ Var }{ ANSI.RESET } (Suggested: {SuggestedValue})" )

printinfo( "\n--- Initializing experiment ---\n" )

# Import package documentation (to avoid having to dump it all on the top of this file instead). You could follow a
# similar strategy in other modules if they are to contain significant documentation that would clutter the sources.
PkgDoc = os.path.join( DOCUMENTATION_PATH, 'PES.__doc__' )
with open( PkgDoc, 'r' ) as f:   __doc__ = f.read()

# RGB tuples of frequently used colours
WHITE      = (255, 255, 255)
YELLOW     = (255, 255,   0)
BLACK      = (  0,   0,   0)
DARK_RED   = (128,   0,   0)
DARK_CYAN  = (  0, 128, 128)
DARK_GREEN = (  0, 128,   0)
GREEN      = (  0, 255,   0)
RED        = (255,   0,   0)
GRAY       = ( 50,  50,  50)
LIGHTGRAY  = (180, 180, 180)
LIGHTBLUE  = (210, 220, 255)

# The experiment uses tensorflow, which has a nasty habit of dumping lots of
# warning messages for missing nvidia libraries etc. The following environmental
# variable disables these. ( '0': all logs are shown; '1': filter out INFOs and
# below; '2': filter out WARNs; '3': filter out ERRORs, etc )
os.environ[ 'TF_CPP_MIN_LOG_LEVEL' ] ="2"

# Set some nice numpy printing defaults and error handling
numpy.set_printoptions( threshold = numpy.inf, precision = 3, suppress = True,
                        linewidth = 80, nanstr = "--", infstr = "∞"  )
numpy.seterr( all = 'raise' )

# Print all (important) final init variables to terminal
if VERBOSE not in [ True, False ]:
    raise ValueError( 'Bad value given for VERBOSE environmental variable. Needs to be True or False.' )


if VERBOSE:
#               Variable name                           Variable Value                           Suggested value check
    printconfig( 'PKG_ROOT'                             ,                              PKG_ROOT                                      )
    printconfig( 'CONFIG_FILE'                          ,                           CONFIG_FILE                                      )
    printconfig( 'AGGREGATION_METHOD'                   ,                    AGGREGATION_METHOD, 'confidence_weighted_median'        )
    printconfig( 'ALLOCATION_TYPE'                      ,                       ALLOCATION_TYPE, 'shared'                            )
    printconfig( 'AVAILABLE_RESOURCES_PER_SEQUENCE'     ,      AVAILABLE_RESOURCES_PER_SEQUENCE, 49                                  )
    printconfig( 'AVATAR_ICONS_SET'                     ,                      AVATAR_ICONS_SET, 'PlaceholderAvatars'                )
    printconfig( 'BLOCK_MODE_INDICES'                   ,                    BLOCK_MODE_INDICES                                      )
    printconfig( 'CITY_RADIUS_REFLECTS_SEVERITY'        ,         CITY_RADIUS_REFLECTS_SEVERITY, False                               )
    printconfig( 'COLORS'                               ,                                COLORS                                      )
    printconfig( 'CONFIDENCE_TIMEOUT'                   ,                    CONFIDENCE_TIMEOUT, 5000                                )
    printconfig( 'CONFIDENCE_UPDATE_AMOUNT'             ,              CONFIDENCE_UPDATE_AMOUNT, 0.05                                )
    printconfig( 'DEBUG'                                ,                                 DEBUG, False                               )
    printconfig( 'DEBUG_RESOLUTION'                     ,                      DEBUG_RESOLUTION, (762, 720)                          )
    printconfig( 'DETECT_USER_RESOLUTION'               ,                DETECT_USER_RESOLUTION, True                                )
    printconfig( 'DISPLAY_FEEDBACK'                     ,                      DISPLAY_FEEDBACK, True                                )
    printconfig( 'FALLBACK_RESOLUTION'                  ,                   FALLBACK_RESOLUTION, (1143, 1080)                        )
    printconfig( 'FEEDBACK_SHOW_COMBINED_ALLOCATIONS'   ,    FEEDBACK_SHOW_COMBINED_ALLOCATIONS, False                               )
    printconfig( 'FEEDBACK_SHOW_GROUP_PERFORMANCE'      , FEEDBACK_SHOW_GROUP_PERFORMANCE      , True                                )
    printconfig( 'FEEDBACK_SHOW_INDIVIDUAL_PERFORMANCES', FEEDBACK_SHOW_INDIVIDUAL_PERFORMANCES, False                               )
    printconfig( 'FORCE_MOUSEWHEEL_SCROLL_CONFIDENCE'   ,    FORCE_MOUSEWHEEL_SCROLL_CONFIDENCE, False                               )
    printconfig( 'INIT_NO_OF_CITIES'                    ,                     INIT_NO_OF_CITIES, 2                                   )
    printconfig( 'INPUTS_PATH'                          ,                           INPUTS_PATH, os.path.join( PKG_ROOT, 'inputs' )  )
    printconfig( 'LIVE_EXPERIMENT'                      ,                       LIVE_EXPERIMENT, True                                )
    printconfig( 'LOBBY_PLAYERS'                        ,                         LOBBY_PLAYERS, 4                                   )
    printconfig( 'LOBBY_TIMEOUT'                        ,                         LOBBY_TIMEOUT, 300                                 )
    printconfig( 'MAX_ALLOCATABLE_RESOURCES'            ,             MAX_ALLOCATABLE_RESOURCES, 10                                  )
    printconfig( 'MAX_INIT_RESOURCES'                   ,                    MAX_INIT_RESOURCES, 6                                   )
    printconfig( 'MAX_INIT_SEVERITY'                    ,                     MAX_INIT_SEVERITY, 5                                   )
    printconfig( 'MIN_ALLOCATABLE_RESOURCES'            ,             MIN_ALLOCATABLE_RESOURCES, 0                                   )
    printconfig( 'MIN_INIT_RESOURCES'                   ,                    MIN_INIT_RESOURCES, 3                                   )
    printconfig( 'MIN_INIT_SEVERITY'                    ,                     MIN_INIT_SEVERITY, 2                                   )
    printconfig( 'MOVEMENT_REFRESH_RATE'                ,                 MOVEMENT_REFRESH_RATE, 7                                   )
    printconfig( 'NUM_ATTEMPTS_TO_ASSIGN_SEQ'           ,            NUM_ATTEMPTS_TO_ASSIGN_SEQ, 8                                   )
    printconfig( 'NUM_BLOCKS'                           ,                            NUM_BLOCKS, 8                                   )
    printconfig( 'NUM_MAX_TRIALS'                       ,                        NUM_MAX_TRIALS, 10                                  )
    printconfig( 'NUM_MIN_TRIALS'                       ,                        NUM_MIN_TRIALS, 3                                   )
    printconfig( 'NUM_PREDEFINED_CITY_COORDS'           ,            NUM_PREDEFINED_CITY_COORDS, 25                                  )
    printconfig( 'NUM_SEQUENCES'                        ,                         NUM_SEQUENCES, 8                                   )
    printconfig( 'OUTPUT_FILE_PREFIX'                   ,                    OUTPUT_FILE_PREFIX, 'PES_full_'                       )
    printconfig( 'OUTPUTS_PATH'                         ,                          OUTPUTS_PATH, os.path.join( PKG_ROOT, 'outputs' ) )
    printconfig( 'PANDEMIC_PARAMETER'                   ,                   PANDEMIC_PARAMETER , 0.6                                 )
    printconfig( 'PLAYER_TYPE'                          ,                           PLAYER_TYPE, 'human'                             )
    printconfig( 'PLAYBACK_ID'                          ,                           PLAYBACK_ID                                      )
    printconfig( 'RANDOM_INITIAL_SEVERITY'              ,               RANDOM_INITIAL_SEVERITY, False                               )
    printconfig( 'RESPONSE_TIMEOUT'                     ,                      RESPONSE_TIMEOUT, 10000                               )
    printconfig( 'RESPONSE_MULTIPLIER'                  ,                   RESPONSE_MULTIPLIER, 0.6                                 )
    printconfig( 'SAVE_INITIAL_SEVERITY_TO_FILE'        ,         SAVE_INITIAL_SEVERITY_TO_FILE, False                               )
    printconfig( 'SAVE_RESULTS'                         ,                          SAVE_RESULTS, True                                )
    printconfig( 'SEVERITY_MULTIPLIER'                  ,                   SEVERITY_MULTIPLIER, 1.6                                 )
    printconfig( 'SHOW_BEFORE_AND_AFTER_MAP'            ,             SHOW_BEFORE_AND_AFTER_MAP, False                               )
    printconfig( 'SHOW_PYGAME_IF_NONHUMAN_PLAYER'       ,        SHOW_PYGAME_IF_NONHUMAN_PLAYER, False                               )
    printconfig( 'STARTING_BLOCK_INDEX'                 ,                  STARTING_BLOCK_INDEX, 0                                   )
    printconfig( 'STARTING_SEQ_INDEX'                   ,                    STARTING_SEQ_INDEX, 0                                   )
    printconfig( 'TOTAL_NUM_TRIALS_IN_BLOCK'            ,             TOTAL_NUM_TRIALS_IN_BLOCK, 45                                  )
    printconfig( 'TRUST_MAX'                            ,             TRUST_MAX                , 100                                 )
    printconfig( 'USE_FIXED_BLOCK_SEQUENCES'            ,             USE_FIXED_BLOCK_SEQUENCES, True                                )
    printconfig( 'VERBOSE'                              ,                               VERBOSE, True                                )
    printconfig( 'BIOSEMI_CONNECTED'                    ,                     BIOSEMI_CONNECTED, False                               )
    printconfig( 'SEQ_LENGTHS_FILE'                     ,                      SEQ_LENGTHS_FILE, 'sequence_lengths.csv'              )
    printconfig( 'INITIAL_SEVERITY_FILE'                ,                 INITIAL_SEVERITY_FILE, 'initial_severity.csv'              )


# Initialise pygame engine
if VERBOSE:
    printinfo( "__init__: Initializing pygame engine ... ", end = '', flush = True )
    pygame.init();
    printstatus( 'Done', ANSI.GREEN )
else:
    pygame.init()


# List of package variables to be made availbale to package modules
__all__ = [
    'PKG_ROOT',
    'CONFIG_FILE',
    'DOCUMENTATION_PATH',
    'RESOURCES_PATH',
    'VERBOSE',
    'BIOSEMI_CONNECTED',
    'SEQ_LENGTHS_FILE',
    'INITIAL_SEVERITY_FILE',
    'WHITE',
    'YELLOW',
    'BLACK',
    'DARK_RED',
    'DARK_CYAN',
    'DARK_GREEN',
    'GREEN',
    'RED',
    'GRAY',
    'LIGHTGRAY',
    'LIGHTBLUE',

    'ANSI',
    'printinfo',
    'printstatus',
    'printconfig',

    'AGGREGATION_METHOD',
    'ALLOCATION_TYPE',
    'AVAILABLE_RESOURCES_PER_SEQUENCE',
    'AVATAR_ICONS_SET',
    'BLOCK_MODE_INDICES',
    'CITY_RADIUS_REFLECTS_SEVERITY',
    'COLORS',
    'CONFIDENCE_TIMEOUT',
    'CONFIDENCE_UPDATE_AMOUNT',
    'DEBUG',
    'DEBUG_RESOLUTION',
    'DETECT_USER_RESOLUTION',
    'DISPLAY_FEEDBACK',
    'FALLBACK_RESOLUTION',
    'FEEDBACK_SHOW_COMBINED_ALLOCATIONS',
    'FEEDBACK_SHOW_GROUP_PERFORMANCE',
    'FEEDBACK_SHOW_INDIVIDUAL_PERFORMANCES',
    'FORCE_MOUSEWHEEL_SCROLL_CONFIDENCE',
    'INIT_NO_OF_CITIES',
    'INPUTS_PATH',
    'LIVE_EXPERIMENT',
    'LOBBY_PLAYERS',
    'LOBBY_TIMEOUT',
    'MAX_ALLOCATABLE_RESOURCES',
    'MAX_INIT_RESOURCES',
    'MAX_INIT_SEVERITY',
    'MIN_ALLOCATABLE_RESOURCES',
    'MIN_INIT_RESOURCES',
    'MIN_INIT_SEVERITY',
    'MOVEMENT_REFRESH_RATE',
    'NUM_ATTEMPTS_TO_ASSIGN_SEQ',
    'NUM_BLOCKS',
    'NUM_MAX_TRIALS',
    'NUM_MIN_TRIALS',
    'NUM_PREDEFINED_CITY_COORDS',
    'NUM_SEQUENCES',
    'OUTPUT_FILE_PREFIX',
    'OUTPUTS_PATH',
    'PANDEMIC_PARAMETER',
    'PLAYBACK_ID',
    'PLAYER_TYPE',
    'RANDOM_INITIAL_SEVERITY',
    'RESPONSE_MULTIPLIER',
    'RESPONSE_TIMEOUT',
    'SAVE_INITIAL_SEVERITY_TO_FILE',
    'SAVE_RESULTS',
    'SEVERITY_MULTIPLIER',
    'SHOW_BEFORE_AND_AFTER_MAP',
    'SHOW_PYGAME_IF_NONHUMAN_PLAYER',
    'STARTING_BLOCK_INDEX',
    'STARTING_SEQ_INDEX',
    'TOTAL_NUM_TRIALS_IN_BLOCK',
    'TRUST_MAX',
    'USE_FIXED_BLOCK_SEQUENCES'
]

if VERBOSE:   print()   # Just to separate initialization messages from rest of execution.
