"""
PES - Pandemic Experiment Scenario

Various logging utility functions:
 - create_ConsoleLog_filehandle_singleton
 - get_subject_id   # TODO confirm if necessary
 - print_settings
 - print_with_colour
 - tee
 - TODO update
"""


# ----------------
# external imports
# ----------------

import os
import datetime

# ----------------
# internal imports
# ----------------

from .. import *


# -----------------------------------------
# module variables requiring initialization
# -----------------------------------------

ConsoleLog_filehandle = None



####################
### Module functions
####################

def create_ConsoleLog_filehandle_singleton( SubjectId : str ):
    """
    Returns the existing filehandle to a log file for redirecting console output to.
    If none exists, it creates this instance and makes it available to the module.

    In theory you should never have a reason to 'reset' this singleton. However, if you'd like to do that regardless, you
    can do so by manually overwriting the existing module-global ConsoleLog_filehandle object with None (preferably closing
    the old one first!), which will cause this function to create a fresh one.
    """

    assert SubjectId is not None

    global ConsoleLog_filehandle

    if ConsoleLog_filehandle is None:
        ConsoleLog_filename   = os.path.join( OUTPUTS_PATH, f'{OUTPUT_FILE_PREFIX}log_{SubjectId}.txt' )
        ConsoleLog_filehandle = ConsoleLog_filehandle = open( ConsoleLog_filename, 'w' )


    return ConsoleLog_filehandle




def close_consolelog_filehandle():

    global ConsoleLog_filehandle
    assert ConsoleLog_filehandle is not None, "ConsoleLog_filehandle provided was None. Aborting `close` operation."
    ConsoleLog_filehandle.close()




