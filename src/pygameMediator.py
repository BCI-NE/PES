"""
PES - Pandemic Experiment Scenario

This module contains functions that provide a higher-level experiment-specific
interface to respective lower-level pygame engine functions.

Functions defined here:
 • ask_player_to_rate_colleagues_using_sliders
 • calculate_agent_response_and_confidence
 • calculate_agent_response_and_confidence_alternative
 • convert_globalseq_to_seqs
 • divide_circle
 • down_arrow
 • draw_city_marker
 • entropy
 • get_age_from_user
 • get_gender_from_user
 • get_handedness_from_user
 • get_user_input
 • gracefully_quit_pygame
 • hide_mouse_cursor
 • init_pygame_display
 • load_image
 • provide_agent_confidence
 • provide_agent_response
 • provide_confidence
 • provide_replay_confidence
 • provide_replay_response
 • provide_response
 • provide_rl_agent_response
 • provide_user_confidence
 • provide_user_response
 • reset_screen
 • rl_agent_meta_cognitive
 • screen_messages
 • set_window_title
 • show_before_and_after_map
 • show_end_of_trial_feedback
 • show_feedback
 • show_images
 • show_message_and_wait
 • up_arrow
"""

# ----------------
# external imports
# ----------------

import copy
import glob
import math
import numpy
import os
import pygame
import sys
import tensorflow as tf

# ----------------
# internal imports
# ----------------

from .. import ANSI
from .. import AVAILABLE_RESOURCES_PER_SEQUENCE
from .. import AVATAR_ICONS_SET
from .. import BIOSEMI_CONNECTED
from .. import COLORS
from .. import CONFIDENCE_TIMEOUT
from .. import CONFIDENCE_UPDATE_AMOUNT
from .. import DEBUG_RESOLUTION
from .. import FALLBACK_RESOLUTION
from .. import FORCE_MOUSEWHEEL_SCROLL_CONFIDENCE
from .. import INPUTS_PATH
from .. import LOBBY_PLAYERS
from .. import MOVEMENT_REFRESH_RATE
from .. import MAX_ALLOCATABLE_RESOURCES
from .. import MIN_ALLOCATABLE_RESOURCES
from .. import NUM_SEQUENCES
from .. import OUTPUT_FILE_PREFIX
from .. import OUTPUTS_PATH
from .. import PLAYER_TYPE
from .. import RESOURCES_PATH
from .. import RESPONSE_TIMEOUT
from .. import TRUST_MAX
from .. import VERBOSE
from .. import WHITE, YELLOW, BLACK, DARK_RED, DARK_CYAN, DARK_GREEN, GREEN, RED, GRAY, LIGHTGRAY, LIGHTBLUE
from .. import SEQ_LENGTHS_FILE
from .. import SHOW_PYGAME_IF_NONHUMAN_PLAYER
from .. import AGENT_NOISE_VARIANCE
from .. import AGENT_WAIT 

if PLAYER_TYPE == 'playback': from .. import PLAYBACK_ID

from . import exp_utils
from . import log_utils
from . import Agent
from . Agent import agent_meta_cognitive, adjust_response_decay, boltzmann_decay, get_random_confidence 
from . exp_utils import chain_ops
from . import eventMarker
from . eventMarker import evmrk
from .. import printinfo
from .. import printcolor
from .. ext.tools import pick_human_reported_confidence, humanise_this_reported_confidence 
from .. ext.tools import convert_globalseq_to_seqs 
# -----------------------------------------------------------
# module variables requiring initialisation before module use
# -----------------------------------------------------------

screen                = None
first_severity        = None
number_of_trials      = None


# -------------------------
# module-specific constants
# -------------------------

# These are constants used throughout the module, which are not required
# elsewhere, and are unlikely to require any adjustments, so there is little
# need to include them in the main CONFIG.py file

MedicImage_filename = os.path.join( RESOURCES_PATH, 'medic.png' )
Avatar_filenames    = os.listdir( os.path.join( RESOURCES_PATH, 'Avatars', AVATAR_ICONS_SET, 'png' ) )
Avatar_filenames    = [ os.path.join( RESOURCES_PATH, 'Avatars', AVATAR_ICONS_SET, 'png', Filename ) for Filename in sorted( Avatar_filenames ) ]

MedicImage_pgsurface = pygame.image.load( MedicImage_filename )
MedicImage_pgsurface = pygame.transform.scale( MedicImage_pgsurface, (16, 16) )
Avatar_pgsurfaces    = [ pygame.image.load( Filename ) for Filename in Avatar_filenames ]

FONT              = 'ubuntumono'   # previously: Arial
BACKGROUND_COLOUR = GRAY

SHOW_PYGAME = PLAYER_TYPE == 'human' or SHOW_PYGAME_IF_NONHUMAN_PLAYER


####################
### Module functions
####################

def set_window_title( Title ):
    if SHOW_PYGAME:   pygame.display.set_caption( Title )
    else          :   pass




def hide_mouse_cursor():
    if SHOW_PYGAME:   pygame.mouse.set_visible( False )
    else          :   pass



def init_pygame_display( Resolution : { tuple, str },
                         Fullscreen : bool           = False ):

    if SHOW_PYGAME:
        global screen

        if Resolution == 'Autodetect':   Resolution = (0, 0)  # (0,0) causes pygame to autodetect the screen size

        screen = pygame.display.set_mode( Resolution )   # Note: In general, there are two ways to enforce fullscreen mode.
                                                         # One is to pass the pygame.FULLSCREEN flag at the point when
                                                         # pygame.display.set_mode is called. The other is as it was done
                                                         # here, i.e. leaving the default flag, and toggling fullscreen mode
                                                         # afterwards. In principle the two methods are identical; however,
                                                         # the second has the 'advantage' that it will work even if the
                                                         # display specified is impossible for the actual monitor resolution
                                                         # used, whereas the pygame.FULLSCREEN flag will fail with an error
                                                         # if the requested size is not compatible with the detected
                                                         # resolutions available. Therefore, given the unusual size selected
                                                         # here, the toggle mode is preferred. (whereas this was not the
                                                         # case in the autodetection scenario).

        if Fullscreen:   pygame.display.toggle_fullscreen()

      # Write selected screen resolution to log
        width  = pygame.display.Info().current_w
        height = pygame.display.Info().current_h

        log_utils.tee( f"pygameMediator: Resolution set to: {width}x{height}" )

    else:
        pass   # invisible, non-human player, disabling pygame functions




def reset_screen( reset_margins = True ):
    """
    Fills the active pygame (fullscreen) 'window' with a background color.
    """
    if SHOW_PYGAME:
        assert screen    is not None

        screen.fill( BACKGROUND_COLOUR )

    else:
        pass    # invisible, non-human player, disabling pygame functions



def load_image():
    """
    Creates two lists:
    - A list of 'images' (where an image is a tuple containing a pygame.surface and a pygame.rect)
    - A list of 'coordinates' corresponding to where each image should be placed to achieve proper scaling

    NOTE: The return value is called 'image' but this is in fact a list of images.
    NOTE: This function does not actually cause pygame to 'load' anything on the display
    """

    img_filenames = chain_ops(
        os.path.join( RESOURCES_PATH, 'bg_image', '*.png' )
        , glob.glob
        , sorted
    )


    if SHOW_PYGAME:
        reset_screen()

        image      = []   # This will hold all map images (as pygame.Surface objects)
        coordinate = []   # This will hold 25 coordinate-pairs per map image, representing pre-defined coordinates
                          # corresponding to possible city locations.

        for i, img_name in enumerate( img_filenames ):

            img = pygame.image.load( img_name )

          # Scale image to fit the screen, maintaining the aspect ratio
            rect       = img.get_rect()
            ratio      = float( rect.width ) / rect.height   # Original image's aspect ratio
            new_height = screen.get_height()                 # Set new image height to screen height.
            new_width  = int( ratio * new_height )           # Tweak new image width so as to preserve original ratio
            ratioX     = float( new_width  / rect.width )    # The original's width has been 'rescaled' by this amount
            ratioY     = float( new_height / rect.height )   # The original's height has been 'rescaled' by this amount

          # Obtain from corresponding file coordinates for the current map
            CurrentCoordinates_file = os.path.join(
                                          RESOURCES_PATH,
                                          'bg_image',
                                          f"coordinates_{i}.txt"
                                      )

            coor     = numpy.loadtxt( CurrentCoordinates_file )
            new_coor = copy.copy( coor )

          # Transform from 'original' to 'rescaled' coordinates
            new_coor[ :, 0 ] = [int( x * ratioX ) for x in coor[ :, 0 ]]
            new_coor[ :, 1 ] = [int( y * ratioY ) for y in coor[ :, 1 ]]

          # Transform (rescale) the original image itself to the new size
            img  = pygame.transform.scale( img, (new_width, new_height) )
            rect = img.get_rect()

          # Move the image in the middle of the screen
            rect.x += (screen.get_width() - rect.width) / 2

          # Update image and coordinate lists with current map image and coordinates
            image.append( (img, rect) )
            coordinate.append( new_coor )


    else:

      # XXX: Note, these are completely garbage values, but still semi-initialized so that they don't cause more errors
      # down the line.

        image      = None
        coordinate = []   # This will hold 25 coordinate-pairs per map image, representing pre-defined coordinates
                          # corresponding to possible city locations.

        for i, img_name in enumerate( img_filenames ):

          # Obtain from corresponding file coordinates for the current map
            CurrentCoordinates_file = os.path.join(
                                          RESOURCES_PATH,
                                          'bg_image',
                                          f"coordinates_{i}.txt"
                                      )

            coor     = numpy.loadtxt( CurrentCoordinates_file )
            new_coor = copy.copy( coor )

          # Update image and coordinate lists with current map image and coordinates
            coordinate.append( new_coor )


    return image, coordinate




def get_age_from_user() -> str :
    """
    Effectively a wrapper of get_user_input, asking specifically about age.
    """
    if PLAYER_TYPE == 'human':
        return get_user_input(
                   "Please type your age and press enter:",
                   str.isdigit   # validation function
               )
    else:
        return int( numpy.random.rand( 1 ) * 100 )




def get_gender_from_user() -> str :
    """
    Effectively a wrapper of get_user_input, asking specifically about gender.
    """
    if PLAYER_TYPE == 'human':
        return get_user_input(
                   "Please specify your (biological) gender (M/F) and press enter:",
                   lambda x: x in ['M', 'F']   # validation function
               )
    else:
        return numpy.random.choice( ['M', 'F'] )




def get_handedness_from_user() -> str :
    """
    Effectively a wrapper of get_user_input, asking specifically about handedness.
    """
    if PLAYER_TYPE == 'human':
        return get_user_input(
                   "Please specify if you are left-handed or right-handed (L/R)",
                   lambda x: x in ['L', 'R']   # validation function
               )
    else:
        return numpy.random.choice( ['L', 'R'] )




