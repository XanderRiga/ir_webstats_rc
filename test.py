#!/usr/bin/python
import sys
from ir_webstats_rc import constants as ct
from ir_webstats_rc.client import iRWebStats
from ir_webstats_rc.util import clean

irw = iRWebStats()
irw.login()
if not irw.logged:
    user = input('Username: ')
    password = input('Password: ')
    irw.login(user, password)
    if not irw.logged:
        print (
            "Couldn't log in to iRacing Membersite. Please check your credentials")
        exit()

if irw.logged:
    inc_flags = {
        0: "clean",
        2: "pitted",
        4: "off_track",
        8: "black_flag",
        16: "car_reset",
        32: "contact",
        64: "car_contact",
        128: "lost_control",
        256: "discontinuity",
        512: "interpolated_crossing",
        1024: "clock_smash",
        2048: "tow"
    }
    incs = {
        "clean": 0,
        "pitted": 0,
        "off_track": 0,
        "black_flag": 0,
        "car_reset": 0,
        "contact": 0,
        "car_contact": 0,
        "lost_control": 0,
        "discontinuity": 0,
        "interpolated_crossing": 0,
        "clock_smash": 0,
        "tow": 0,
    }
    for lap in irw.event_laps_all(23346289)["lapdata"]:
        if lap['flags'] == 0:
            incs["clean"] += 1
        for k in inc_flags.keys():
            if lap['flags'] & k:
                incs[inc_flags[k]] += 1

    print(incs)
"""
			if(flags & 2)flags_comments.push("pitted");
			if(flags & 4)flags_comments.push("off track");
			if(flags & 8)flags_comments.push("black flag");
			if(flags & 16)flags_comments.push("car reset");
			if(flags & 32)flags_comments.push("contact");
			if(flags & 64)flags_comments.push("car contact");
			if(flags & 128)flags_comments.push("lost control");

			if(flags & 256)flags_comments.push("discontinuity");
			if(flags & 512)flags_comments.push("interpolated crossing");
			if(flags & 1024)flags_comments.push("clock smash");
			if(flags & 2048)flags_comments.push("tow");
"""