def print_settings( **kwargs ):
    """
    Print / log various settings of the experiment
    """

    assert ConsoleLog_filehandle is not None, \
           "Contractual precondition violated: ConsoleLog_filehandle should not be empty"


    # Log all relevant init variables first.
    # No need to 'tee' anything at this point, since these will have already been
    # printed by __init__.

    InitVarsToLog = [
    #   variable name, variable value, optional default value check
      ( 'PKG_ROOT',                           PKG_ROOT                                                                 ),
      ( 'CONFIG_FILE',                        CONFIG_FILE                                                              ),
      ( 'AGGREGATION_METHOD',                 AGGREGATION_METHOD                 , 'confidence_weighted_median'        ),
      ( 'AVAILABLE_RESOURCES_PER_SEQUENCE',   AVAILABLE_RESOURCES_PER_SEQUENCE   , 49                                  ),
      ( 'AVATAR_ICONS_SET',                   AVATAR_ICONS_SET                   , 'PlaceholderAvatars'                ),
      ( 'CITY_RADIUS_REFLECTS_SEVERITY',      CITY_RADIUS_REFLECTS_SEVERITY      , False                               ),
      ( 'COLORS',                             COLORS                                                                   ),
      ( 'CONFIDENCE_TIMEOUT',                 CONFIDENCE_TIMEOUT                 , 5000                                ),
      ( 'CONFIDENCE_UPDATE_AMOUNT',           CONFIDENCE_UPDATE_AMOUNT           , 0.05                                ),
      ( 'DEBUG',                              DEBUG                              , False                               ),
      ( 'DEBUG_RESOLUTION',                   DEBUG_RESOLUTION                   , (762, 720)                          ),
      ( 'DETECT_USER_RESOLUTION',             DETECT_USER_RESOLUTION             , True                                ),
      ( 'DISPLAY_FEEDBACK',                   DISPLAY_FEEDBACK                   , True                                ),
      ( 'FALLBACK_RESOLUTION',                FALLBACK_RESOLUTION                , (1143, 1080)                        ),
      ( 'FEEDBACK_SHOW_COMBINED_ALLOCATIONS', FEEDBACK_SHOW_COMBINED_ALLOCATIONS , False                               ),
      ( 'FORCE_MOUSEWHEEL_SCROLL_CONFIDENCE', FORCE_MOUSEWHEEL_SCROLL_CONFIDENCE , False                               ),
      ( 'INIT_NO_OF_CITIES',                  INIT_NO_OF_CITIES                  , 2                                   ),
      ( 'INPUTS_PATH',                        INPUTS_PATH                        , os.path.join( PKG_ROOT, 'inputs' )  ),
      ( 'LIVE_EXPERIMENT',                    LIVE_EXPERIMENT                    , True                                ),
      ( 'LOBBY_PLAYERS',                      LOBBY_PLAYERS                      , 4                                   ),
      ( 'LOBBY_TIMEOUT',                      LOBBY_TIMEOUT                      , 300                                 ),
      ( 'MAX_ALLOCATABLE_RESOURCES',          MAX_ALLOCATABLE_RESOURCES          , 10                                  ),
      ( 'MAX_INIT_RESOURCES',                 MAX_INIT_RESOURCES                 , 6                                   ),
      ( 'MAX_INIT_SEVERITY',                  MAX_INIT_SEVERITY                  , 5                                   ),
      ( 'MIN_ALLOCATABLE_RESOURCES',          MIN_ALLOCATABLE_RESOURCES          , 0                                   ),
      ( 'MIN_INIT_RESOURCES',                 MIN_INIT_RESOURCES                 , 3                                   ),
      ( 'MIN_INIT_SEVERITY',                  MIN_INIT_SEVERITY                  , 2                                   ),
      ( 'MOVEMENT_REFRESH_RATE',              MOVEMENT_REFRESH_RATE              , 7                                   ),
      ( 'NUM_ATTEMPTS_TO_ASSIGN_SEQ',         NUM_ATTEMPTS_TO_ASSIGN_SEQ         , 8                                   ),
      ( 'NUM_BLOCKS',                         NUM_BLOCKS                         , 8                                   ),
      ( 'NUM_MAX_TRIALS',                     NUM_MAX_TRIALS                     , 10                                  ),
      ( 'NUM_MIN_TRIALS',                     NUM_MIN_TRIALS                     , 3                                   ),
      ( 'NUM_PREDEFINED_CITY_COORDS',         NUM_PREDEFINED_CITY_COORDS         , 25                                  ),
      ( 'NUM_SEQUENCES',                      NUM_SEQUENCES                      , 8                                   ),
      ( 'OUTPUT_FILE_PREFIX',                 OUTPUT_FILE_PREFIX                 , 'PES_full_'                       ),
      ( 'OUTPUTS_PATH',                       OUTPUTS_PATH                       , os.path.join( PKG_ROOT, 'outputs' ) ),
      ( 'PLAYER_TYPE',                        PLAYER_TYPE                        , 'human'                             ),
      ( 'PLAYBACK_ID',                        PLAYBACK_ID                                                              ),
      ( 'RANDOM_INITIAL_SEVERITY',            RANDOM_INITIAL_SEVERITY            , False                               ),
      ( 'RESPONSE_TIMEOUT',                   RESPONSE_TIMEOUT                   , 10000                               ),
      ( 'RESPONSE_MULTIPLIER',                RESPONSE_MULTIPLIER                , 0.2                                 ),
      ( 'SAVE_INITIAL_SEVERITY_TO_FILE',      SAVE_INITIAL_SEVERITY_TO_FILE      , False                               ),
      ( 'SAVE_RESULTS',                       SAVE_RESULTS                       , True                                ),
      ( 'SEVERITY_MULTIPLIER',                SEVERITY_MULTIPLIER                , 1.2                                 ),
      ( 'SHOW_PYGAME_IF_NONHUMAN_PLAYER',     SHOW_PYGAME_IF_NONHUMAN_PLAYER     , False                               ),
      ( 'STARTING_BLOCK_INDEX',               STARTING_BLOCK_INDEX               , 0                                   ),
      ( 'STARTING_SEQ_INDEX',                 STARTING_SEQ_INDEX                 , 0                                   ),
      ( 'TOTAL_NUM_TRIALS_IN_BLOCK',          TOTAL_NUM_TRIALS_IN_BLOCK          , 45                                  ),
      ( 'USE_FIXED_BLOCK_SEQUENCES',          USE_FIXED_BLOCK_SEQUENCES          , True                                ),
      ( 'VERBOSE',                            VERBOSE                            , True                                ),
      ( 'BIOSEMI_CONNECTED',                  BIOSEMI_CONNECTED                  , False                               ),
      ( 'SEQ_LENGTHS_FILE',                   SEQ_LENGTHS_FILE                   , 'sequence_lengths.csv'              ),
      ( 'INITIAL_SEVERITY_FILE',              INITIAL_SEVERITY_FILE              , 'initial_severity.csv'              )
    ]


  # Write above initialisation parameters to logfile
    def write( *args, **kwargs ):   print( *args, file = ConsoleLog_filehandle, **kwargs )

    write( )
    write( )
    write( '-- Initialisation parameters --' )
    write( )

    for Var in InitVarsToLog:
        if len( Var ) > 2 and Var[ 1 ] != Var[ 2 ]:
            write( f"{ Var[ 0 ] }: { Var[ 1 ] } (Suggested: { Var[ 2 ] })" )
        else:
            write( f"{ Var[ 0 ] }: { Var[ 1 ] }" )


  # Proceed to runtime-derived parameters (passed into this function as kwargs)
    write( )
    write( )
    write( '-- Parameters derived at runtime --' )
    write( )


    # We will be 'tee-ing' manually from now on, to print on the terminal as
    # well as write to the logfile

    def printvar( Varname, Var ):
        printinfo( f"log_utils: Setting {Varname} to {ANSI.ORANGE}{Var}" )


    printvar( 'Date' , kwargs    [ 'Date' ] )
    write   ( 'Date:', kwargs.pop( 'Date' ) )

    printvar( 'SubjectId' , kwargs    [ 'SubjectId' ] )
    write   ( 'SubjectId:', kwargs.pop( 'SubjectId' ) )




def tee( *Strings, **kwargs ):
    """
    Utility to simultaneously print a string to the terminal and also write it
    to a filehandle with an associated timestamp. Defaults to ANSI Blue colour
    if no other colours are used.

    Any ansi color sequences are stripped before writing to file, but are kept
    for printing to the terminal.
    """

    global ConsoleLog_filehandle
    assert ConsoleLog_filehandle is not None, "ConsoleLog_filehandle has not been initialised in module"

    if 'file'  in kwargs:   kwargs.pop( 'file' )
    if 'flush' in kwargs:   kwargs.pop( 'flush' )

    Strings = [ ANSI.BLUE + str(Str) + ANSI.RESET for Str in Strings ]

    ColorlessStrings = []
    for Str in Strings:
        ColorlessStrings.append( strip_colour( Str ) )

    if VERBOSE: print( *Strings, flush = True, **kwargs )
    print( '[', datetime.datetime.now( tz = datetime.timezone.utc ), ']:', *ColorlessStrings, file = ConsoleLog_filehandle, flush = True, **kwargs )




def strip_colour( Str ):
    AnsiColours = [i for i in dir( ANSI ) if not i.startswith( '_' )]
    for Colour in AnsiColours:  Str = Str.replace( getattr( ANSI, Colour ), '' )
    return Str