def show_before_and_after_map( Severities_before, Severities_after ):
    """
    Shows a screen containing a 'before' (i.e. an individual's theoretical severities resulting from their allocations),
    and an 'after' map (i.e. severities resulting from the aggregate allocation).

    For now, this is not shown on an actual 'map' but as a separate screen, just as a quick prototype.
    """

    if SHOW_PYGAME:

        global screen
        reset_screen()

        FontSize = 32

      # Create a 'before and after' title on the top of the screen
        TitleLabel_topline      = f"City outcomes before"
        TitleLabel_bottomline   = f"and after group decision"

        MyFont                  = pygame.font.SysFont( FONT, FontSize )

        PGTitleLabel_topline    = MyFont.render( TitleLabel_topline   , True, WHITE )
        PGTitleLabel_bottomline = MyFont.render( TitleLabel_bottomline, True, WHITE )

        XCoord_topline    = screen.get_size()[ 0 ] / 2 - MyFont.size( TitleLabel_topline    )[ 0 ] / 2
        XCoord_bottomline = screen.get_size()[ 0 ] / 2 - MyFont.size( TitleLabel_bottomline )[ 0 ] / 2

        YCoord_topline    = 10
        YCoord_bottomline = 10 + MyFont.size( TitleLabel_topline )[ 1 ]

        screen.blit( PGTitleLabel_topline   , (XCoord_topline   , YCoord_topline   ) )
        screen.blit( PGTitleLabel_bottomline, (XCoord_bottomline, YCoord_bottomline) )

      # Return copies of severity arrays
        Severities_before = Severities_before.copy()
        Severities_after  = Severities_after.copy()


        # -------------------------
        # Draw the 'you' severities
        # -------------------------

      # Create the 'you' row of city severities
        XCoord = 25   # Lovely MAGIC NUMBERS
        YCoord = 200

      # Draw Avatar (with optional textlabel for current player)
        MyFont         = pygame.font.SysFont( FONT, FontSize )
        Label          = '(You) '
        MaxLabelWidth  = MyFont.size( '(You) ' )[ 0 ]
        MaxLabelHeight = MyFont.size( '(You) ' )[ 1 ]
        PGLabel        = MyFont.render( Label, True, WHITE )   # True is for 'antialias'
        Avatar         = Avatar_pgsurfaces[ 0 ]
        AvatarWidth    = Avatar.get_size()[ 0 ]
        AvatarHeight   = Avatar.get_size()[ 1 ]
        TotalPadding   = MaxLabelWidth + AvatarWidth

        screen.blit( PGLabel, (XCoord, YCoord - MaxLabelHeight / 2) )   # XXX: MAGIC number
        screen.blit( Avatar , (XCoord + MaxLabelWidth, YCoord - AvatarHeight / 2) )   # XXX: MAGIC number

      # Draw city markers
        for i, CitySeverity in enumerate( Severities_before ):
            Offset  = 50 + i * 50
            Radius  = 20
            Colour  = exp_utils.rgb_from_severity( CitySeverity )
            draw_city_marker( screen, XCoord + TotalPadding + Offset, YCoord, Radius, Colour )


        # ---------------------------
        # Draw the 'group' severities
        # ---------------------------

      # Create the 'you' row of city severities
        XCoord = 25   # Lovely MAGIC NUMBERS
        YCoord = 300

      # Draw Group label
        MyFont         = pygame.font.SysFont( FONT, FontSize )
        Label          = 'Group:'
        PGLabel        = MyFont.render( Label, True, WHITE )   # True is for 'antialias'

        screen.blit( PGLabel, (XCoord, YCoord - MaxLabelHeight / 2) )   # XXX: MAGIC number

      # Draw city markers
        for i, CitySeverity in enumerate( Severities_after ):
            Offset  = 50 + i * 50
            Radius  = 20
            Colour  = exp_utils.rgb_from_severity( CitySeverity )
            draw_city_marker( screen, XCoord + TotalPadding + Offset, YCoord, Radius, Colour )


      # Display 'click left mouse button' message
        Label   = f"Click the left mouse button to continue"
        MyFont  = pygame.font.SysFont( FONT, FontSize )
        PGLabel = MyFont.render( Label, True, WHITE )
        XCoord  = screen.get_size()[ 0 ] / 2 - MyFont.size( Label )[ 0 ] / 2
        YCoord  = 600

        screen.blit( PGLabel, (XCoord, YCoord) )

        pygame.display.update()


      # ----------------------------------------
      # Block until left mouse button is clicked
      # ----------------------------------------

      # Restrict which event types should be placed on the event queue
        pygame.event.set_blocked( None )
        pygame.event.set_allowed( [pygame.MOUSEBUTTONDOWN] )

        pygame.event.clear()   # clear the events queue

        LeftMouseClicked = False
        while not LeftMouseClicked:

            if pygame.event.peek():
                pass                  # proceed to process event
            else:
                pygame.event.pump()   # prevent pygame engine from freezing during un-event-ful frames
                continue

            Event = pygame.event.poll()   # Get (pop) a single event from the queue

            if Event.type not in [pygame.MOUSEBUTTONDOWN]:
                print( "ERROR: We should not have had an invalid event type creep into here ... how did we get to this?" )
                print( "Dropping to a pdb terminal" )
                #import pdb; pdb.set_trace()
                pass

            if Event.type == pygame.MOUSEBUTTONDOWN and Event.button == 1:
                LeftMouseClicked = True


        pygame.event.set_allowed( None )   # remove restrictions to event types.


    else:
        pass   # invisible, non-human player; disable pygame functions.






def show_message_and_wait( text, colour = YELLOW, wait = True, FontSize = 32 ):
    """
    Show a message and wait for the left mouse button.
    If ESC is pressed, return an exit code, to be processed externally.
    """

    if SHOW_PYGAME:
        reset_screen()

        MyFont        = pygame.font.SysFont( FONT, FontSize )
        FontHeight    = MyFont.size('|')[1]
        Sentences     = text.split( "\n" )
        NumSentences  = len( Sentences )
        TextboxHeight = NumSentences * FontHeight
        TextboxYCoord = (screen.get_height() - TextboxHeight) / 2

        for i in range( NumSentences ):

            PGLabel  = MyFont.render( Sentences[i], 1, colour )
            x_coord  = (screen.get_width() - MyFont.size( Sentences[i] )[ 0 ]) / 2
            y_coord  = TextboxYCoord + i * FontHeight

            screen.blit( PGLabel, (x_coord, y_coord) )

        pygame.display.flip()   # updates contents of entire (pygame) display

    else:
        pass   # invisible, non-human player; disable pygame functions.


    if wait and PLAYER_TYPE == 'human':
        log_utils.tee( 'pygameMediator: Waiting for player to proceed ... ', end = '', flush = True )

        pygame.event.set_blocked( None )
        pygame.event.set_allowed( [pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN] )
        pygame.event.clear()   # clear the events queue

        LeftMouseOrESCPressed = False
        while not LeftMouseOrESCPressed:

            if pygame.event.peek():
                pass                  # proceed to process event
            else:
                pygame.event.pump()   # prevent pygame engine from freezing during un-event-ful frames
                continue

            Event = pygame.event.poll()   # Get (pop) a single event from the queue

            if Event.type not in [pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN]:
                #print( "ERROR: We should not have had an invalid event type creep into here ... how did we get to this?" )
                #print( "Dropping to a pdb terminal" )
                #import pdb; pdb.set_trace()
                pass

            if Event.type == pygame.MOUSEBUTTONDOWN and Event.button == 1:
                LeftMouseOrESCPressed = True
                ExitGame = False
                break

            if Event.type == pygame.KEYDOWN and Event.key == 27:
                LeftMouseOrESCPressed = True
                ExitGame = True
                break


        pygame.event.set_allowed( None )   # remove restrictions to event types.

        log_utils.tee( f'{ANSI.GREEN}[{ANSI.RESET}Done{ANSI.GREEN}]{ANSI.RESET}' )

        if ExitGame:
            log_utils.tee( f"{ANSI.RED}Received 'ExitGame' event. Gracefully exiting ... {ANSI.RESET}" )
            return True

    else:
        if (LOBBY_PLAYERS > 1 or PLAYER_TYPE == 'human' or SHOW_PYGAME_IF_NONHUMAN_PLAYER) and (AGENT_WAIT): pygame.time.wait(3000)   # @FIXME: This is what is being shown when the AI is playing...





def draw_city_marker( PygameSurface, X_coord, Y_coord, Radius, Colour ):

      # Create a nice 'outline'.
      # Note: the final 0 specifies that the circle should be color-filled
        pygame.draw.circle( PygameSurface, BLACK , (X_coord, Y_coord), Radius + 1, 0 )

      # Overlay the marker on top of the 'outline'
        pygame.draw.circle( PygameSurface, Colour, (X_coord, Y_coord), Radius    , 0 )




def show_images( img               ,   # type: (img_surface, img_rect)
                 severity          ,   # list of 'severity' values for all cities currently displayed on the map
                 resources         ,   # list of 'allocated resources' for all cities currently displayed on the map
                 no_of_cities      ,   # Number of cities currently displayed on the map
                 coordinateX       ,   # List of X-coordinates for all cities currently displayed on the map
                 coordinateY       ,   # List of Y-coordinates for all cities currently displayed on the map
                 circle_radius     ,   # Circle radius of the city markers for all cities currently displayed on the map
                 direction         ,   # list of change of severity to show for all cities (1: increase, 2: decrease)
                 show_arrow = False    # XXX
               ) -> [ (pygame.Surface, pygame.Rect) ] :
    """
    Refreshes screen with current map and city status (severity, allocated resources, etc)
    """

    if SHOW_PYGAME:
        reset_screen()

        img_surface, img_rect = img

        original_surf = copy.copy( img_surface )
        new_img       = []

        for c in range( no_of_cities ):
            X_coord = int( coordinateX[ c ] )
            Y_coord = int( coordinateY[ c ] )
            Radius  = numpy.clip( int( circle_radius[ c ] ), 5, 20 )
            Colour  = exp_utils.rgb_from_severity( severity[ c ] )

            draw_city_marker( original_surf, X_coord, Y_coord, Radius, Colour )


        for c in range( no_of_cities - 1 ):   # update situation in all cities except the one that is currently being annotated

            X = int( coordinateX  [ c ] )
            Y = int( coordinateY  [ c ] )
            R = int( circle_radius[ c ] )

            if show_arrow and direction[ c ] == 1:    # downward direction (improvement of severity)
                up_arrow( original_surf, BLACK, (X, Y + R), (X, Y - R) )

            elif show_arrow and direction[ c ] == 2:    # upward direction (increase in severity)
                down_arrow( original_surf, BLACK, (X, Y - R), (X, Y + R) )


      # Show resources
        res_font = pygame.font.SysFont( FONT, 20 )

        screen.blit( original_surf, img_rect )


      # Draw colorbar
        nColors   = len( COLORS )   # This will dictate how many discrete color-rectangles make up the full colorbar
        bar_width = 50

        bar_pos_top  = ( 3/4 * img_rect.h                                # XXX Shouldn't it be 1/4 for the 'top' edge?
                         + (img_surface.get_height() - img_rect.h) / 2   # XXX Isn't this always zero??
                       )

        bar_pos_left = img_surface.get_width() - bar_width * 1.25   # XXX This places the bar slightly to the left of the
                                                                    # image's right edge



        max_bar = screen.get_height() - 2 * bar_pos_top   # Total height of the whole colorbar, such that it appears centred
                                                          # for the given 'top_position'. Note that this is given as a
                                                          # negative value. (also the calculation only works because
                                                          # img_surface height should always be equal to screen height at
                                                          # this point --- i.e. if image height == screen height == 4h, then
                                                          # top_pos == 3h, and therefore max_bar == -2h).

        bars = max_bar / nColors   # (negative) height of each discrete colour rectangle in the colorbar
                                   # Note: original code: 'max_bar / 11'

        Colorbar_rect = pygame.Rect(  bar_pos_left,  int( bar_pos_top ),  bar_width,  max_bar  )

        pygame.draw.rect( original_surf, BLACK, Colorbar_rect )


        for c in range( nColors ):   # Original code: 'range(10)'. XXX Why not 11? (i.e. why was red excluded?)

            Colour      = COLORS[ c ]
            SubRect_top = int( bar_pos_top + (bars * c) )
            Rect        =  pygame.Rect( bar_pos_left, SubRect_top, bar_width, bars )

            pygame.draw.rect( original_surf, Colour, Rect )


        screen.blit( original_surf, img_rect )

        my_font  = pygame.font.SysFont( FONT, 24 )
        res_font = pygame.font.SysFont( FONT, 18 )


      # Show resources allocated
        for c in range( no_of_cities ):

            X = int( coordinateX[ c ] )
            Y = int( coordinateY[ c ] )

          # XXX Correction for non-standard resolutions (see ticket:009)
            X += img_rect.x

            Resources_str = str( resources[ c ] )


            if resources[ c ] > 0:

                label = res_font.render( Resources_str, 1, BLACK )

                screen.blit( MedicImage_pgsurface, (X + 15, Y - 15) )
                screen.blit( label  , (X + 16, Y     ) )


        label = my_font.render( "Low", 1, BLACK )

      # XXX Correction for non-standard resolutions (see ticket:009)
        CorrectedBarPosLeft = bar_pos_left + img_rect.x

        screen.blit( label, (CorrectedBarPosLeft, bar_pos_top - my_font.size( "Low" )[ 1 ]) )

        pygame.display.update()
        pygame.event.pump()
        pygame.display.flip()

        new_img.append( (screen, screen.get_rect()) )   # XXX Note: this line is not in the context of a for loop etc,
                                                        # therefore it effectively acts as an assignment.

        return new_img   # new_img is a list with a single element, of type '(pygame.Surface, pygame.Rect) tuple'
                         # XXX Why does a new_img need to be returned in the first place, if it has been drawn already?
                         # XXX Why does surface.get_rect() need to be returned separately from its parent surface?

    else:
        pass   # invisible, non-human player, disabling pygame functions
        return None



