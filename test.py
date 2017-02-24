#!/usr/bin/python
import sys
from ir_webstats import constants as ct
from ir_webstats.client import iRWebStats
from ir_webstats.util import clean

if (sys.version_info > (3, 0)):
    user = input('Username: ')
    password = input('Password: ')
else:
    user = raw_input('Username: ')
    password = raw_input('Password: ')

irw = iRWebStats()
irw.login(user, password)
if not irw.logged:
    print (
        "Couldn't log in to iRacing Membersite. Please check your credentials")
    exit()

for i in range(1, 13):
    sof = 0
    sof_sessionid = None
    for res in irw.season_race_sessions(1708, i):
        if res['strengthoffield'] > sof:
           sof = res['strengthoffield']
           sof_sessionid = res['sessionid']
    if not sof_sessionid == None:
        print("SOF for week {}: session {} sof {}".format(i, sof_sessionid, sof))
