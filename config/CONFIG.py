## This is the project's main configuration file.
##
## Any configuration variables appearing here will be imported by the project's __init__ file to perform appropriate
## initialization.

import os

## Notes:
## According to the original specs, the experiment will be divided in 6 to 8 "blocks", each comprising 8-12 "sequences
## of trials". For the purposes of the current code, these terms are understood as follows:
##   - Sequence   : A single map scene on which you annotate several cities, constitutes a 'sequence' of trials.
##   - Trial      : Each city the Agent annotates (e.g. with the mouse) on a map is a 'trial'.
##   - Block      : A collection of 8 to 12 sequences (i.e. maps)
##   - Experiment : A collection of blocks, intended to be completed by a participant in a single experimental session
##                  (with optional breaks after every few blocks).

def get_INPUTS_PATH ( PkgRoot ):   return os.path.join( PkgRoot, 'inputs'  )   ## Specify a path for input data (e.g. csv files). The default here places them 'inside' the package (given an appropriate __init__)
def get_OUTPUTS_PATH( PkgRoot ):   return os.path.join( PkgRoot, 'outputs' )   ## Specify a path for outputs. The default here places them 'inside' the package (given an appropriate __init__)

AGGREGATION_METHOD = {  1: 'confidence_weighted_median',
                        2: 'confidence_weighted_mean',
                        3: 'confidence_weighted_mode'
                     }[ 2 ]    # <-- select option here

ALLOCATION_TYPE = {  1: 'shared',       # Allocation is decided via vote, resources are shared, the voted allocation is taken of the shared pool of resources
                     2: 'individual',   # Allocation is decided via vote, but each individual has their own resource pool, which is unaffected by what was actually allocated by the group.
                     3: 'penalised',    # Allocation is shared, but individuals are penalised to the extent that they have overallocated compared to the group decision.
                     4: 'proportional'
                  }[ 1 ]   # <-- select option here

AVAILABLE_RESOURCES_PER_SEQUENCE = 39    # Suggested Value: 39      ## The number of available resources at the start of a sequence. Note, some of these will be consumed by the 'initial' cities, whose allocation is not under the user's control. Therefore this is not necessarily equal to the number of resources available to the user for allocation.

AVATAR_ICONS_SET = [   # uncomment as needed
#   'AnimalAvatars',
   'PlaceholderAvatars'
][ 0 ]

# These will determine which block indices will be in 'joint' mode and which in 'solo'.
BLOCK_MODE_INDICES = { 'Joint': [2,3,4,5,6,7],
                       'Solo' : [0,1]   }


CITY_RADIUS_REFLECTS_SEVERITY = False    # Suggested Value: False   ## If true, a city's severity status is reflected visually by the radius of the marker, as well as the colour.

COLORS = {  0: (245, 243, 243),     # Faint pink, almost white   ## Define the (11) different colours that the city markers will display with increasing severity:
            1: (237, 230, 230),     #
            2: (231, 215, 215),     #
            3: (227, 198, 198),     #
            4: (224, 180, 180),     #
            5: (224, 137, 137),     # ... increasingly saturated red in between
            6: (227, 113, 113),     #
            7: (231,  88,  88),     #
            8: (237,  60,  60),     #
            9: (245,  31,  31),     #
           10: (255,   0,   0)  }   # Fully saturated red

CONFIDENCE_TIMEOUT = 5000                  # Suggested Value: 5000         ## Delay (in milliseconds) after which it is assumed the user has failed to provide a confidence.

# Note: The product of MOVEMENT_REFRESH_RATE and CONFIDENCE_UPDATE_AMOUNT should ideally be between 0.05 and 0.1. See below at the MOVEMENT_REFRESH_RATE entry for details.
CONFIDENCE_UPDATE_AMOUNT= 0.05  # Suggested Value: 0.01 for online, 0.05 for biosemi on server.  ## Determines by how much confidence is increased per pygame event (e.g. mousewheel)