def up_arrow( screen : pygame.surface,
              color  : (int, int, int),
              start  : (int, int),       # x,y pixel coordinates (column,row to be more precise)
              end    : (int, int)
            ):
    """
    Draws an arrow on a pygame surface.

    In theory the direction is determined by the orientation of the 'start' and 'end' coordinates; in practice, the
    start and end coordinates passed to this function from elsewhere in the module are always such that start_x = end_x,
    and start_y > end_y, and therefore this function always results in an 'upwards' pointing arrow.

    NOTE: The coordinate system is such that larger y's correspond to lower positions on screen (with the [0,0] the
    origin defined as the top left corner )
    """

    pygame.draw.line( screen, color, start, end, 2 )

    rotation = math.degrees( math.atan2( start[ 1 ] - end[ 1 ], end[ 0 ] - start[ 0 ] ) ) + 150
    # NOTE: In practice this will always result in 240 degrees given the way it is called in the module

    pygame.draw.polygon( screen,
                         BLACK,
                         ((end[ 0 ] + 10 * math.sin( math.radians( rotation       ) ), end[ 1 ] + 10 - 10 * math.cos( math.radians( rotation       ) )),
                          (end[ 0 ] + 10 * math.sin( math.radians( rotation - 120 ) ), end[ 1 ] + 10 - 10 * math.cos( math.radians( rotation - 120 ) )),
                          (end[ 0 ] + 10 * math.sin( math.radians( rotation + 120 ) ), end[ 1 ] + 10 - 10 * math.cos( math.radians( rotation + 120 ) ))
                         )
                       )




def down_arrow( screen : pygame.surface,
                color  : (int, int, int),
                start  : (int, int),       # x,y pixel coordinates (column,row to be more precise)
                end    : (int, int)
              ):
    """
    Draws an arrow on a pygame surface.

    In theory the direction is determined by the orientation of the 'start' and 'end' coordinates; in practice, the
    start and end coordinates passed to this function from elsewhere in the module are always such that start_x = end_x,
    and start_y < end_y, and therefore this function always results in an 'downwards' pointing arrow.

    NOTE: The coordinate system is such that larger y's correspond to lower positions on screen (with the [0,0] the
    origin defined as the top left corner )
    """

    pygame.draw.line( screen, color, start, end, 2 )

    rotation = math.degrees( math.atan2( start[ 1 ] - end[ 1 ], end[ 0 ] - start[ 0 ] ) ) + 90
  # NOTE: In practice this will always result in 0 degrees given the way it is called in the module

    pygame.draw.polygon( screen,
                         BLACK,
                         ((end[ 0 ] + 10 * math.sin( math.radians( rotation       ) ), end[ 1 ] - 10 + 10 * math.cos( math.radians( rotation       ) )),
                          (end[ 0 ] + 10 * math.sin( math.radians( rotation - 120 ) ), end[ 1 ] - 10 + 10 * math.cos( math.radians( rotation - 120 ) )),
                          (end[ 0 ] + 10 * math.sin( math.radians( rotation + 120 ) ), end[ 1 ] - 10 + 10 * math.cos( math.radians( rotation + 120 ) ))
                         )
                       )




def provide_response( img,
                      resources,
                      resources_left,
                      coordinate,
                      circle_radius,
                      session_no    = 0,
                      sequence_no   = -1,
                      trial_no      = -1,
                      image         = None
                    ):

    try:
        if image is None:   image = img[ 0 ]
    except TypeError:
        print( 'Bypassing image checks due to SHOW_PYGAME_IF_NONHUMAN_PLAYER config option' )

    if   PLAYER_TYPE == 'ai'            :   return provide_agent_response     ( img, resources, resources_left, coordinate, circle_radius, session_no,sequence_no, trial_no, False )
    elif PLAYER_TYPE == 'humanised_ai'  :   return provide_agent_response     ( img, resources, resources_left, coordinate, circle_radius, session_no, sequence_no, trial_no, True )
    elif PLAYER_TYPE == 'RL-Agent'      :   return provide_rl_agent_response  ( img, resources, resources_left, coordinate, circle_radius, session_no,sequence_no, trial_no )
    elif PLAYER_TYPE == 'playback'      :   return provide_replay_response    ( img, resources, resources_left, coordinate, circle_radius, session_no, sequence_no, trial_no, PLAYBACK_ID )
    elif PLAYER_TYPE == 'human'         :   return provide_user_response      ( img, resources, resources_left, coordinate, circle_radius, image )
    else:
        raise ValueError( f'Invalid PLAYER_TYPE value provided: {PLAYER_TYPE}' )




def provide_replay_response(img,
                         resources,
                         resources_left,
                         coordinate,
                         circle_radius,
                         session_no,
                         sequence_no,
                         trial_no,
                         SubjectId
                         ):

    assert number_of_trials is not None
    assert isinstance( SubjectId, str ) and len( SubjectId ) >= 3

    SequenceLengthsCsv = os.path.join( INPUTS_PATH, SEQ_LENGTHS_FILE)
    sequence_length = numpy.loadtxt( SequenceLengthsCsv , delimiter=',')

    Responses_filename = os.path.join(
        OUTPUTS_PATH,
        f'{OUTPUT_FILE_PREFIX}responses_{ SubjectId }.txt'
    )

  # Verify playback file exists, otherwise gracefully abort.
    try:
        temp = numpy.loadtxt( Responses_filename, delimiter=',', skiprows=1)

    except OSError as E:

        if E.args[0].endswith('not found.'):
            log_utils.tee( f"{ANSI.RED}ERROR: No corresponding 'responses' file found for ID specified for playback! Aborting experiment ...{ANSI.RESET}" )
            sys.exit(1)
        else:
            raise


    n_trials =  int( sum( sum( number_of_trials ) ) )
    stimuli = numpy.zeros((n_trials))                ## These are the initial stimulus, exactly.
    response = numpy.zeros((n_trials))
    reported_confidence = numpy.zeros( (n_trials))
    hold_rts = numpy.zeros(( n_trials))
    release_rts = numpy.zeros((n_trials))

    stimuli = temp[:,0]
    response = temp[:, 1]
    reported_confidence = numpy.clip(temp[:, 2], .0, 1.0)  ## 0-1 real
    hold_rts = temp[:, 3]                               ## When they press the button ms
    release_rts = temp[:, 4]                            ## When they release the button ms

    response_in_series = convert_globalseq_to_seqs(sequence_length, response)
    reported_confidence_in_series = convert_globalseq_to_seqs(sequence_length, reported_confidence)
    hold_rts_in_series = convert_globalseq_to_seqs(sequence_length, hold_rts)
    release_rts_in_series = convert_globalseq_to_seqs(sequence_length, release_rts)

    resp       = response_in_series            [ session_no * NUM_SEQUENCES + sequence_no ][ trial_no ]
    rt_hold    = hold_rts_in_series            [ session_no * NUM_SEQUENCES + sequence_no ][ trial_no ]
    rt_release = release_rts_in_series         [ session_no * NUM_SEQUENCES + sequence_no ][ trial_no ]
    confidence = reported_confidence_in_series [ session_no * NUM_SEQUENCES + sequence_no ][ trial_no ]

    resp = numpy.clip(resp, 0, resources_left) 

    if LOBBY_PLAYERS > 1 or PLAYER_TYPE == 'human' or SHOW_PYGAME_IF_NONHUMAN_PLAYER:   pygame.time.wait(int(1000 * rt_release))

    movement = []

    log_utils.tee( 'Response:', resp )

    return confidence, resp, rt_hold, rt_release, movement




def entropy(x, bins=None):
    '''
    Returns the entropy of the empiricial distribution of x
    '''

    N = x.shape

    if bins is None:   counts = numpy.bincount( x )
    else           :   counts = numpy.histogram( x, bins = bins )[ 0 ]   # Counts, probs

    p = counts[ numpy.nonzero( counts ) ] / N    # log(0)
    H = -numpy.dot( p, numpy.log2( p ) )

    return H




def calculate_agent_response_and_confidence(model, city_severity, trial_no, resource_remaining):
    repl = 1000
    M_entropy = entropy(numpy.linspace(MIN_ALLOCATABLE_RESOURCES,MAX_ALLOCATABLE_RESOURCES, repl), bins=MAX_ALLOCATABLE_RESOURCES-MIN_ALLOCATABLE_RESOURCES+1)
    m_entropy = entropy(numpy.ones((repl,)), bins=MAX_ALLOCATABLE_RESOURCES-MIN_ALLOCATABLE_RESOURCES+1)
    allocated_resources = numpy.asarray([])
    for i in range(0,repl):
        r_remaining = resource_remaining + numpy.random.normal(MIN_ALLOCATABLE_RESOURCES,MAX_ALLOCATABLE_RESOURCES,1)[0]
        c_severity = city_severity +  numpy.random.normal( 0,3,1)[0]
        t_no = trial_no + numpy.random.normal(0,3,1)[0]
        resp = model( tf.Variable(c_severity, dtype=tf.float32), tf.Variable(t_no, dtype=tf.float32), tf.Variable(r_remaining, dtype=tf.float32) )
        allocated_resources = numpy.append( allocated_resources, resp.numpy())

    resp = allocated_resources.mean()
    entrp = entropy(allocated_resources, bins=MAX_ALLOCATABLE_RESOURCES-MIN_ALLOCATABLE_RESOURCES+1)
    confidence = (1./(m_entropy-M_entropy)) * (entrp - M_entropy)

    return confidence, resp




def calculate_agent_response_and_confidence_alternative(model, city_severity, trial_no, resource_remaining):

    r_remaining = resource_remaining
    t_no = trial_no
    c_severity = city_severity

    action = model( tf.Variable(c_severity, dtype=tf.float32), tf.Variable(t_no, dtype=tf.float32), tf.Variable(r_remaining, dtype=tf.float32) )

    response, confidence, rt_hold, rt_release = agent_meta_cognitive(action, MAX_ALLOCATABLE_RESOURCES+1, resource_remaining,RESPONSE_TIMEOUT)


    return confidence, response, rt_hold, rt_release




