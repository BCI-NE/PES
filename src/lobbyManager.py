"""
PES - Pandemic Experiment Scenario

This module manages all incoming connections from other players, and is
responsible for communicating data between participants.

Functions defined here:
 • request_data_from_other_players
 • send_data_to_other_players
 • set_up_lobby
 • set_up_UDP_server
"""


# ----------------
# external imports
# ----------------

import fcntl
import numpy
import os
import pickle
import select
import signal
import socket
import struct
import subprocess
import sys
import time

from struct import *
from threading import Timer


# ------------------------------
# internal 'third-party' imports
# ------------------------------

from .. lib import MCast


# ----------------
# internal imports
# ----------------

from . import log_utils

from .. import printinfo
from .. import ANSI
from .. import LOBBY_PLAYERS
from .. import LOBBY_TIMEOUT
from .. import VERBOSE

# -----------------------
# module-global variables
# -----------------------

Port  = ...   # Will be initialised by set_up_lobby
Lobby = ...   # Will be initialised by set_up_lobby   XXX the variable's role is not clear from the name?

InputSocket  = ...   # Will be initialised by set_up_UDP_server
OutputSocket = ...   # Will be initialised by set_up_UDP_server

MySubjectId = ...   # Will be initialised from set_up_lobby (obtained from __main__)

MessageLog_dict = ...   # Will be initialised by set_up_lobby

SocketsLobby    = ...

####################
### Module functions
####################

def set_up_lobby( SubjectId ):
    """
    Listen for other players transmitting their presence (IP/Port/SubjectId).
    Relies on the Multicast module (in ^/lib/MCast.py), which serves as a
    central port (8123) accepting and distributing messages.
    """
    global Port
    global Lobby
    global MySubjectId
    global MessageLog_dict

    MySubjectId = SubjectId

    Lobby    = {}
    reporter = MCast.Receiver()
    noticer  = MCast.Sender()
    start    = time.time()
    Port     = 8000
    Port     = Port + numpy.random.choice( range( 0, 1000 ) )
    Port     = str( Port )

    MessageLog_dict = {}

        # XXX Commented out for now, but left for potential debugging use.
        # Remove completely after satisfied with debugging.
#    if VERBOSE: printinfo( 'lobbyManager: Waiting for all the participants to join...' )

    while True:

        noticer.send( f'{MySubjectId}@{Port}' )

        Data                   = reporter.receive( PrintToTerminal = False )

        ReceivedIP             = Data[ 0 ]

        ( ReceivedSubjectId,
          ReceivedPort_str   ) = Data[ 1 ].decode().split( '@' )

        assert ReceivedPort_str[ -1 :] == '\0'   # confirm data was \0 terminated

        ReceivedPort_int = int( ReceivedPort_str[ : -1 ] )

        # XXX Commented out for now, but left for potential debugging use.
        # Remove completely after satisfied with debugging.
        if VERBOSE: printinfo( f'lobbyManager: Data Received:{ANSI.ORANGE} {Data}' )

        if ReceivedPort_int == int( Port ):   Lobby[ ReceivedIP, ReceivedPort_int ] = MySubjectId
        else                              :   Lobby[ ReceivedIP, ReceivedPort_int ] = ReceivedSubjectId

        if abs( time.time() - start )   >  LOBBY_TIMEOUT:   break
        if len( set( Lobby.values() ) ) == LOBBY_PLAYERS:   break
        if len( set( Lobby.values() ) ) >  LOBBY_PLAYERS:   raise RuntimeError('Lobby has exceeded LOBBY_PLAYERS limit')


    assert len( set( Lobby.values() ) ) == len( list( Lobby.values() ) ), \
           "Player Ids are not unique. Aborting ..."

    assert int((str(MySubjectId)+'  ')[:3]) > 0, \
           "Player Ids must be numbers at least in the first three characters." 

    return


def set_up_TCP_server():
    '''
    Setup a TCP connection peer-to-peer between all the participants.
    The idea is that the Player with the higher PlayerId is the server, the other the client.
    Hence, they connect to each other, and the connection stream is stored in TCPConnections
    '''
    global Port
    global TCPConnections

    assert Port is not ..., "Port has not been initialised yet in module!"

    TCPConnections = {}

    ServerAddress = ( '0.0.0.0', int( Port ) )
    serversock   = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
    serversock.bind( ServerAddress )
    serversock.listen(1)

    
    for Socket, PlayerId in Lobby.items():
        if PlayerId != MySubjectId:
            if int((str(MySubjectId)+'  ')[:3]) > int((str(PlayerId)+'  ')[:3]):
                print(f'Server waiting at {ServerAddress}')
                connection, client_address =  serversock.accept()
                TCPConnections[PlayerId] = connection
            else:
                time.sleep(5)
                print(f'Connecting to {Socket}')
                clientsock = socket.socket( socket.AF_INET, socket.SOCK_STREAM)
                clientsock.connect(Socket)
                TCPConnections[PlayerId] = clientsock
                pass


