#!/usr/bin/python
import sys
from ir_webstats_rc import constants as ct
from ir_webstats_rc.client import iRWebStats
from ir_webstats_rc.util import clean

irw = iRWebStats()
irw.login('rob.crouch@gmail.com', 'cYFVPo%^Gs03')
if not irw.logged:
    print (
        "Couldn't log in to iRacing Membersite. Please check your credentials")
    exit()

print(irw.event_results(23743409))
    