def rl_agent_meta_cognitive(options, resources_left, response_timeout):

    def entropy_from_pdf(pdf):
        pdf = pdf + numpy.abs(numpy.min( pdf ))
        p =  pdf / numpy.sum(pdf)  # log(0)
        p[ p==0 ] += 0.000001
        print( p )
        H = -numpy.dot( p, numpy.log2( p ) )
        return H


  # Min entropy from a univalue distribution (0)
    m_entropy = numpy.zeros((11,),)
    m_entropy[0] = 1

  # Max entropy from a uniform distribution (3.55....)
    M_entropy = numpy.ones((11,),)

  # Options are the available choices from the Q Table
    log_utils.tee( 'Options:', options )

    entrp1 = entropy_from_pdf(options)

    o = [i for i in range(len(options))]
    o = numpy.asarray(o, dtype=numpy.float32)

    options[o>resources_left] = 0.00001

    log_utils.tee( 'Agent Feasible Options:', options)

  # available resources, trial, severity
    dec_entropy = entropy_from_pdf(options)
    M_entropy = entropy_from_pdf(M_entropy)
    m_entropy = entropy_from_pdf(m_entropy)

    confidence = (1./(m_entropy-M_entropy)) * (dec_entropy - M_entropy)

    response = numpy.argmax(options)

    map_to_response_time = lambda x: x * (-2) + 1

    mu, sigma = int(map_to_response_time(confidence) * 10), 3

    rt_hold = numpy.random.normal(mu, sigma, 1)[0]
    rt_release = rt_hold + numpy.random.normal(mu, 1, 1)[0]

    rt_hold = numpy.clip( rt_hold, 0, response_timeout/1000.0)
    rt_release = numpy.clip( rt_release, 0, response_timeout/1000.0)

    return response, confidence, rt_hold, rt_release




def provide_rl_agent_response( img,
                         resources,
                         resources_left,
                         coordinate,
                         circle_radius,
                         session_no,
                         sequence_no,
                         trial_no,
                         ):

    assert first_severity is not None, \
           "The 'first_severity' module-global variable needs to be set by caller before calling this function"

    Q = numpy.load(os.path.join( INPUTS_PATH,'q.npy'))
    rewards = numpy.load(os.path.join( INPUTS_PATH,'rewards.npy'))

    if VERBOSE:
        printinfo( "Reading preloaded Q-Table for RL-Agent" )

    resources_remaining = tf.Variable(resources_left, dtype=tf.float32)

    if VERBOSE:
        printinfo( 'Resources remaining...' )
        printcolor( resources_remaining, ANSI.ORANGE )
        print()

    SequenceLengthsCsv = os.path.join( INPUTS_PATH, SEQ_LENGTHS_FILE )
    sequence_length = numpy.loadtxt( SequenceLengthsCsv , delimiter=',')
    sevs = convert_globalseq_to_seqs(sequence_length, first_severity)

    sever = sevs[ session_no * NUM_SEQUENCES + sequence_no ][ trial_no ]
    city_number = trial_no

    print( resources_left )
    print( city_number )
    print( sever )
  # Calculate the response and confidence feeding the NN with noisy inputs, getting the mean and entropy from the responses.
    resp, confidence, rt_hold, rt_release = rl_agent_meta_cognitive(Q[int(resources_left), int(city_number),int(sever)],resources_left,RESPONSE_TIMEOUT)

    if ( (LOBBY_PLAYERS > 1 or PLAYER_TYPE == 'human' or SHOW_PYGAME_IF_NONHUMAN_PLAYER) and AGENT_WAIT): pygame.time.wait( int(rt_release) * 1000)

    movement = []

    return confidence, resp, rt_hold, rt_release, movement




def provide_agent_response( img,
                         resources,
                         resources_left,
                         coordinate,
                         circle_radius,
                         session_no,
                         sequence_no,
                         trial_no,
                         humanise
                          ):

    assert first_severity is not None, \
           "The 'first_severity' module-global variable needs to be set by caller before calling this function"

    model = Agent.Model([4, 4], 10)
    model.load()

    if VERBOSE:
        printinfo( "Model parameters: " )
        for m in model.Ws:
            printcolor( m, ANSI.ORANGE )
        print()

    resources_remaining = tf.Variable(resources_left, dtype=tf.float32)

    if VERBOSE:
        printinfo( 'Resources remaining...' )
        printcolor( resources_remaining, ANSI.ORANGE )
        print()

    SequenceLengthsCsv = os.path.join( INPUTS_PATH, SEQ_LENGTHS_FILE )
    sequence_length = numpy.loadtxt( SequenceLengthsCsv , delimiter=',')
    sevs = convert_globalseq_to_seqs(sequence_length, first_severity)
    
    # Latest version of TF are strict in terms of using only tensors as inputs.
    t_sevs = tf.Variable( sevs[ session_no * NUM_SEQUENCES + sequence_no ][ trial_no ], dtype=tf.float32)
    t_trial_no = tf.Variable( trial_no, dtype=tf.float32 )
    
    resp = model( t_sevs, t_trial_no, resources_remaining ).numpy()

  # Calculate the response and confidence feeding the NN with noisy inputs, getting the mean and entropy from the responses.
    confidence, resp, rt_hold, rt_release = calculate_agent_response_and_confidence_alternative(model, sevs[ session_no * NUM_SEQUENCES + sequence_no ][ trial_no ], trial_no, resources_left)

    print( "DEBUG: rt_release = ", rt_release )         # typically between 0 and 10
    DelayModifier = 0.5
    if ((LOBBY_PLAYERS > 1 or PLAYER_TYPE == 'human' or SHOW_PYGAME_IF_NONHUMAN_PLAYER) and AGENT_WAIT): pygame.time.wait( int(rt_release) * int(1000 * DelayModifier) + 5000 )   # 5000 corresponds to the 5 seconds added to the human for confidence timeout

    movement = []

    # What 'humanise' mean for us ?  Picking a random number at the beggining and stick to the optimal value at the end.
    if (humanise):
        g_seq_no = session_no * NUM_SEQUENCES + sequence_no + 1 
        decay = boltzmann_decay ( g_seq_no )

        right_response = resp 
        # The decay function is a negative exponential that starts slowly close to 0, grow monotonically until it arrives 0.9 around the sequence 63.
        # So at the end, the random number between 0..1 should be greater that 0.9 to force a random (and silly) response from the NN.
        resp = adjust_response_decay( resp, decay, resources_left) 

        # Experiment 3f: Humanizing AI
        #confidence = numpy.asarray ( [confidence] )
        #confidence = humanise_this_reported_confidence( confidence )

        # Alternative 2: pick the reported confidence based on what subjects have reported for this given response.
        #confidence = pick_human_reported_confidence( resp )

        # Alternative 3: pick the difference between the right-value vs the noisy response.
        distance = numpy.clip( numpy.abs(right_response - resp), 0, 10)
        distance = -distance
        confidence = (distance - (-(3.0))) / (3.0)

        # Remap the differences in the responses to confidences, using the range [0,3]
        confidence = numpy.clip( confidence, 0.0, 1.0)

        printinfo (f'------------------------------> RESPONSE: {resp}({right_response})')
        printinfo (f'------------------------------> CONFIDENCE: {confidence}')

        # Now clip the response value up to 3 in difference.  This will avoid very big mistakes from the NN.
        if (numpy.abs(resp - right_response) > 3):
            resp = right_response - 3
            resp = numpy.clip( resp,0, resources_left)

        if (confidence == 0):
            confidence = get_random_confidence(3)
            confidence = numpy.clip( confidence, 0.0, 1.0)

        if (resp == 0):
            confidence = -1.0
        # The response needs to be an integer number.
        resp = round(resp)

    return confidence, resp, rt_hold, rt_release, movement




def provide_user_response( img,   # list of (surface, rect) tuples - XXX is this always (a : pygame.Surface, a.get_rect()) ??
                           resources,
                           resources_left,
                           coordinate,
                           circle_radius,
                           image = None   # needed for 'ugly hack' below
                         ):
    """
    This function processes events relating to the participant's response, and updates the pygame display accordingly
    (i.e. by drawing the allocated resources to the city in question)
    """

    if image is None: image = img[0]   # XXX These variables are all declared global, but not used outside this
                                       # function. Why? Is there a reason they need to be persistent between calls? XXX
                                       # If no response is given in a trial, the previous allocation is repeated (I
                                       # think). Is this intentional?
    global resp, rt_hold, rt_release


  # Log all the mouse movements from mouse click to mouse release
    img_surface, img_rect = img[ 0 ]   # Note: 'img' is always a list of a single element, as returned from
                                       # 'show_image'

    CurrentCityCoords     = coordinate[ -1 ]

    movement              = []   # to hold list of coordinate pairs corresponding to mouse movements

    nColors      = len( COLORS )   # Note: 'colors' defined at global scope
    bar_width    = 50
    bar_pos_top  = 3 * img_rect.h / 4 + (img_surface.get_height() - img_rect.h) / 2
    bar_pos_left = img_surface.get_width() - bar_width * 1.25   # XXX The calculation of `bar_pos_left` here looks
                                                                # identical to the one in show_image() ... HOWEVER,
                                                                # img_rect and img_surface are very different here,
                                                                # therefore this results in an entirely different
                                                                # colorbar location in any resolution other than the
                                                                # original resolution in the lab machines. Therefore
                                                                # different corrections are needed w.r.t. ticket:009
                                                                # (see CorrectedBarPosLeft Ugly Hack below)
    max_bar      = screen.get_height() - 2 * bar_pos_top
    bars         = max_bar / nColors

  # Create clocks and start timing
    hold_clock    = pygame.time.Clock()
    release_clock = pygame.time.Clock()
    timeout_clock = pygame.time.Clock()

    timeout       = RESPONSE_TIMEOUT       #  timeout after which the uncertainty value is collected


  # Initiate status channel
    status = 0   # I believe a status of 0 signifies "No mousebutton has been pressed yet". (XXX confirm)
    pygame.mouse.set_visible( True )   # Note: this happens instantly (not at display update)
    pygame.display.flip()

  # for debugging purposes, to compare against actual resources
    ResourcesAllocatedVisually = 0
    ActualResourcesAllocated   = 0
    FromFirstposToCurrentpos   = (0, 0, 0)   # First coord, current coord, curr-first diff
    FromFirstposToLastpos      = (0, 0, 0)   # First coord, last coord   , last-first diff

    original_surf = copy.copy( img_surface )
    MovementFrame = 0   # counter for mouse motion events; together with refresh rate, it will determine how often redraws are honoured
    RefreshRate   = MOVEMENT_REFRESH_RATE

    CurrentAllocation = 0   # for use in efficiently drawing sectors only when allocation has changed

  # Restrict which event types should be placed on the event queue
    pygame.event.set_blocked( None )
    pygame.event.set_allowed( [pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP] )

    pygame.event.clear()   # clear the events queue


    while timeout > 0 and status != 2:   # I believe a status of 2 signifies a mouse button has been released (XXX confirm)

        events = pygame.event.get()

      # Stop game from processing non-events, and 'pump' pygame.event queue appropriately
        if events: pass
        else:
            pygame.event.pump()
            timeout -= timeout_clock.tick()
            continue


        for event in events:   # XXX Note that timeout is not checked while this list of events is being consumed.
                               # (However, this is presumably inconsequential in terms of actual computing times)

            MovementFrame += 1

          # Draw Colorbar
            if not MovementFrame % RefreshRate:
                for c in range( nColors ):   # Note: Original code: 'range(10)'

                    CorrectedBarPosLeft = bar_pos_left - image[1].x   # XXX Ugly Hack for (ticket:009) relying on global
                                                                      # variable. UPDATE: with new package format, this
                                                                      # is now passed as an extra optional variable.

                    pygame.draw.rect( original_surf,
                                      COLORS[ c ],
                                      pygame.Rect( CorrectedBarPosLeft, int( bar_pos_top + (bars * c) ), bar_width, bars )
                                    )

                my_font = pygame.font.SysFont( FONT, 24 )
                label   = my_font.render( "Low", 1, BLACK )

                original_surf.blit( label, (CorrectedBarPosLeft, bar_pos_top - my_font.size( "Low" )[ 1 ]) )
                screen.blit( original_surf, img_rect )

            temp_resources = copy.copy( resources )


            if status == 0:

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

                    first_position = event.pos
                    hold_clock.tick()
                    rt_hold = hold_clock.get_time() / 1000.0
                    evmrk.responsehold()
                  # Mark that the 'HOLD event' begins -- i.e. mouse button has been pressed, but not released yet.
                    status = 1

                    resp       = 0
                  # Commenting out these lines, DOES the magic (unexpected as it may seem).  XXX ?