def send_and_request_stream(TrialId, MyMessage):
    '''
    With TCP this is totally synchronous.
    As the TCP connection is bidirectional, first everybody send their own messages to all the others.
    Hence all the others just pick the message from the connection, guaranteed to be there,
    unless there is some kind of disconnection.  There is no need of timeout.
    (we can check if we need to add keep alive flag)
    '''
    global TCPConnections
    global Lobby
    global OutputSocket
    global MySubjectId

    PlayerIds      = []
    PlayerMessages = []

    PickledMessage = pickle.dumps( (TrialId, MySubjectId, MyMessage) )

    for Socket, PlayerId in Lobby.items():
        if PlayerId != MySubjectId:
            connection = TCPConnections[PlayerId]
            connection.send( PickledMessage )

            #XXX This must be bigger than the biggest message that can be sent !!!!
            Block, _ = connection.recvfrom( 65535 )

            # This is the severity generated by the other players.
            PlayerTrialId, ExternalPlayerId, PlayerMessage = pickle.loads( Block )

            PlayerIds.append( ExternalPlayerId )
            PlayerMessages.append( PlayerMessage )

            assert PlayerTrialId == TrialId, 'Not matching Trial Ids.  Participants are not synchronized and this should not happen with connection oriented networking.'

    return PlayerIds, PlayerMessages



def set_up_UDP_server():
    """
    Set up the UDP server to get the feedback from the other participants
    """
    global Port
    global InputSocket
    global OutputSocket

    assert Port is not ..., "Port has not been initialised yet in module!"


    ServerAddress = ( '0.0.0.0', int( Port ) )
    InputSocket   = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )

    InputSocket.bind( ServerAddress )
    InputSocket.settimeout(1)



