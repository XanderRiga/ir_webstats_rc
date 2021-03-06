#!/usr/bin/python
""" iRWebStats class. Check examples.py for example usage. """
__author__ = "Jeyson Molina"
__email__ = "jjmc82@gmail.com"
__version__ = "1.3"

import urllib
import urllib.parse

encode = urllib.parse.urlencode
from io import StringIO

import requests_async as requests
import datetime
import csv
import time
import re
import sys

from .util import *
from .responses.series import Series
from .constants import *
from .responses.last_races_stats import LastRacesStats
from .responses.career_stats import CareerStats
from .responses.yearly_stats import YearlyStats


class iRWebStats:
    """ Use this class to connect to iRacing website and request some stats
        from drivers, races and series. It needs to be logged in the
        iRacing membersite so valid login crendentials (user, password)
        are required. Most  data is returned in JSON format and
        converted to python dicts. """

    def __init__(self, username, password, log):
        self.username = username
        self.password = password
        self.last_cookie = ''
        self.logged = False
        self.custid = 0
        self.log = log
        self.TRACKS, self.CARS, self.DIVISION, self.CARCLASS, self.CLUB = {}, \
                                                                          {}, {}, {}, {}
        self.last_request_at = None

    async def __save_cookie(self):
        """ Saves the current cookie to disk from a successful login to avoid
            future login procedures and save time. A cookie usually last
            at least a couple of hours """

        self.log.info("Saving cookie for future use")
        o = open('cookie.tmp', 'w')
        o.write(self.last_cookie)
        o.write('\n' + str(self.custid))
        o.close()

    async def __load_cookie(self):
        """ Loads a previously saved cookie """
        self.log.info('Attempting to load cookie')
        try:
            o = open('cookie.tmp', 'r')
            self.last_cookie, self.custid = o.read().split('\n')
            o.close()
            return True
        except:
            return False

    async def login(self, get_info=False):
        """ Log in to iRacing members site. If there is a valid cookie saved
            then it tries to use it to avoid a new login request. Returns
            True is the login was succesful and stores the customer id
            (custid) of the current login in self.custid. """

        if self.logged:
            return True
        data = {"username": self.username, "password": self.password, 'utcoffset': 300,
                'todaysdate': ''}
        try:
            self.log.info("Loggin in...")
            # Check if there's a previous cookie
            if await self.__load_cookie() and await self.__check_cookie():
                #  If previous cookie is valid
                self.log.info("Previous cookie valid")
                self.logged = True
                if get_info:
                    # Load iracing info
                    self.__get_irservice_info(await self.__req(URL_IRACING_HOME,
                                                         cookie=self.last_cookie))
                # TODO Should we cache this?
                return self.logged
            self.custid = ''
            r = await self.__req(URL_IRACING_LOGIN, grab_cookie=True)
            r = await self.__req(URL_IRACING_LOGIN2, data,
                           cookie=self.last_cookie, grab_cookie=True)

            if 'irsso_members' in self.last_cookie:
                ind = r.index('js_custid')
                custid = int(r[ind + 11: r.index(';', ind)])
                self.custid = custid
                self.log.info("CUSTID: " + str(self.custid))
                self.logged = True
                self.__get_irservice_info(r)
                await self.__save_cookie()
                self.log.info("Log in successful")
            else:
                self.log.info("Invalid Login (user: %s). Please check your credentials" % self.username)
                self.logged = False

        except Exception as e:
            self.log.info("Error on Login Request " + str(e))
            self.logged = False
        return self.logged

    def logout(self):
        self.logged = False  # TODO proper logout

    async def __check_cookie(self):
        """ Checks the cookie by testing a request response"""

        r = parse(await self.__req(URL_DRIVER_COUNTS, cookie=self.last_cookie))
        if isinstance(r, dict):
            return True
        return False

    async def __req(self, url, data=None, cookie=None, grab_cookie=False,
                    useget=False):
        """ Creates and sends the HTTP requests to iRacing site """

        # Sleep/wait to avoid flooding the service with requests
        if self.last_request_at:
            self.log.info('Time difference: ' + str(time.perf_counter() - self.last_request_at))
            while (time.perf_counter() - self.last_request_at) < WAIT_TIME:
                pass

        self.last_request_at = time.perf_counter()
        h = HEADERS.copy()
        if cookie is not None:  # Send the cookie
            h['Cookie'] = cookie
        elif len(self.last_cookie):
            h['Cookie'] = self.last_cookie

        if (data is None) or useget:
            self.log.info('get request being sent')
            self.log.info('url: ' + url)
            resp = await requests.get(url, headers=h, params=data)
        else:
            h['Content-Type'] = 'application/x-www-form-urlencoded;\
                    charset=UTF-8'
            resp = await requests.post(url, data=data, headers=h)
        if 'Set-Cookie' in resp.headers and grab_cookie:
            self.last_cookie = resp.headers['Set-Cookie']
            # Must get irsso_members from another header
            if 'cookie' in resp.request.headers:
                resp_req_cookie = resp.request.headers['cookie']
                self.last_cookie += ';' + resp_req_cookie
        html = resp.text
        return html

    def __get_irservice_info(self, resp):
        """ Gets general information from iracing service like current tracks,
            cars, series, etc. Check self.TRACKS, self.CARS, self.DIVISION
            , self.CARCLASS, self.CLUB. """

        self.log.info("Getting iRacing Service info (cars, tracks, etc.)")
        items = {"TRACKS": "TrackListing", "CARS": "CarListing",
                 "CARCLASS": "CarClassListing", "CLUBS": "ClubListing",
                 "SEASON": "SeasonListing", "DIVISION": "DivisionListing",
                 "YEARANDQUARTER": "YearAndQuarterListing"}
        for i in items:
            str2find = "var " + items[i] + " = extractJSON('"
            try:
                ind1 = resp.index(str2find)
                json_o = resp[ind1 + len(str2find): resp.index("');", ind1)] \
                    .replace('+', ' ')
                o = json.loads(json_o)
                if i not in ("SEASON", "YEARANDQUARTER"):
                    o = {ele['id']: ele for ele in o}
                setattr(self, i, o)  # i.e self.TRACKS = o

            except Exception as e:
                self.log.info("Error ocurred. Couldn't get {}".format(i))

    def _load_irservice_var(self, varname, resp, appear=1):
        str2find = "var " + varname + " = extractJSON('"
        ind1 = -1
        for _ in range(appear):
            ind1 = resp.index(str2find, ind1 + 1)
        json_o = resp[ind1 + len(str2find): resp.index("');", ind1)] \
            .replace('+', ' ')
        o = json.loads(json_o)
        if varname not in ("SeasonListing", "YEARANDQUARTER"):
            o = {ele['id']: ele for ele in o}
        return o

    @logged_in
    async def iratingchart(self, custid=None, category=IRATING_ROAD_CHART, retry=True):
        """ Gets the irating data of a driver using its custom id (custid)
            that generates the chart located in the driver's profile. """

        r = await self.__req(URL_STATS_CHART % (custid, category),
                             cookie=self.last_cookie)
        parsed_iratings = parse(r)

        if parsed_iratings == '' and retry:
            self.log.info('trying to log in again')
            self.logged = False
            await self.login()
            return await self.iratingchart(custid, category, False)
        elif not parsed_iratings:
            return []

        return parsed_iratings

    @logged_in
    async def driver_counts(self):
        """ Gets list of connected myracers and notifications. """
        r = await self.__req(URL_DRIVER_COUNTS, cookie=self.last_cookie)
        return parse(r)

    @logged_in
    async def career_stats(self, custid=None, retry=True):
        """ Gets career stats (top5, top 10, etc.) of driver (custid)."""
        r = await self.__req(URL_CAREER_STATS % (custid),
                             cookie=self.last_cookie)
        career_stats_dict = parse(r)
        if career_stats_dict == '' and retry:
            self.log.info('trying to login again')
            self.logged = False
            await self.login()
            return await self.career_stats(custid, False)
        elif not career_stats_dict:
            return []

        return map(lambda x: CareerStats(x), career_stats_dict)

    @logged_in
    async def yearly_stats(self, custid=None, retry=True):
        """ Gets yearly stats (top5, top 10, etc.) of driver (custid)."""
        r = await self.__req(URL_YEARLY_STATS % (custid),
                             cookie=self.last_cookie)
        yearly_stats_dict = parse(r)
        if yearly_stats_dict == '' and retry:
            self.log.info('trying to log in again')
            self.logged = False
            await self.login()
            return await self.yearly_stats(custid, False)
        elif not yearly_stats_dict:
            return []

        return map(lambda x: YearlyStats(x), yearly_stats_dict)

    @logged_in
    async def cars_driven(self, custid=None):
        """ Gets list of cars driven by driver (custid)."""
        r = await self.__req(URL_CARS_DRIVEN % (custid),
                             cookie=self.last_cookie)
        # tofile(r)
        return parse(r)

    @logged_in
    async def personal_best(self, custid=None, carid=0):
        """ Personal best times of driver (custid) using car
            (carid. check self.CARS) set in official events."""
        r = await self.__req(URL_PERSONAL_BEST % (carid, custid),
                             cookie=self.last_cookie)
        return parse(r)

    @logged_in
    async def driverdata(self, drivername):
        """ Personal data of driver  using its name in the request
            (i.e drivername="Victor Beltran"). """

        r = await self.__req(URL_DRIVER_STATUS % (encode({
            'searchTerms': drivername})), cookie=self.last_cookie)
        # tofile(r)
        return parse(r)

    @logged_in
    async def lastrace_stats(self, custid=None, retry=True):
        """ Gets stats of last races (10 max?) of driver (custid)."""
        r = await self.__req(URL_LASTRACE_STATS % (custid),
                             cookie=self.last_cookie)
        lastrace_dict = parse(r)

        if lastrace_dict == '' and retry:
            self.log.info('attempting to log in and try again')
            self.logged = False
            await self.login()
            return await self.lastrace_stats(custid, False)
        elif not lastrace_dict:
            return []

        return map(lambda x: LastRacesStats(x), lastrace_dict)

    @logged_in
    async def driver_search(self, race_type=RACE_TYPE_ROAD, location=LOC_ALL,
                            license=(LIC_ROOKIE, ALL), irating=(0, ALL),
                            ttrating=(0, ALL), avg_start=(0, ALL),
                            avg_finish=(0, ALL), avg_points=(0, ALL),
                            avg_incs=(0, ALL), active=False,
                            sort=SORT_IRATING, page=1, order=ORDER_DESC):
        """Search drivers using several search fields. A tuple represent a
           range (i.e irating=(1000, 2000) gets drivers with irating
           between 1000 and 2000). Use ALL used in the lower or
           upperbound of a range disables that limit. Returns a tuple
           (results, total_results) so if you want all results you should
           request different pages (using page) until you gather all
           total_results. Each page has 25 (NUM_ENTRIES) results max."""

        lowerbound = NUM_ENTRIES * (page - 1) + 1
        upperbound = lowerbound + NUM_ENTRIES - 1
        search = 'null'
        friend = ALL  # TODO
        studied = ALL  # TODO
        recent = ALL  # TODO

        active = int(active)
        # Data to POST
        data = {'custid': self.custid, 'search': search, 'friend': friend,
                'watched': studied, 'country': location, 'recent': recent,
                'category': race_type, 'classlow': license[0],
                'classhigh': license[1], 'iratinglow': irating[0],
                'iratinghigh': irating[1], 'ttratinglow': ttrating[0],
                'ttratinghigh': ttrating[1], 'avgstartlow': avg_start[0],
                'avgstarthigh': avg_start[1], 'avgfinishlow': avg_finish[0],
                'avgfinishhigh': avg_finish[1], 'avgpointslow': avg_points[0],
                'avgpointshigh': avg_points[1], 'avgincidentslow':
                    avg_incs[0], 'avgincidentshigh': avg_incs[1],
                'lowerbound': lowerbound, 'upperbound': upperbound,
                'sort': sort, 'order': order, 'active': active}

        total_results, drivers = 0, {}

        try:
            r = await self.__req(URL_DRIVER_STATS, data=data,
                                 cookie=self.last_cookie)
            res = parse(r)
            total_results = res['d'][list(res['m'].keys())[list(res['m'].values()).index('rowcount')]]
            custid_id = list(res['m'].keys())[list(res['m'].values()).index('rowcount')]
            header = res['m']
            f = res['d']['r'][0]
            if int(f[custid_id]) == int(self.custid):
                drivers = res['d']['r'][1:]
            else:
                drivers = res['d']['r']
            drivers = format_results(drivers, header)

        except Exception as e:
            self.log.info("Error fetching driver search data. Error: " + str(e))

        return drivers, total_results

    def test(self, a, b=2, c=3):
        return a, b, c

    @logged_in
    async def results_archive(self, custid=None, race_type=RACE_TYPE_ROAD,
                        event_types=ALL, official=ALL,
                        license_level=ALL, car=ALL, track=ALL,
                        series=ALL, season=(2016, 3, ALL),
                        date_range=ALL, page=1, sort=SORT_TIME,
                        order=ORDER_DESC):
        """ Search race results using various fields. Returns a tuple
            (results, total_results) so if you want all results you should
            request different pages (using page). Each page has 25
            (NUM_ENTRIES) results max."""

        format_ = 'json'
        lowerbound = NUM_ENTRIES * (page - 1) + 1
        upperbound = lowerbound + NUM_ENTRIES - 1
        #  TODO carclassid, seriesid in constants
        data = {'format': format_, 'custid': custid, 'seriesid': series,
                'carid': car, 'trackid': track, 'lowerbound': lowerbound,
                'upperbound': upperbound, 'sort': sort, 'order': order,
                'category': race_type, 'showtts': 0, 'showraces': 0,
                'showquals': 0, 'showops': 0, 'showofficial': 0,
                'showunofficial': 0, 'showrookie': 0, 'showclassa': 0,
                'showclassb': 0, 'showclassc': 0, 'showclassd': 0,
                'showpro': 0, 'showprowc': 0, }
        # Events
        ev_vars = {EVENT_RACE: 'showraces', EVENT_QUALY: 'showquals',
                   EVENT_PRACTICE: 'showops', EVENT_TTRIAL: 'showtts'}
        if event_types == ALL:
            event_types = (EVENT_RACE, EVENT_QUALY, EVENT_PRACTICE,
                           EVENT_TTRIAL)

        for v in event_types:
            data[ev_vars[v]] = 1
        # Official, unofficial
        if official == ALL:
            data['showofficial'] = 1
            data['showunoofficial'] = 1
        else:
            if EVENT_UNOFFICIAL in official:
                data['showunofficial'] = 1
            if EVENT_OFFICIAL in official:
                data['showofficial'] = 1

        # Season
        if date_range == ALL:
            data['seasonyear'] = season[0]
            data['seasonquarter'] = season[1]
            if season[2] != ALL:
                data['raceweek'] = season[2]
        else:
            # Date range
            tc = lambda s: \
                time.mktime(datetime.datetime.strptime(s, "%Y-%m-%d").
                            timetuple()) * 1000
            data['starttime_low'] = tc(date_range[0])  # multiplied by 1000
            data['starttime_high'] = tc(date_range[1])

        # License levels
        lic_vars = {LIC_ROOKIE: 'showrookie', LIC_A: 'showclassa',
                    LIC_B: 'showclassb', LIC_C: 'showclassc',
                    LIC_D: 'showclassd', LIC_PRO: 'showpro',
                    LIC_PRO_WC: 'showprowc'}

        if license_level == ALL:
            license_level = (LIC_ROOKIE, LIC_A, LIC_B, LIC_C,
                             LIC_D, LIC_PRO, LIC_PRO_WC)
        for v in license_level:
            data[lic_vars[v]] = 1
        r = await self.__req(URL_RESULTS_ARCHIVE, data=data,
                       cookie=self.last_cookie)
        res = parse(r)
        total_results = res['d'][list(res['m'].keys())[list(res['m'].values()).index('rowcount')]]
        results = []
        if total_results > 0:
            results = res['d']['r']
            header = res['m']
            results = format_results(results, header)

        return results, total_results

    @logged_in
    async def all_seasons(self):
        """ Get All season data available at Series Stats page"""
        self.log.info("Getting iRacing Seasons with Stats")
        resp = await self.__req(URL_SEASON_STANDINGS2)
        seasons_dict_list = self._load_irservice_var("SeasonListing", resp)
        if not seasons_dict_list:
            return []

        return list(map(lambda x: Series(x), seasons_dict_list))

    @logged_in
    async def season_standings(self, season, carclass, club=ALL, raceweek=ALL,
                         division=ALL, sort=SORT_POINTS,
                         order=ORDER_DESC, page=1):
        """ Search season standings using various fields. season, carclass
            and club are ids.  Returns a tuple (results, total_results) so
            if you want all results you should request different pages
            (using page)  until you gather all total_results. Each page has
            25 results max."""

        lowerbound = NUM_ENTRIES * (page - 1) + 1
        upperbound = lowerbound + NUM_ENTRIES - 1

        data = {'sort': sort, 'order': order, 'seasonid': season,
                'carclassid': carclass, 'clubid': club, 'raceweek': raceweek,
                'division': division, 'start': lowerbound, 'end': upperbound}
        r = await self.__req(URL_SEASON_STANDINGS, data=data)
        res = parse(r)
        total_results = res['d'][list(res['m'].keys())[list(res['m'].values()).index('rowcount')]]
        results = res['d']['r']
        header = res['m']
        results = format_results(results, header)

        return results, total_results

    @logged_in
    async def hosted_results(self, session_host=None, session_name=None,
                       date_range=None, sort=SORT_TIME,
                       order=ORDER_DESC, page=1):
        """ Search hosted races results using various fields. Returns a tuple
            (results, total_results) so if you want all results you should
            request different pages (using page) until you gather all
            total_results. Each page has 25 (NUM_ENTRIES) results max."""

        lowerbound = NUM_ENTRIES * (page - 1) + 1
        upperbound = lowerbound + NUM_ENTRIES - 1

        data = {'sort': sort, 'order': order, 'lowerbound': lowerbound,
                'upperbound': upperbound}
        if session_host is not None:
            data['sessionhost'] = session_host
        if session_name is not None:
            data['sessionname'] = session_name

        if date_range is not None:
            # Date range
            tc = lambda s: \
                time.mktime(datetime.datetime.strptime(s, "%Y-%m-%d").
                            timetuple()) * 1000
            data['starttime_lowerbound'] = tc(date_range[0])
            # multiplied by 1000
            data['starttime_upperbound'] = tc(date_range[1])

        r = await self.__req(URL_HOSTED_RESULTS, data=data)
        # tofile(r)
        res = parse(r)
        total_results = res['rowcount']
        results = res['rows']  # doesn't need format_results
        return results, total_results

    @logged_in
    async def session_times(self, series_season, start, end):
        """ Gets Current and future sessions (qualy, practice, race)
            of series_season """
        r = await self.__req(URL_SESSION_TIMES, data={'start': start, 'end': end,
                                                'season': series_season}, useget=True)
        return parse(r)

    @logged_in
    async def current_series_images(self):
        """ Gets Current series images
        """

        resp = await self.__req(URL_CURRENT_SERIES, useget=True)

        series_images = {}
        seriesobjs = re.findall(r'seriesobj=([^;]*);', resp)
        for seriesobj in seriesobjs:
            seasonid = re.findall(r'seasonID:([0-9]*),', seriesobj)[0]
            image = re.findall(r'col_color_img:".+members/member_images/series/([^"]*)"', seriesobj)[0]
            series_images[seasonid] = image

        return series_images

    @logged_in
    async def season_race_sessions(self, season, raceweek):
        """ Gets races sessions for season in specified raceweek """

        r = await self.__req(URL_SERIES_RACERESULTS, data={'seasonid': season,
                                                     'raceweek': raceweek})  # TODO no bounds?
        res = parse(r)
        try:
            header = res['m']
            results = res['d']
            results = format_results(results, header)
            return results
        except TypeError:
            self.log.info(res)
            return None

    @logged_in
    async def event_results(self, subsession, sessnum=0):
        """ Gets the event results (table of positions, times, etc.). The
            event is identified by a subsession id. """

        r = await self.__req(URL_GET_EVENTRESULTS % (subsession, sessnum)).encode('utf8').decode('utf-8')
        data = [x for x in csv.reader(StringIO(r), delimiter=',', quotechar='"')]
        header_res = []
        for header in data[3]:
            header_res.append("".join([c for c in header.lower() if ord(c) > 96 and ord(c) < 123]))
        header_ev = data[0]
        for i in range(4, len(data)):
            for j in range(len(data[i])):
                if data[i][j] == '':
                    data[i][j] = None
                elif data[i][j].isnumeric():
                    data[i][j] = int(data[i][j])
        event_info = dict(list(zip(header_ev, data[1])))
        results = [dict(list(zip(header_res, x))) for x in data[4:]]

        return event_info, results

    @logged_in
    async def event_results2(self, subsession, custid):
        """ Get the event results from the web page rather than CSV.
        Required to get ttRating for time trials """

        r = await self.__req(URL_GET_EVENTRESULTS2 % (subsession, custid))

        resp = re.sub('\t+', ' ', r)
        resp = re.sub('\r\r\n+', ' ', resp)
        resp = re.sub('\s+', ' ', resp)

        str2find = "var resultOBJ ="
        ind1 = resp.index(str2find)
        ind2 = resp.index("};", ind1) + 1
        resp = resp[ind1 + len(str2find): ind2].replace('+', ' ')

        ttitems = ("custid", "isOfficial", "carID", "avglaptime", "fastestlaptime", "fastestlaptimems", "fastestlapnum",
                   "bestnlapstime", "bestnlapsnum", "lapscomplete", "incidents", "newttRating", "oldttRating", "sr_new",
                   "sr_old", "reasonOutName")
        out = ""
        for ttitem in ttitems:
            ind1 = resp.index(ttitem)
            ind2 = resp.index(",", ind1) + 1
            out = out + resp[ind1: ind2]

        out = re.sub(r"{\s*(\w)", r'{"\1', out)
        out = re.sub(r",\s*(\w)", r',"\1', out)
        out = re.sub(r"(\w):", r'\1":', out)
        out = re.sub(r":\"(\d)\":", r':"\1:', out)
        out = re.sub(r"parseFloat\((\"\d\.\d\d\")\)", r'\1', out)

        out = out.strip().rstrip(',')
        out = "{\"" + out + "}"
        out = json.loads(out)

        return out

    async def subsession_results(self, subsession):
        """ Get the results for a time trial event from the web page.
        """

        r = await self.__req(URL_GET_SUBSESSRESULTS % (subsession), useget=True)

        out = parse(r)['rows']

        return out

    async def event_laps_single(self, subsession, custid, sessnum=0):
        """ Get the lap times for an event from the web page.
        """

        r = await self.__req(URL_GET_LAPS_SINGLE % (subsession, custid, sessnum))

        out = parse(r)

        return out

    async def event_laps_all(self, subsession):
        """ Get the lap times for an event from the web page.
        """

        r = await self.__req(URL_GET_LAPS_ALL % subsession)

        out = parse(r)

        return out

    def best_lap(self, subsessionid, custid):
        """ Get the best lap time for a driver from an event.
        """

        laptime = self.event_laps_single(subsessionid, custid)['drivers'][0]['bestlaptime']

        return laptime

    async def world_record(self, seasonyear, seasonquarter, carid, trackid, custid):
        """ Get the world record lap time for certain car in a season.
        """

        r = await self.__req(URL_GET_WORLDRECORD % (seasonyear, seasonquarter, carid, trackid, custid))
        res = parse(r)

        header = res['m']
        try:
            results = res['d']['r'][1]
            newr = dict()
            for k, v in results.items():
                newr[header[k]] = v

            if newr['race'].find("%3A") > -1:
                t = datetime.datetime.strptime(newr['race'], "%M%%3A%S.%f")
                record = (t.minute * 60) + t.second + (t.microsecond / 1000000)
            else:
                record = float(newr['race'])
        except:
            record = None

        return record