#                    rt_release = 0.0
#                    rt_hold    = 0.0


            elif status == 1:   # i.e. 'Mousebutton has been pressed (but not released yet)'

                temp_resources[ -1 ] = 0   # XXX The last element was -1, now it's set to 0. Why?


                if event.type == pygame.MOUSEMOTION and event.buttons[ 0 ] == 1:

                    current_position = event.pos
                    movement.append( pygame.mouse.get_pos() )


                    # XXX This bit draws an invisible black bar on the screen, whose height depends on the
                    # vertical distance from the original city coordinates. It is not clear why this exists, so
                    # I'm disabling (commenting it out) for now
#                            pygame.draw.rect( original_surf,
#                                              BLACK,
#                                              pygame.Rect( bar_pos_left, current_position[ 1 ], bar_width, img_rect.h )
#                                            )


                    temp_resources[ -1 ] = chain_ops( current_position[ 1 ] - first_position[ 1 ]
                                                      , lambda _ : _ // -20   # XXX MAGIC NUMBER (mouse sensitivity?)
                                                      , int
                                                      , lambda _ : numpy.clip( _, MIN_ALLOCATABLE_RESOURCES, MAX_ALLOCATABLE_RESOURCES )
                                                    )

                    if  temp_resources[ -1 ] > resources_left:
                        temp_resources[ -1 ] = resources_left

                  # Divide the circle into ten different sectors to increase/decrease crosses on mouse movement
                    sectors = divide_circle( circle_radius[ -1 ], CurrentCityCoords )

                    # XXX UGLY HACK to fix positioning bug (see ticket:009). This relies on accessing one of the
                    # variables defined at global scope in __main__ (i.e. image), which holds information about how much
                    # the original map was shifted relative to the screen's left border. This is necessary for monitors
                    # which differ in resolution from the one for which the experiment was originally designed,
                    # otherwise this shift would be ignored in the sector positions.

                    # NOTE: This also has to be repeated below, as this drawing event is only triggered "if
                    # movement has been detected that is below city level". (It is unclear why this distinction
                    # was useful).

                    sectors = [ (i[0] + image[1].x, i[1]) for i in sectors]

                    if CurrentAllocation != temp_resources[ -1 ]:
                        for r in range( 1, temp_resources[ -1 ] + 1 ):
                            screen.blit( MedicImage_pgsurface, sectors[ r - 1 ] )

                        pygame.display.update()   # XXX Used to be flip
                        CurrentAllocation = temp_resources[ -1 ]

                    ResourcesAllocatedVisually = temp_resources[ -1 ]   # XXX duplication, but for debugging, delete when not needed
                    FromFirstposToCurrentpos   = (first_position[ 1 ],
                                                  current_position[ 1 ],
                                                  current_position[ 1 ] - first_position[ 1 ]
                                                 )


                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:

                    release_clock.tick()

                    rt_release    = release_clock.get_time() / 1000.0
                    evmrk.responserelease()
                    status        = 2
                    last_position = event.pos


                else:
                    try:
                        last_position = current_position   # Note: Changed (previously 'CurrentCityCoordinates'). XXX I
                                                           # believe this was primarily placed here for the purpose of
                                                           # preventing an unreferenced local variable exception at the
                                                           # last minute coming from mouse movement events (i.e. rather
                                                           # than because we actually expect any events that fall in the
                                                           # broader category of "non-buttonup" events).
                    except UnboundLocalError:
                        last_position = first_position     # Catch stuff like scrollmotion before movement has occurred


                  # This is set when the mouseup event is triggered after the confidence bar appears.
                    rt_release    = 0.0


                resp = chain_ops( last_position[ 1 ] - first_position[ 1 ]
                                  , lambda _ : _ // -20   # XXX MAGIC NUMBER (mouse sensitivity?)
                                  , int
                                  , lambda _ : numpy.clip( _, MIN_ALLOCATABLE_RESOURCES, MAX_ALLOCATABLE_RESOURCES )
                                )


                if resp > resources_left:
                    resp = resources_left

                ActualResourcesAllocated = resp   # XXX duplication, but for debugging, delete when not needed
                FromFirstposToLastpos    = (first_position[ 1 ],
                                            last_position[ 1 ],
                                            last_position[ 1 ] - first_position[ 1 ]
                                           )

            elif status == 2:   break    # Stop processing further events if mouse button has been released


        timeout -= timeout_clock.tick()
    #
    ### END OF while timeout > 0 and status != 2:


    pygame.event.set_allowed( None )   # remove restrictions to event types.

    sectors = divide_circle( circle_radius[ -1 ], CurrentCityCoords )

  # XXX UGLY HACK addressing (ticket:009); see details above
    sectors = [ (i[0] + image[1].x, i[1]) for i in sectors]

  # XXX Ugly HACK addressing (ticket:016), when there are no responses
    try:
        resp
        rt_hold
        rt_release
    except NameError:
        resp = 0
        rt_hold = 0
        rt_release = 0

    if resp > 0:
        resp = int(resp)   # Next line range break if resp is not an integer
        for re in range( 1, resp + 1 ):
            screen.blit( MedicImage_pgsurface, sectors[ re - 1 ] )

    pygame.display.update()


    # Why resp is global? I don't know O).  Anyway, we need to "reset" the resp value because otherwise
    # if the subject does not respond anything, it will use the previous value.
    newresp = resp
    resp = 0

    # Note: the '-1' here is a flag, indicating that this function does not return a confidence calculation, like with
    # artificial agents. This is used elsewhere to decide whether to trigger a 'confidence' dialogue. In other words,
    # for human players, the -1 flag will later trigger an interaction that allows them to rate their confidence.
    return -1, newresp, rt_hold, rt_release, movement




def divide_circle( circle_radius : int,
                   coordinate    : numpy.ndarray   # Nx2 array
                 ) -> [ (int, int) ]:
    """
    For a given circle, obtain the coordinates for a number of points equal to the total resources that can be
    allocated, such that these points could be plotted with equal spacing along the curvature of the circle (on
    the outside)
    """

    Radius  = circle_radius + 8 - 3   # enlarge radius to account for width of image.
                                      # NOTE: XXX: MAGIC numbers:
                                      #  • 8: because MedicImage_pgsurface is rescaled to 16x16 early on
                                      #  • 3: overlap by 3 pixels, rather than place marker completely at city periphery

    Thetas = numpy.linspace( 0, 2 * numpy.pi,
                             MAX_ALLOCATABLE_RESOURCES + 1 )   # Divide circle into n+1 equal points
    Thetas = Thetas[ : -1 ]                                    # discard 2π (since this coincides with point at 0 )

    XCoords = coordinate[ 0 ] + Radius * numpy.cos( Thetas ) - 8   # Account for coordinate denoting top-left corner of image.
    YCoords = coordinate[ 1 ] + Radius * numpy.sin( Thetas ) - 8   # Note: XXX MAGIC number here too.

    Sectors = list( zip( XCoords, YCoords ) )


    return Sectors




def screen_messages( text, colour = BLACK ):
    """
    Display text strings directly on top of the current pygame display
    """

#    img_surface, img_rect = img[0]

    if SHOW_PYGAME:
        FontSize      = 32
        MyFont        = pygame.font.SysFont( FONT, FontSize )
        FontHeight    = MyFont.size('|')[1]
        Sentences     = text.split( "\n" )
        NumSentences  = len( Sentences )
        TextboxHeight = NumSentences * FontHeight
        TextboxYCoord = (screen.get_height() - TextboxHeight) * 0.9   # Position at 9/10ths of unused screenspace

        for i in range( NumSentences ):
            PGLabel  = MyFont.render( Sentences[i], 1, colour )
            x_coord  = (screen.get_width() - MyFont.size( Sentences[i] )[ 0 ]) / 2
            y_coord  = TextboxYCoord + i * FontHeight
            screen.blit( PGLabel, (x_coord, y_coord) )

        pygame.display.flip()

    else:
        pass   # invisible, non-human player, disabling pygame functions



# @DEPRECATED This is not being used (the response and the confidence is provided in one method for every mode)
def provide_confidence( img, session_no=0, sequence_no=-1, trial_no=-1 ):

    if   PLAYER_TYPE == 'ai'      :   return provide_agent_confidence  ( img, session_no, sequence_no, trial_no )
    elif PLAYER_TYPE == 'playback':   return provide_replay_confidence ( img, session_no, sequence_no, trial_no, PLAYBACK_ID )
    else                          :   return provide_user_confidence   ( img )




def provide_replay_confidence(img,
                         session_no,
                         sequence_no,
                         trial_no,
                         SubjectId
                         ):

    assert number_of_trials is not None

    SequenceLengthsCsv = os.path.join( INPUTS_PATH, SEQ_LENGTHS_FILE )
    sequence_length = numpy.loadtxt( SequenceLengthsCsv , delimiter=',')

  # @TODO Verify if the sequence/trial structure of the responses is compatible with the one for this experiment.

    Responses_filename = os.path.join(
        OUTPUTS_PATH,
        f'{OUTPUT_FILE_PREFIX}responses_{ SubjectId }.txt'
    )

    temp = numpy.loadtxt( Responses_filename, delimiter=',', skiprows=1)

    n_trials =  int( sum( sum( number_of_trials ) ) )

    stimuli = numpy.zeros((n_trials))                ## These are the initial stimulus, exactly.
    response = numpy.zeros((n_trials))
    reported_confidence = numpy.zeros( (n_trials))
    hold_rts = numpy.zeros(( n_trials))
    release_rts = numpy.zeros((n_trials))

    stimuli = temp[:,0]
    response = temp[:, 1]
    reported_confidence = numpy.clip(temp[:, 2], .0, 1.0)  ## 0-1 real
    hold_rts = temp[:, 3]                                  ## When they press the button ms
    release_rts = temp[:, 4]                               ## When they release the button ms

    response_in_series = convert_globalseq_to_seqs(sequence_length, response)
    reported_confidence_in_series = convert_globalseq_to_seqs(sequence_length, reported_confidence)
    hold_rts_in_series = convert_globalseq_to_seqs(sequence_length, hold_rts)
    release_rts_in_series = convert_globalseq_to_seqs(sequence_length, release_rts)

    resp                   = response_in_series            [ session_no * NUM_SEQUENCES + sequence_no ][ trial_no ]
    rt_hold                = hold_rts_in_series            [ session_no * NUM_SEQUENCES + sequence_no ][ trial_no ]
    rt_release             = release_rts_in_series         [ session_no * NUM_SEQUENCES + sequence_no ][ trial_no ]
    CurrentConfidenceValue = reported_confidence_in_series [ session_no * NUM_SEQUENCES + sequence_no ][ trial_no ]

    assert False, 'This method should not be called anymore.'
    return CurrentConfidenceValue




def provide_agent_confidence( img, session_no, sequence_no, trial_no ):

    CurrentConfidenceValue = numpy.random.rand( 1 )[ 0 ]
    CurrentConfidenceValue = max( 0.0, CurrentConfidenceValue )
    CurrentConfidenceValue = min( 1.0, CurrentConfidenceValue )

    return CurrentConfidenceValue