def send_data_and_request_data_from_players( TrialId, Message ):
    '''
    This code assumes:
    * TrialIds are numerics
    * TrialIds are different from those that came before and after (this is VERY important because
        messages are repeated in case they are lost and the trial id is used to identify them)
    * PlayersIds are Ids.

    This code is an message exchange checkpoint between all the participants.  It will continue
    until each participant receives a message from all the others, and can confirm to the group that
    all the messages were received.

    '''
    global Lobby
    global OutputSocket
    global InputSocket
    global MySubjectId
    global MessageLog_dict

    PlayerIds      = []   # E.g. "TEST_001" or "001"
    PlayerMessages = []   # 2D numpy arrays of size  'number of players' x 'number of fields (allocations, confidence, severity, etc...). See __main__ for definition.

    HavePlayersSentMeAMessage_dict = {}   # A dictionary whose keys are PlayerIds, and values are booleans.
    HavePlayersConfirmedHavingReceivedAllMessages_dict = {}   # A dictionary whose keys are PlayerIds, and values are booleans

    NumberOfConfirmationRequestsPerformed = 0   # This counter will go up to ten before telling the function to exit.
                                                # The reason we require such a counter is because in the unlikely event
                                                # that for whatever reason there are no more confirmations coming from
                                                # other players, this player will get stuck waiting for them. This
                                                # counter prevents this problem by giving up listening for requests when
                                                # the count hits 10 (hardcoded below).

    for _, PlayerId in Lobby.items():
        HavePlayersSentMeAMessage_dict                     [ PlayerId ] = False
        HavePlayersConfirmedHavingReceivedAllMessages_dict [ PlayerId ] = False

    AllPlayersHaveSentMeAMessage                     = False
    AllPlayersHaveConfirmedHavingReceivedAllMessages = False

    MessageLog_dict[TrialId] = Message 

    while not AllPlayersHaveConfirmedHavingReceivedAllMessages:

        PickledMessage = pickle.dumps( (TrialId,
                                        AllPlayersHaveSentMeAMessage,   # If this is true, this will act as confirmation
                                                                        # that my player has received all necessary
                                                                        # responses from all other players.
                                        MySubjectId,
                                        Message)
                                     )


      # Send my message to all players (including myself)
        for Socket, PlayerId in Lobby.items():

            if PlayerId == MySubjectId:   HavePlayersSentMeAMessage_dict[ PlayerId ] = True
            else                      :   send_data_to_player( PickledMessage, Socket )


      # Receive messages from all players
        for _, PlayerId in Lobby.items():

            try:
                if PlayerId == MySubjectId:
                    pass

                else:
                    PlayerTrialId                            = ...
                    PlayerConfirmedHavingReceivedAllMessages = ...
                    ExternalPlayerId                         = ...
                    PlayerMessage                            = ...

                    PlayerTrialId, PlayerConfirmedHavingReceivedAllMessages, ExternalPlayerId, PlayerMessage = request_data_from_player()

                    print( f"lobbyManager: Processing Trial ID = {TrialId}. Received from {ExternalPlayerId}: PlayerTrialId {PlayerTrialId}, Completed: {PlayerConfirmedHavingReceivedAllMessages}" )


                  # Confirm my player and this external player are sending stuff about the same trial!
                    if int( PlayerTrialId ) == int( TrialId ):

                      # Check if a message has been sent by this player to me yet. If not process it now.
                        if not HavePlayersSentMeAMessage_dict[ ExternalPlayerId ]:
                            PlayerIds     .append( ExternalPlayerId )
                            PlayerMessages.append( PlayerMessage    )

                            HavePlayersSentMeAMessage_dict[ ExternalPlayerId ] = True

                      # Update whether this player has received all their messages.
                        HavePlayersConfirmedHavingReceivedAllMessages_dict[ ExternalPlayerId ] = PlayerConfirmedHavingReceivedAllMessages


                    else:   # If we end up here, it means the players are not coordinated; they are on different trials!!!
                        # If the PlayerTrialId that the other player is asking for is in the log, send it.
                        print( f"{ANSI.RED}lobbyManager: I had to 'cheat' because my TrialId was {TrialId} which was different to other players {PlayerTrialId}!{ANSI.RESET}" )

                        if (PlayerTrialId in MessageLog_dict):
                            Message = MessageLog_dict[PlayerTrialId]
                            PickledMessage = pickle.dumps( (PlayerTrialId, True, MySubjectId, Message) )

                            for Socket, Id in Lobby.items():
                                if Id == ExternalPlayerId:
                                    send_data_to_player(PickledMessage, Socket)
                                    print( f"{ANSI.RED}lobbyManager: Resending previous TrialId {PlayerTrialId}!{ANSI.RESET}" )

                        


            except Exception as E:
              # If we get here, the exception that has happened is most likely the Socket timing out.
                print( "lobbyManager: Exception thrown from 'send_data_and_request_data_from_players':" )
                print( E )
                pass


        print( "lobbyManager: HavePlayersSentMeAMessage_dict = ", HavePlayersSentMeAMessage_dict )

        AllPlayersHaveSentMeAMessage = all( HavePlayersSentMeAMessage_dict[ PlayerId ] for _, PlayerId in Lobby.items() )


        if AllPlayersHaveSentMeAMessage:
             HavePlayersConfirmedHavingReceivedAllMessages_dict[ MySubjectId ] = True


        print( "lobbyManager: HavePlayersConfirmedHavingReceivedAllMessages_dict = ", HavePlayersConfirmedHavingReceivedAllMessages_dict )

        AllPlayersHaveConfirmedHavingReceivedAllMessages = all( HavePlayersConfirmedHavingReceivedAllMessages_dict[ PlayerId ] for _, PlayerId in Lobby.items() )


        # Up to this point, it could be that one party received all the other responses, but missed
        # the chance to send their response, so all the other could be waiting (but surely they already
        # received the original message).
        #
        # Therefore we artificially set AllPlayersHaveConfirmedHavingReceivedAllMessages to True, to exit the infinite
        # while loop

        NumberOfConfirmationRequestsPerformed = NumberOfConfirmationRequestsPerformed + 1


        #if (NumberOfConfirmationRequestsPerformed >= 10 and not AmIAheadOfOthers):

        #    AllPlayersHaveConfirmedHavingReceivedAllMessages = True

        #    print( f"{ANSI.RED}lobbyManager: For TrialId {TrialId} giving up waiting for messages and confirmations !{ANSI.RESET}" )




    return PlayerIds, PlayerMessages