DEBUG_RESOLUTION = (962, 920 )                # Suggested Value: (762, 720)   ## This resolution will be applied if running in DEBUG = False mode.
DEBUG = False                                 # Suggested Value: False        ## Set to True to test the experimental setup without having to go through entire experiment Set to False to conduct a proper experiment, without the ability to escape.
BIOSEMI_CONNECTED = False                     # Whether or not the biosemi device is connected.
DETECT_USER_RESOLUTION = True                 # Suggested Value: True         ## If True, the user's resolution will be detected automatically, and used to create a fullscreen window for the experiment. Ignored when DEBUG is True.
DISPLAY_FEEDBACK = True                       # Suggested Value: True
FALLBACK_RESOLUTION = (1143, 1080)            # Suggested Value: (1143,1080)  ## This resolution will be applied if DETECT_USER_RESOLUTION = False (and not running in DEBUG mode)
FEEDBACK_SHOW_COMBINED_ALLOCATIONS = False    # Suggested Value: False  ## If True, the combined allocations (i.e. the allocation resulting from the group vote) will also be shown in the top feedback graph showing allocation decisions by players.
FEEDBACK_SHOW_INDIVIDUAL_PERFORMANCES = True  # Suggested Value: False  ## If True, the theoretical performance of each individual will be shown alongside the group performance.
FEEDBACK_SHOW_GROUP_PERFORMANCE = False        # Suggested Value: True   ## If true, the group performance is shown. Note: this will always be forced to true in-game if 'feedback_show_individual_performances' is false.
FORCE_MOUSEWHEEL_SCROLL_CONFIDENCE = True     # Suggested Value: False  ## If False, default confidence marking is point-to-click, except when biosemi is connected. Setting this to true forces the scroll interface regardless of a biosemi connection. Mostly for testing purposes.
SHOW_PYGAME_IF_NONHUMAN_PLAYER = False        # Suggested Value: False
INIT_NO_OF_CITIES = 2                         # Suggested Value: 2            ## This specifies the number of cities that will be given answers already at the start of each map, before the user starts making decisions

INITIAL_SEVERITY_FILE = {  1: 'initial_severity.csv',   # Suggested value
                           2: 'practice_severity.csv'   # Alternative, used for practice session
                        }[ 1 ]   # <-- select option here

LIVE_EXPERIMENT = True                    # Suggested Value: False        ## If this is True, it means we are using this on an actual participant, and we will be generating a subject Id and asking about age, gender, etc. If False, we are simply testing, and therefore only test files will be generated.

LOBBY_PLAYERS = 2      # Suggested Value: 4
LOBBY_TIMEOUT = 300    # Suggested Value: 300  (i.e. 5 minute timeout period)   ## Set amount of time for which lobby will be accepting connections (per client)

MAX_ALLOCATABLE_RESOURCES = 10  # Suggested Value: 10
MAX_INIT_RESOURCES = 6          # Suggested Value: 6
MAX_INIT_SEVERITY  = 5          # Suggested Value: 5
MIN_ALLOCATABLE_RESOURCES = 0   # Suggested Value: 0
MIN_INIT_RESOURCES = 3          # Suggested Value: 3
MIN_INIT_SEVERITY  = 2          # Suggested Value: 2       ## Severity and Resources min/max ranges for the random initialisation of the "Initial Cities" in a sequence.

# Note: The product of MOVEMENT_REFRESH_RATE and CONFIDENCE_UPDATE_AMOUNT should ideally be between 0.05 and 0.1, to
# ensure the screen is redrawn at a resolution that is lower than the desired confidence values. Faster environments can
# afford to have lower refresh rates (down to a minimum of 1). Slower environments (e.g. ssh) might benefit from a
# higher refresh rate, with an appropriately increased update amount.
MOVEMENT_REFRESH_RATE = 1      # Suggested Value: 10 for online, 1 for biosemi ## Determines every how many mouse movement events a screen redraw instruction will be honoured