def provide_user_confidence( img ):
    """
    Ask the user to provide his/her confidence in the current decision
    """

    img_surface, img_rect = img[ 0 ]

    original_surf = copy.copy( img_surface )
    bar_height    = 50
    bar_pos_top   = screen.get_height() / 7 - bar_height
    bar_pos_left  = img_rect.w / 3 + (screen.get_width() - img_rect.w) / 2
    max_bar       = 2 * img_rect.w / 3 + (screen.get_width() - img_rect.w) / 2
    my_font       = pygame.font.SysFont( FONT, 24 )

    CurrentConfidenceValue = 0.0            # (takes values betwen 0.0 and 1.0)
    MovementFrame = 0                       # A counter that tracks mouse movement events
    RefreshRate   = MOVEMENT_REFRESH_RATE   # Only refresh screen events if this many movementframes have occurred


  # Set a timeout after which the uncertainty value is collected
    timeout       = CONFIDENCE_TIMEOUT  # In milliseconds. Defined at global scope.
    timeout_clock = pygame.time.Clock()

    timeout_clock.tick()


  # Add the background
    pygame.mouse.set_visible( True )
    screen.blit( original_surf, img_rect )

  # Starting line and "0"
    def draw_starting_line( Colour = BLACK ):
        pygame.draw.rect( screen, Colour, pygame.Rect( bar_pos_left, bar_pos_top, 3, bar_height ) )
        label = my_font.render( "0", 1, Colour )
        screen.blit( label, (bar_pos_left - my_font.size( "0" )[ 0 ] / 2, bar_pos_top - my_font.size( "0" )[ 1 ]) )

  # Ending line
    def draw_ending_line( Colour = BLACK ):
        pygame.draw.rect( screen, Colour, pygame.Rect( max_bar, bar_pos_top, 3, bar_height ) )
        label = my_font.render( "100", 1, Colour )
        screen.blit( label, (max_bar - my_font.size( "100" )[ 0 ] / 2, bar_pos_top - my_font.size( "100" )[ 1 ]) )

    draw_starting_line()
    draw_ending_line()


  # Update (full) display
    pygame.display.flip()


    if BIOSEMI_CONNECTED or FORCE_MOUSEWHEEL_SCROLL_CONFIDENCE:

        def update_confidence_bar_from_scrolling( x, Colour, Force = False ):
            nonlocal CurrentConfidenceValue
            nonlocal MovementFrame
            nonlocal RefreshRate

            if Force or not MovementFrame % RefreshRate:
                screen.blit( original_surf, img_rect )

                CurrentConfidenceValue = max( 0.0, CurrentConfidenceValue )
                CurrentConfidenceValue = min( 1.0, CurrentConfidenceValue )

                ConfidenceBarWidth = CurrentConfidenceValue * ((max_bar - 1) - (bar_pos_left + 3))

                draw_starting_line( RED if CurrentConfidenceValue == 0 else BLACK )
                draw_ending_line(   RED if CurrentConfidenceValue == 1 else BLACK )

                pygame.draw.rect( screen, Colour, pygame.Rect( bar_pos_left + 3,
                                                               bar_pos_top,
                                                               ConfidenceBarWidth,
                                                               bar_height
                                                             )
                                )

                pygame.display.update()


      # Restrict which event types should be placed on the event queue
        pygame.event.set_blocked( None )
        pygame.event.set_allowed( [ pygame.MOUSEBUTTONDOWN ] )

        pygame.event.clear()   # Clear the event queue

        while timeout > 0:

            if pygame.event.peek():
                pass                  # proceed to process event
            else:
                pygame.event.pump()   # prevent pygame engine from freezing during un-event-ful frames
                timeout -= timeout_clock.tick()
                continue


            Event = pygame.event.poll()

            if Event.type not in [ pygame.MOUSEBUTTONDOWN ]:
                #print( "ERROR: We should not have had an invalid event type creep into here ... how did we get to this?" )
                #print( "Dropping to a pdb terminal" )
                #import pdb; pdb.set_trace()
                pass


            if ( Event.type == pygame.MOUSEBUTTONDOWN and Event.button == 4 ):     # Scroll 'up'
                MovementFrame += 1
                CurrentConfidenceValue += CONFIDENCE_UPDATE_AMOUNT
                update_confidence_bar_from_scrolling( CurrentConfidenceValue, DARK_RED )

            elif ( Event.type == pygame.MOUSEBUTTONDOWN and Event.button == 5 ):   # Scroll 'down'
                MovementFrame += 1
                CurrentConfidenceValue -= CONFIDENCE_UPDATE_AMOUNT
                update_confidence_bar_from_scrolling( CurrentConfidenceValue, DARK_RED )

            else:
                pass   # Disregard any other mousebutton presses except '4' and '5'

            timeout -= timeout_clock.tick()


        update_confidence_bar_from_scrolling( CurrentConfidenceValue, DARK_GREEN, Force = True )
        pygame.event.set_allowed( None )   # remove restrictions to event types.


    else:   # Running experiment without a biosemi device.

        def is_inside_confidence_box( MouseCoords_pair ) -> bool:
            x, y = MouseCoords_pair
            return   bar_pos_left -50 <= x < max_bar + 50   and   bar_pos_top <= y < bar_pos_top + bar_height

        def update_confidence_bar_from_click( x, Colour, Force = False ):
            nonlocal CurrentConfidenceValue
            nonlocal MovementFrame
            nonlocal RefreshRate

            if Force or not MovementFrame % RefreshRate:
                screen.blit( original_surf, img_rect )
                x = numpy.clip( x, bar_pos_left + 3, max_bar - 1)
                draw_starting_line( RED if x <= bar_pos_left + 3 else BLACK )
                draw_ending_line(   RED if x >= max_bar - 1      else BLACK )
                pygame.draw.rect( screen, Colour, pygame.Rect( bar_pos_left + 3, bar_pos_top, x - (bar_pos_left + 3), bar_height ) )
                pygame.display.update()

            CurrentConfidenceValue = (x - (bar_pos_left + 3)) / ((max_bar - 1) - (bar_pos_left + 3))


        pygame.event.clear()   # Clear the event queue

        ConfidenceHasChanged = False

        while timeout > 0:

            if pygame.event.peek():
                pass                  # proceed to process event
            else:
                pygame.event.pump()   # prevent pygame engine from freezing during un-event-ful frames
                timeout -= timeout_clock.tick()
                continue


            Event = pygame.event.poll()


            if Event.type in [ pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP ]:
                pass   # allow these events only

            else:
                timeout -= timeout_clock.tick()
                continue


            if ( Event.type == pygame.MOUSEBUTTONDOWN
                 and Event.button == 1
                 and is_inside_confidence_box( Event.pos )
            ):

                update_confidence_bar_from_click( Event.pos[0], DARK_RED, Force = True )


            elif ( Event.type == pygame.MOUSEMOTION
                   and is_inside_confidence_box( Event.pos )
            ):

                if   Event.buttons[ 0 ] == 1:   # left mouse button pressed
                    MovementFrame += 1
                    update_confidence_bar_from_click( Event.pos[0], DARK_RED  )

                elif Event.buttons[ 0 ] == 0:   # left mouse button unpressed
                    MovementFrame += 1
                    update_confidence_bar_from_click( Event.pos[0], DARK_CYAN )

                else: raise IOError( "Mouse button neither 0 nor 1. In theory this shouldn't happen." )


            elif ( Event.type == pygame.MOUSEBUTTONUP
                   and Event.button == 1
                   and is_inside_confidence_box( Event.pos )
            ):

                update_confidence_bar_from_click( Event.pos[0], DARK_GREEN, Force = True )
                ConfidenceHasChanged = True


            if ConfidenceHasChanged:    break

            timeout -= timeout_clock.tick()


    CurrentConfidenceValue = round( CurrentConfidenceValue, 1 )
    CurrentConfidenceValue = max( 0.0, CurrentConfidenceValue )
    CurrentConfidenceValue = min( 1.0, CurrentConfidenceValue )

    return CurrentConfidenceValue