def send_and_request(TrialId, MyMessage):
    '''
    If everything goes well, this will send first the messages to all the others and it will get their
    response.  It will receive all the message, will update the HavePlayersSentMeAMessage dictionary, and 
    will return with the obtained values.
    However, if some message is missing, it will just resend the message, and wait for any response.
    In case a message from other party is received asking for an old TrialId, it is resent by using the 
    MessageLog dictionary.
    
    '''
    global Lobby
    global InputSocket
    global MessageLog_dict

    PlayerIds      = []
    PlayerMessages = []
    HavePlayersSentMeAMessage_dict = {}

    for _, PlayerId in Lobby.items():
        HavePlayersSentMeAMessage_dict[ PlayerId ] = False

    PickledMessage = pickle.dumps( (TrialId, True, MySubjectId, MyMessage) )

    MessageLog_dict[TrialId] = PickledMessage

    for Socket, PlayerId in Lobby.items():
        if PlayerId != MySubjectId:
            send_data_to_player(PickledMessage, Socket)

    AllPlayersHaveSentMeAMessage = False

    while not AllPlayersHaveSentMeAMessage:
        try:
            for _, PlayerId in Lobby.items():
                if PlayerId == MySubjectId:   HavePlayersSentMeAMessage_dict[ MySubjectId ] = True
                else:
                    PlayerTrialId, PlayerAllGood, ExternalPlayerId, PlayerMessage = request_data_from_player()

                    print( f"lobbyManager: Processing Trial ID = {TrialId}. Received from {ExternalPlayerId}: PlayerTrialId {PlayerTrialId}" )


                    if PlayerTrialId == TrialId:
                        if not HavePlayersSentMeAMessage_dict[ExternalPlayerId]:
                            HavePlayersSentMeAMessage_dict[ ExternalPlayerId ] = True
                            PlayerIds.append( ExternalPlayerId )
                            PlayerMessages.append( PlayerMessage )

                    else:
                        if (PlayerTrialId in MessageLog_dict):
                            PickledMessage = MessageLog_dict[PlayerTrialId]
                            send_data_to_this_player(ExternalPlayerId, PickledMessage)
                            print( f"{ANSI.RED}lobbyManager: Resending previous TrialId {PlayerTrialId}!{ANSI.RESET}" )
        
        except Exception as E:
            # If we get here, the exception that has happened is most likely the Socket timing out.
            print( "lobbyManager: Exception thrown from 'send_data_and_request_data_from_players':" )
            print( E )
            pass

        #print( HavePlayersSentMeAMessage_dict )
        AllPlayersHaveSentMeAMessage = all( HavePlayersSentMeAMessage_dict[ PlayerId ] for _, PlayerId in Lobby.items() )

        for Socket, PlayerId in Lobby.items():
            if PlayerId != MySubjectId and not HavePlayersSentMeAMessage_dict[PlayerId]:
                PickledMessage = MessageLog_dict[TrialId]
                send_data_to_player(PickledMessage, Socket)


    return PlayerIds, PlayerMessages


def request_data_from_other_players(TrialId=None):

    global Lobby
    global InputSocket

    PlayerIds      = []
    PlayerMessages = []

    for _, Id in Lobby.items():
        if Id == MySubjectId:   pass
        else:
            PlayerTrialId, PlayerAllGood, PlayerId, PlayerMessage = request_data_from_player()

            PlayerIds.append( PlayerId )
            PlayerMessages.append( PlayerMessage )


    return PlayerIds, PlayerMessages




def request_data_from_player():
    # This should be big enough to be able to fit inside the length of any message that can be
    #   send by this UDP socket.
    Block, _ = InputSocket.recvfrom( 65535 )

    # This is the severity generated by the other players.
    PlayerTrialId, PlayerAllGood, PlayerId, PlayerMessage = pickle.loads( Block )

    log_utils.tee( 'lobbyManager: Received data from', PlayerId, '--',
                           str(PlayerMessage).replace('  ', '').replace( '\n', ',')
                         )

    return PlayerTrialId, PlayerAllGood, PlayerId,PlayerMessage




def peek_data_from_player():
    keepWaiting = True

    PlayerId = ...
    PlayerAllGood = ...
    PlayerMessage = ...

    while keepWaiting:
        try:
            PlayerTrialId, PlayerAllGood, PlayerId, PlayerMessage = request_data_from_player()

            keepWaiting = False
        except:
            pass

    return PlayerTrialId, PlayerAllGood, PlayerId, PlayerMessage

def send_data_to_this_player(ThisPlayerId, PickledMessage):
    for Socket, PlayerId in Lobby.items():
        if PlayerId == ThisPlayerId:
            send_data_to_player(PickledMessage, Socket)


def send_data_to_player(PickledMessage, Socket):
    # @NOTE The rationale behind this is open the socket, send the data, and close it,
    #    forcing a single datagram.
    OutputSocket = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
    log_utils.tee( 'Sending data to IP %s at port %d' % (Socket))
    OutputSocket.sendto( PickledMessage, Socket )
    OutputSocket.close()


def send_data_to_other_players( TrialId, Message ):

    global Lobby
    global OutputSocket
    global MySubjectId

    PickledMessage = pickle.dumps( (TrialId, True, MySubjectId, Message) )

    for Socket, Id in Lobby.items():
        if Id != MySubjectId:
            send_data_to_player(PickledMessage, Socket)

