'''
PES - Pandemic Experiment Scenario

This is the eventMarker to handle neurophysiological triggers.
'''

import os
import sys
import getpass
import subprocess

from .. import BIOSEMI_CONNECTED
from .. import PKG_ROOT
from .. import VERBOSE

from .. src import log_utils


if BIOSEMI_CONNECTED:
    # Access the real device with superuser permits.
    username = getpass.getuser()

    #subprocess.call(["sudo","-H", "/bin/chown -R %s /dev/bus/usb/" % username ])

    sys.path.append( os.path.join( PKG_ROOT, 'lib', 'BioSemiUSB', 'out' ) )
    import bsusb

else:
    sys.path.append( os.path.join( PKG_ROOT, 'lib', 'BioSemiUSB', 'src' ) )
    import bsusb2file as bsusb




class EventMarker():
    def __init__(self):
        pass

    def init(self):
        bsusb.init()
        log_utils.tee("eventMarker: Initialising BIOSEMIUSB interface")

    def blockstart(self, CurrentBlockIndex):
        bsusb.send("Experiment3f_Block=" + str(CurrentBlockIndex+1), code=bsusb.SOR)
        log_utils.tee("eventMarker: Sending 'Block Start' trigger")

    def stimulus(self):
        bsusb.send("S", code=bsusb.CTL + bsusb.TRG)
        log_utils.tee("eventMarker: Sending 'Stimulus' trigger")

    def responsehold(self):
        bsusb.send("RH", code=bsusb.CTL + bsusb.TRG)
        log_utils.tee("eventMarker: Sending 'Response Hold' trigger")

    def responserelease(self):
        bsusb.send("RR", code=bsusb.CTL + bsusb.TRG)
        log_utils.tee("eventMarker: Sending 'Response Release' trigger")

    def trialend(self, response, confidence):
        resp_header = 'R=' + str(response) + "Conf=" + \
                str( confidence )
        bsusb.send(resp_header, code=bsusb.CTL + bsusb.TRG)
        log_utils.tee("eventMarker: Sending 'End of trial' trigger")

# There is only one object for the entire module which is initialized on __main__
global evmrk
evmrk = EventMarker()