def show_end_of_trial_feedback( AllMessages, LastAggregatedAllocation, LastAggregatedSeverity, ResourcesLeft ):
    """
    Simple screen shown after each trial, showing what each player allocated, with what confidence, and severity impact)
    """

    if SHOW_PYGAME:

        global screen

        reset_screen()

        NumPlayers                = len( AllMessages )
        LastAllocationPerPlayer   = [ i[ -1, 0 ] for i in AllMessages ]
        LastConfidencePerPlayer   = [ i[ -1, 1 ] for i in AllMessages ]
        LastSeverityPerPlayer     = [ i[ -1, 2 ] for i in AllMessages ]
        LastCircleRadiusPerPlayer = [ i[ -1, 3 ] for i in AllMessages ]

        FontSize = 32

      # Assign appropriate colour to 'remaining resources' string (going from green to red as resources decrease)
        ResourceColour = ResourcesLeft / AVAILABLE_RESOURCES_PER_SEQUENCE
        ResourceColour = max( 0, ResourceColour )
        MaxColour      = max( ResourceColour, 1 - ResourceColour )
        ResourceColour = (int( 255 * (1 - ResourceColour) / MaxColour ), int( 255 * ResourceColour / MaxColour ), 0)

      # Place string informing of remaining resources at the top of the screen
        ResourcesType = 'shared' if exp_utils.AllocationType == 'shared' else 'not shared'
        Label_a  = f"Resources remaining ({ResourcesType}) :"
        Label_b  = f" {max(0, ResourcesLeft):.0f}"
        MyFont_a = pygame.font.SysFont( FONT, int(FontSize / 2) )
        MyFont_b = pygame.font.SysFont( FONT, int(FontSize * 2) )
        PGLabel_a = MyFont_a.render( Label_a, True, WHITE )
        PGLabel_b = MyFont_b.render( Label_b, True, ResourceColour )

        XCoord = screen.get_size()[ 0 ] / 2 - MyFont_a.size( Label_a )[ 0 ] / 2 - MyFont_b.size( Label_b )[ 0 ] / 2
        YCoord = 10 + (MyFont_b.size( Label_b )[ 1 ] - MyFont_a.size( Label_a )[ 1 ]) / 2
        screen.blit( PGLabel_a, (XCoord, YCoord) )

        XCoord = screen.get_size()[ 0 ] / 2 + MyFont_a.size( Label_a )[ 0 ] / 2 - MyFont_b.size( Label_b )[ 0 ] / 2
        YCoord = 10
        screen.blit( PGLabel_b, (XCoord, YCoord) )


      # Proceed to place city markers and related info
        for i in range( NumPlayers ):

          # XXX beautiful MAGIC numbers, that's some high quality code right here
            XCoord = 25 if i < 5 else 25 + int( screen.get_size()[ 0 ] / 2 )
            YCoord = 70 + MyFont_b.size( Label_b )[ 1 ] + (i % 5) * 135

          # Draw Avatar (with optional textlabel for current player)
            MyFont         = pygame.font.SysFont( FONT, FontSize )
            Label          = '(You) ' if i == 0 else ''
            MaxLabelWidth  = MyFont.size( '(You) ' )[ 0 ]
            MaxLabelHeight = MyFont.size( '(You) ' )[ 1 ]
            PGLabel        = MyFont.render( Label, True, WHITE )   # True is for 'antialias'
            Avatar         = Avatar_pgsurfaces[ i ]
            AvatarWidth    = Avatar.get_size()[ 0 ]
            AvatarHeight   = Avatar.get_size()[ 1 ]
            TotalPadding   = MaxLabelWidth + AvatarWidth

            screen.blit( PGLabel, (XCoord, YCoord - MaxLabelHeight / 2) )   # XXX: MAGIC number
            screen.blit( Avatar , (XCoord + MaxLabelWidth, YCoord - AvatarHeight / 2) )   # XXX: MAGIC number

          # Draw city marker
            Radius  = numpy.clip( int( LastCircleRadiusPerPlayer[ i ] ), 5, 20 )
            Colour  = exp_utils.rgb_from_severity( LastSeverityPerPlayer[ i ] )

            draw_city_marker( screen, XCoord + TotalPadding + 50, YCoord, Radius, Colour )

          # Draw allocated resources around city
            Sectors = divide_circle( LastCircleRadiusPerPlayer[ i ], (XCoord + TotalPadding + 50, YCoord) )
            Sectors = Sectors[ : int( LastAllocationPerPlayer[ i ] ) ]

            for Sector in Sectors:   screen.blit( MedicImage_pgsurface, Sector )

          # Draw confidence bar (with thin black outline and appropriate colour code, similar to Resources)
            BorderThickness     = 2
            ConfidenceBarHeight = 20
            RectXCoord          = XCoord + TotalPadding + 100
            RectYCoord          = YCoord - ConfidenceBarHeight / 2
            ConfidenceBarWidth  = screen.get_size()[ 0 ] / 2 - 25 - BorderThickness - RectXCoord if i < 5 else screen.get_size()[ 0 ] - 25 - BorderThickness - RectXCoord
            RectWidth           = ConfidenceBarWidth * LastConfidencePerPlayer[ i ]
            BGRectXCoord        = RectXCoord + ConfidenceBarWidth * LastConfidencePerPlayer[ i ]
            BGRectWidth         = ConfidenceBarWidth * (1 - LastConfidencePerPlayer[ i ])

          # Choose an appropriate colour code for the confidence bar (going from green to red as it drops from 1 to 0)
            ConfidenceColour = LastConfidencePerPlayer[ i ]
            MaxColour        = max( ConfidenceColour, 1 - ConfidenceColour )
            ConfidenceColour = (int( 255 * (1 - ConfidenceColour) / MaxColour ), int( 255 * ConfidenceColour / MaxColour ), 0)


            pygame.draw.rect( screen , BLACK,
                              pygame.Rect( RectXCoord-BorderThickness,
                                           RectYCoord-BorderThickness,
                                           ConfidenceBarWidth  + BorderThickness * 2,
                                           ConfidenceBarHeight + BorderThickness * 2 )
                            )

            if LastConfidencePerPlayer[ i ] == -1:
                pygame.draw.rect( screen , RED,
                                  pygame.Rect( RectXCoord-BorderThickness,
                                               RectYCoord-BorderThickness,
                                               ConfidenceBarWidth  + BorderThickness * 2,
                                               ConfidenceBarHeight + BorderThickness * 2 )
                                )
                pygame.draw.rect( screen, BACKGROUND_COLOUR, pygame.Rect( RectXCoord, RectYCoord, ConfidenceBarWidth, ConfidenceBarHeight ) )
            else:
                pygame.draw.rect( screen , BLACK,
                                  pygame.Rect( RectXCoord-BorderThickness,
                                               RectYCoord-BorderThickness,
                                               ConfidenceBarWidth  + BorderThickness * 2,
                                               ConfidenceBarHeight + BorderThickness * 2 )
                                )
                pygame.draw.rect( screen, ConfidenceColour , pygame.Rect( RectXCoord    , RectYCoord    , RectWidth             , ConfidenceBarHeight     ) )
                pygame.draw.rect( screen, BACKGROUND_COLOUR, pygame.Rect( BGRectXCoord  , RectYCoord    , BGRectWidth           , ConfidenceBarHeight     ) )


        c=0
        initial_ticks = pygame.time.get_ticks()
        while (True):
            pygame.draw.rect( screen, RED, pygame.Rect( 0,
                                                        10,
                                                        0+int(c/70.0),
                                                        5)
                                                        )
            c=c+1

            if (pygame.time.get_ticks() - initial_ticks > 2000):
                break

            pygame.display.update()


    else:
        pass   # invisible, non-human player; disable pygame functions.


    #if LOBBY_PLAYERS > 1 or PLAYER_TYPE == 'human' or SHOW_PYGAME_IF_NONHUMAN_PLAYER:   pygame.time.wait(2000)





def show_feedback( canvas, raw_data, text, wait = True, FontSize = 32 ):
    """
    Show feedback and wait for the left mouse button
    """

    if SHOW_PYGAME:
        reset_screen()

        MyFont     = pygame.font.SysFont( FONT, FontSize )

      # Draw graph in the middle of the available screen
        CanvasSize     = canvas.get_width_height()
        GraphImage     = pygame.image.fromstring( raw_data, CanvasSize, 'RGB' )
        CanvasPos_x = (screen.get_width()  - CanvasSize[ 0 ]) / 2
        CanvasPos_y = (screen.get_height() - CanvasSize[ 1 ]) / 2

        screen.blit( GraphImage, (CanvasPos_x, CanvasPos_y) )

      # Render 'Feedback' label
        TopLabel    = MyFont.render( "Feedback", 1, WHITE )
        TopLabelPos_x = (screen.get_width() - MyFont.size( 'Feedback' )[ 0 ]) / 2
        TopLabelPos_y = (CanvasPos_y - MyFont.size( "Feedback" )[ 1 ]) / 2

        screen.blit( TopLabel, (TopLabelPos_x, TopLabelPos_y ) )
        pygame.display.flip()

        if wait:

            Sentences     = text.split( "\n" )
            NumSentences  = len( Sentences )
            FontHeight    = MyFont.size( '|' )[1]
            TextboxHeight = NumSentences * FontHeight

            for i in range( NumSentences ):

                BottomLabel      = MyFont.render( Sentences[i], 1, WHITE )
                BottomLabelPos_x = (screen.get_width() - MyFont.size( Sentences[i] )[0]) / 2
                BottomLabelPos_y = (CanvasPos_y - TextboxHeight) / 2 + CanvasPos_y + CanvasSize[1] + FontHeight * i

                screen.blit( BottomLabel, (BottomLabelPos_x, BottomLabelPos_y) )
                pygame.display.flip()

            if PLAYER_TYPE == 'human':

                pygame.event.set_blocked( None )
                pygame.event.set_allowed( [pygame.MOUSEBUTTONDOWN] )
                pygame.event.clear()   # clear the events queue
                LeftMouseClicked = False
                while not LeftMouseClicked:
                    if pygame.event.peek():   pass
                    else:   pygame.event.pump(); continue

                    Event = pygame.event.poll()   # Get (pop) a single event from the queue

                    if Event.type not in [pygame.MOUSEBUTTONDOWN]:
                        #print( "ERROR: We should not have had an invalid event type creep into here ... how did we get to this?" )
                        #print( "Dropping to a pdb terminal" )
                        #import pdb; pdb.set_trace()
                        pass

                    if Event.type == pygame.MOUSEBUTTONDOWN and Event.button == 1: LeftMouseClicked = True

                pygame.event.set_allowed( None )   # remove restrictions to event types.
                return

            else:
                # Fake some time wait on the feedback screen.
                val = random.randrange(5,10)
                if ((LOBBY_PLAYERS > 1 or PLAYER_TYPE == 'human' or SHOW_PYGAME_IF_NONHUMAN_PLAYER) and AGENT_WAIT): pygame.time.wait(val*1000)

    else:
        pass   # invisible, non-human player; disable pygame functions.




def get_user_input( Prompt_str, validation_function ) -> str :
    """
    Prompts user with a question within pygame, and collects the response
    """

  # Initialise important pygame elements
    MyFont = pygame.font.SysFont( FONT, 28 )
    reset_screen()

  # Define some helpful utility functions (lambdas) for consistency
    get_x_coord = lambda Str   : (screen.get_width() - MyFont.size( Str )[0]) / 2
    get_y_coord = lambda offset: screen.get_height() / 2 + MyFont.size('Arbitrary Text')[1] * offset

    def render_string( Str, offset, colour ):

        Str = Str.split('\n')

        for i in range( len( Str ) ):
            pgLabel = MyFont.render( Str[i], 1, colour )
            x_coord = get_x_coord( Str[i] )
            y_coord = get_y_coord( offset + i )

            screen.blit( pgLabel, (x_coord, y_coord) )

        pygame.display.update()


  # Show initial prompt on screen
    render_string( Prompt_str, offset = -1, colour = WHITE )

  # Process user's response
    Response_str = ""
    pygame.event.clear()

    while Response_str == "":

      # Get user's reponse
        while True:
            if pygame.event.peek():   # check if events are present in the event queue
                Event = pygame.event.poll()   # get single event from queue

                if Event.type == pygame.KEYUP:
                    if pygame.key.name( Event.key ) == 'return':
                        break
                    elif pygame.key.name( Event.key ) not in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', 'm', 'f', 'l', 'r', ',']:
                        pass
                    else:
                        Response_str += pygame.key.name( Event.key ).upper()

                        reset_screen()
                        render_string( Prompt_str, offset = -1, colour = WHITE )
                        render_string( Response_str, offset = 1 + Prompt_str.count('\n'), colour = YELLOW )

            else:
                pygame.event.pump()   # ensure lack of response does not freeze the app

      # Validate response before exiting
        if validation_function( Response_str ):
            pass
        else:
            Error_str = f"Input provided ({Response_str}) is invalid; please try again!"

            reset_screen()
            render_string( Prompt_str, offset = -1, colour = WHITE )
            render_string( Error_str , offset = 2 + Prompt_str.count('\n') , colour = RED )

            Response_str = ""

    return Response_str




def ask_player_to_rate_colleagues_using_sliders( InitialTrustRatings ):

    assert isinstance( InitialTrustRatings, list )
    NumOtherPlayers = len( InitialTrustRatings )

  # If not an interactive player, return a standard result.
    if PLAYER_TYPE != 'human' or NumOtherPlayers < 1:
        return numpy.full( (1, NumOtherPlayers), 4 )


  # Continue as normal for human players.
    global screen
    reset_screen()

    Submitted     = False
    SliderValues  = InitialTrustRatings[:]   # initialised here, but accessed/updated by subfunctions as a nonlocal variable
    FontSize      = 32

    KnobLocations  = None   # A list of rectangle coordinates, used for mouse-event detection
    ButtonLocation = None   # A tuple of rectangle coordinates, used for button-event detection



    def run():

        nonlocal Submitted

        blit_top_message()
        blit_avatars()

        blit_sliders()         # Note: accesses and updates the nonlocal SliderValues object
        blit_submit_button()

        pygame.display.update()

        process_click_events()   # Note: SliderValues expected to have changed after this function call