NUM_ATTEMPTS_TO_ASSIGN_SEQ = 8  # Suggested Value: 8       ## During the process of assigning a random map to a sequence in a block, this constant dictates how many attempts at assignment will be made per sequence (XXX why?). Each attempt overrides the previous one, unless the same map already exists in the block, or the default map '0' is selected. If no valid attempts have occurred after this number of attempts, the default map '0' is used
NUM_BLOCKS = 8                  # Suggested Value: 8       ## Number of Blocks in the Experiment (between 6 and 8 according to spec document)
NUM_MAX_TRIALS = 10             # Suggested Value: 10      ## Maximum number of trials that can be allocated to a sequence
NUM_MIN_TRIALS = 3              # Suggested Value: 3       ## Minimum number of trials that can be allocated to a sequence
NUM_PREDEFINED_CITY_COORDS = 25 # Suggested Value: 25      ## For each map, there exists a file containing a collection of 25 possible coordinate-pairs, that have been predefined by hand
NUM_SEQUENCES = 8               # Suggested Value: 8       ## Number of Sequences (i.e. 'maps') per Block (between 8 and 12 according to spec)

OUTPUT_FILE_PREFIX = 'PES_full_'    # Suggested Value: 'PES_full_'   ## This will be prepended to any output files placed in the 'results' folder

   ## Select kind of player. Uncomment as needed to choose between 'human', 'ai', or 'playback'. If the type is 'playback', also specify the Subject ID that will be played back.
PLAYER_TYPE = {  1: 'human'       ,
                 2: 'ai'          ,
                 3: 'humanised_ai',
                 4: 'playback'    ,
                 5: 'RL-Agent'
              }[ 1 ]   # <-- select option here

PLAYBACK_ID = '001'   # only used during 'playback' mode
AGENT_NOISE_VARIANCE = 8.0
AGENT_WAIT = True
RANDOM_INITIAL_SEVERITY = False       # Suggested Value: False   ## If False, initial severities are loaded from INITIAL_SEVERITY_FILE
PANDEMIC_PARAMETER = 0.4              # This gets converted to a severity multiplier and a response multiplier at initialisation
RESPONSE_TIMEOUT = 10000              # Suggested Value: 10000   ## Delay (in milliseconds) after which it is assumed the user has failed to provide a response.
SAVE_INITIAL_SEVERITY_TO_FILE = False # Suggested Value: False   ## If set to True, the array of 360 (8 blocks of 45 trials) values between 2-8 (inclusive) corresponding to the initialseverity for all trials in the experiment, will be saved to the file initial_severity.csv (overwriting older files if present).
SAVE_RESULTS = True                   # Suggested Value: True    ## Save behaviourial results in txt files

SEQ_LENGTHS_FILE = {  1: 'sequence_lengths.csv',   # Suggested Value
                      2: 'practice_lengths.csv'    # Alternative, used for practice session.
                   }[ 1 ]   # <-- select option here

SHOW_BEFORE_AND_AFTER_MAP = False   # If True, before the sequence feedback, we will also show a 'before and after' map,
                                    # comparing individual theoretical resulting severities on the map against the group
                                    # decision.

STARTING_BLOCK_INDEX = 0   # Default: 0  (i.e. start at the first block of the experiment)
STARTING_SEQ_INDEX   = 0   # Default: 0  (i.e. start at the first sequence of the selected block)

TOTAL_NUM_TRIALS_IN_BLOCK  = 45       # Suggested Value: 45      ## The total trials contained in a Block should be 45; in other words, the sum of trials over all sequences in a block should sum up to 45. Q: Why? A: According to Riccardo, this is probably to ensure that all blocks have more or less the same duration (i.e. so that breaks occur at relatively consistent intervals)
TRUST_MAX = 100                       # Suggested Value: 100     ## The maximum integer value on the trust slider scales. (previously 4, now 100)
USE_FIXED_BLOCK_SEQUENCES = True      # Suggested Value: True    ## If True, the length of each sequence is obtained from 'sequence_lengths.csv' file.
VERBOSE = True                        # Suggested Value: True    ## Set to True to enable informative messages on the terminal (e.g. initialization logs etc)