#
#        # XXX may need to hide mouse cursor here (also may need to make it visible beforehand)
#

        TrustRatings = numpy.array( SliderValues ).reshape( (1, -1) )
        return TrustRatings



    def blit_top_message():
        Message_strlist = [ "Please use the sliders to rate how much you trust",
                            "the decisions of each of your fellow team members."  ]

        MyFont = pygame.font.SysFont( FONT, int( FontSize / 1.5 ) )

        for i in range( len( Message_strlist ) ):
            Line_str  = Message_strlist[ i ]
            XCoord    = (screen.get_size()[ 0 ] - MyFont.size( Line_str )[ 0 ]) / 2
            YCoord    = 25 + i * MyFont.size( Line_str )[ 1 ]
            Line_surf = MyFont.render( Line_str, True, LIGHTBLUE )   # True is for 'antialias'
            screen.blit( Line_surf, (XCoord, YCoord) )



    def blit_avatars():

      # Proceed to place city markers and related info
        for i in range( NumOtherPlayers ):

          # XXX beautiful MAGIC numbers, that's some high quality code right here
            XCoord = 25 if i < 5 else 25 + int( screen.get_size()[ 0 ] / 2 )
            YCoord = 140 + (i % 5) * 135

          # Draw Avatar
            Avatar         = Avatar_pgsurfaces[ i + 1 ]   # "i+1" because avatar index 0 is the 'you' player, and
                                                                # here we're only dealing with 'other' players.
            AvatarWidth    = Avatar.get_size()[ 0 ]
            AvatarHeight   = Avatar.get_size()[ 1 ]

            screen.blit( Avatar , (XCoord, YCoord - AvatarHeight / 2) )




    def get_slider_rect( SliderIndex ):

      # Estimate width of 'avatar' to inform the positioning of the slider.
      # XXX: This only works here because we ensured our avatars are of the same size (64x64 to be exact)
        AvatarWidth = Avatar_pgsurfaces[ 0 ].get_size()[ 0 ]

      # XXX beautiful MAGIC numbers, that's some high quality code right here
        SliderXCoord    = 50 if SliderIndex < 5 else 50 + int( screen.get_size()[ 0 ] / 2 )
        SliderXCoord    = SliderXCoord + AvatarWidth

        SliderYCoord    = 140 + (SliderIndex % 5) * 135
        SliderBarHeight = 10   # XXX Beautiful magic numbers.
        SliderBarWidth  = screen.get_size()[ 0 ] / 2 - SliderXCoord if SliderIndex < 5 else screen.getsize()[ 0 ] - SliderXCoord

        return SliderXCoord, SliderYCoord, SliderBarWidth, SliderBarHeight




    def blit_slider( SliderIndex, KnobCoords  = None, KnobPressed = False ):

        SliderValue = SliderValues[ SliderIndex ]

      # Choose an appropriate colour for the slider bar (going from green to red as it drops from 1 to 0)
        SliderColour = SliderValue / TRUST_MAX   # TRUST_MAX is the max value, denoting full trust
        MaxColour    = max( SliderColour, 1 - SliderColour )
        SliderColour = (int( 255 * (1 - SliderColour) / MaxColour ), int( 255 * SliderColour / MaxColour ), 0)

      # Get Slider rect
        SliderXCoord, SliderYCoord, SliderBarWidth, SliderBarHeight = get_slider_rect( SliderIndex )

      # Get knob details
        KnobRadius = 12

        if KnobCoords is None:
            KnobXCoord = int( SliderXCoord + SliderBarWidth * SliderValue / TRUST_MAX )
            KnobYCoord = int( SliderYCoord + SliderBarHeight / 2 )
        else:
            KnobXCoord, KnobYCoord = KnobCoords

      # Estimate text value above knob
        TextValue  = f"{SliderValue}%"
        MyFont     = pygame.font.SysFont( FONT, 20)
        TextXCoord = KnobXCoord - MyFont.size( TextValue )[ 0 ] / 2
        TextXCoord = max( SliderXCoord, TextXCoord )
        TextXCoord = min( TextXCoord, SliderXCoord + SliderBarWidth  - MyFont.size( TextValue )[ 0 ] )
        TextYCoord = KnobYCoord - KnobRadius - MyFont.size( TextValue )[ 1 ] - 16

      # Update Knob Location (i.e. its enclosing rectangle)
        KnobLocations[ SliderIndex ] = (KnobXCoord - KnobRadius, KnobYCoord - KnobRadius, KnobRadius * 2, KnobRadius * 2)

      # Perform actual draws
        pygame.draw.rect( screen, BACKGROUND_COLOUR, (SliderXCoord - KnobRadius - 2, TextYCoord, SliderBarWidth + KnobRadius * 2 + 4, SliderYCoord - TextYCoord + KnobRadius * 2) )
        pygame.draw.rect( screen, SliderColour     , (SliderXCoord, SliderYCoord, SliderBarWidth, SliderBarHeight          ) )
        pygame.draw.circle( screen, BLACK    , (KnobXCoord, KnobYCoord), KnobRadius + 2 )
        if KnobPressed:   pygame.draw.circle( screen, WHITE,      (KnobXCoord, KnobYCoord), KnobRadius     )
        else          :   pygame.draw.circle( screen, LIGHTGRAY, (KnobXCoord, KnobYCoord), KnobRadius     )
        screen.blit( MyFont.render( TextValue, True, YELLOW ), (TextXCoord, TextYCoord) )





    def blit_sliders():

        nonlocal SliderValues
        nonlocal KnobLocations

        if KnobLocations == None:   KnobLocations = [ (0,0,0,0) ] * NumOtherPlayers

        for i in range( NumOtherPlayers ):   blit_slider( i )




    def blit_submit_button():

        nonlocal ButtonLocation
        if ButtonLocation == None:   ButtonLocation = (0,0,0,0)

        MyFont = pygame.font.SysFont( FONT, 20 )

        Message_strlist = [ "Click this button to submit",
                            "once you've finished rating" ]
        MessageWidth  = max( MyFont.size( i )[ 0 ] for i in Message_strlist )
        MessageHeight = sum( MyFont.size( i )[ 1 ] for i in Message_strlist )

        ButtonWidth  = MessageWidth  + 10 * 2
        ButtonHeight = MessageHeight + 5 * 2
        ButtonXCoord = screen.get_size()[ 0 ] - ButtonWidth  - 15
        ButtonYCoord = screen.get_size()[ 1 ] - ButtonHeight - 10

        pygame.draw.rect( screen, BLACK    , (ButtonXCoord+5, ButtonYCoord+5, ButtonWidth, ButtonHeight) )
        pygame.draw.rect( screen, LIGHTGRAY, (ButtonXCoord  , ButtonYCoord  , ButtonWidth, ButtonHeight) )

        for i in range( len( Message_strlist ) ):
            Line_str   = Message_strlist[ i ]
            TextXCoord = ButtonXCoord + 10
            TextYCoord = ButtonYCoord + 5 + sum( MyFont.size( i )[ 1 ] for i in Message_strlist[ : i ] )
            Line_surf = MyFont.render( Line_str, True, BLACK )   # True is for 'antialias'
            screen.blit( Line_surf, (TextXCoord, TextYCoord) )


      # Updated Button Location
        ButtonLocation = (ButtonXCoord, ButtonYCoord, ButtonWidth, ButtonHeight)




    def isInsideRect( Point : tuple( (float,) * 2 ),
                      Rect  : tuple( (float,) * 4 )
                    ) -> bool :

        assert isinstance( Point, list ) or isinstance( Point, tuple )
        assert len( Point ) == 2
        assert isinstance( Rect, list ) or isinstance( Rect, tuple )
        assert len( Rect ) == 4

        px, py         = Point
        rx, ry, rw, rh = Rect

        return (rx <= px <= rx + rw) and (ry <= py <= ry + rh)




    def process_click_events():

        nonlocal Submitted
        nonlocal SliderValues

      # Restrict which event types should be placed on the event queue
        pygame.event.set_blocked( None )
        pygame.event.set_allowed( [pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP] )

        pygame.event.clear()   # clear the events queue

        while not Submitted:

            if pygame.event.peek():
                pass                  # proceed to process event
            else:
                pygame.event.pump()   # prevent pygame engine from freezing during un-event-ful frames
                continue

            Event = pygame.event.poll()   # Get (pop) a single event from the queue

            if Event.type not in [ pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP ]:
                print( "ERROR: We should not have had an invalid event type creep into here ... how did we get to this?" )
                print( "Dropping to a pdb terminal" )
                #import pdb; pdb.set_trace()
                pass

            if Event.type == pygame.MOUSEBUTTONDOWN and Event.button == 1:   # left mouse button pressed

              # Check if we are inside a region of interest (i.e. an interactable element)
                ROIActivations = [ isInsideRect( Event.pos, Rect ) for Rect in KnobLocations + [ ButtonLocation ] ]

                if any( ROIActivations ):

                    assert sum( ROIActivations ) == 1, "It should not be possible to be inside more than one interactive elements on screen at the same time!"

                    if ROIActivations[ -1 ]:   # The ROI triggered was the submission button

                      # Wait for a release event, and detect if we're still inside the button area; otherwise silently ignore event
                        while Event.type != pygame.MOUSEBUTTONUP:
                            if pygame.event.peek():   pass
                            else                  : pygame.event.pump(); continue
                            Event = pygame.event.poll()

                        if isInsideRect( Event.pos, ButtonLocation ):   Submitted = True; break
                        else                                        :   continue

                    else:   # we have intercepted a click inside one of the slider knobs

                        SliderIndex     = ROIActivations.index( True )
                        SliderValue     = SliderValues[ SliderIndex ]
                        SliderXCoord, SliderYCoord, SliderBarWidth, SliderBarHeight = get_slider_rect( SliderIndex )
                        KnobRectXCoord, KnobRectYCoord, KnobDiameter, _ = KnobLocations[ SliderIndex ]
                        KnobRadius = round( KnobDiameter / 2 )
                        KnobCentreXCoord = int( KnobRectXCoord + KnobRadius )
                        KnobCentreYCoord = int( KnobRectYCoord + KnobRadius )

                        blit_slider( SliderIndex, (KnobCentreXCoord, KnobCentreYCoord), KnobPressed = True )
                        pygame.display.update()

                      # Process all movement events appropriately, until the mouse button is released
                        RefreshRate   = MOVEMENT_REFRESH_RATE * 2   # XXX needed to make this a bit faster than the main game refresh rate
                        MovementFrame = 0

                        while Event.type != pygame.MOUSEBUTTONUP:

                            if pygame.event.peek():   pass
                            else                  : pygame.event.pump(); continue
                            Event = pygame.event.poll()

                            if Event.type == pygame.MOUSEMOTION:

                                if SliderXCoord <= Event.pos[0] <= SliderXCoord + SliderBarWidth:
                                    KnobCentreXCoord += Event.rel[0]
                                KnobCentreXCoord = max( SliderXCoord, KnobCentreXCoord )
                                KnobCentreXCoord = min( KnobCentreXCoord, SliderXCoord + SliderBarWidth )
                                KnobCentreXCoord = int( KnobCentreXCoord )

                                blit_slider( SliderIndex, (KnobCentreXCoord, KnobCentreYCoord), KnobPressed = True )

                                SliderValues  [ SliderIndex ] = round( TRUST_MAX * (KnobCentreXCoord - SliderXCoord) / SliderBarWidth )

                                if not MovementFrame % RefreshRate:   pygame.display.update()

                                MovementFrame += 1


                      # Upon releasing mouse button, shift knob to nearest 'integer' position (with 'unpressed' colour).
                        KnobCentreXCoord = int( SliderXCoord + SliderBarWidth * SliderValues[ SliderIndex ] / TRUST_MAX )
                        KnobCentreYCoord = int( SliderYCoord + SliderBarHeight / 2 )
                        KnobLocations [ SliderIndex ] = int( KnobCentreXCoord - KnobRadius ), int( KnobCentreYCoord - KnobRadius ), KnobDiameter, KnobDiameter
                        blit_slider( SliderIndex, (KnobCentreXCoord, KnobCentreYCoord) )
                        pygame.display.update()

                        continue


                else:   # left button was pressed at a non-interactive location

                  # Ignore all events until mouse button is released
                    while Event.type != pygame.MOUSEBUTTONUP:
                        if pygame.event.peek():   pass
                        else                  : pygame.event.pump(); continue
                        Event = pygame.event.poll()

                    continue
            #
            ### END OF 'if mouse button pressed'

        #
        ### END OF 'while not Submitted:'

        pygame.event.set_allowed( None )   # remove restrictions to event types.


        return None

        #
        ### END OF 'def process_click_events()' local function


    TrustRatings = run()
    pygame.display.update()


    return TrustRatings




def gracefully_quit_pygame():
    pygame.display.quit()
    pygame.quit()
