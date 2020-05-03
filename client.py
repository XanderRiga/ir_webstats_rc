#!/usr/bin/python
""" iRWebStats class. Check examples.py for example usage. """
__author__ = "Jeyson Molina"
__email__ = "jjmc82@gmail.com"
__version__ = "1.3"

import urllib
import urllib.parse
encode = urllib.parse.urlencode
from io import StringIO

import requests
import datetime
import csv
import time
import re
import ast

from .util import *
# from .constants import constants as ct

# _*_ coding: utf_8 _*_

ALL = -1
NUM_ENTRIES = 25  # Entries per page. This is the ammount set in iRacing site. We shouldn't increase it.
WAIT_TIME = 0.3  # Minimum time in seconds between two consecutive requests to iRacing site (we don't want to flood/abuse the service). I'm not sure about the minimum value for this, I'll have to ask a dev.

IRATING_OVAL_CHART = 1
IRATING_ROAD_CHART = 2

RACE_TYPE_OVAL = 1
RACE_TYPE_ROAD = 2

LIC_ROOKIE = 1
LIC_D = 2
LIC_C = 3
LIC_B = 4
LIC_A = 5
LIC_PRO = 6
LIC_PRO_WC = 7

SORT_IRATING = 'irating'
SORT_TIME = 'start_time'
SORT_POINTS = 'points'
ORDER_DESC = 'desc'
ORDER_ASC = 'asc'

# OTHER
EVENT_RACE = 1
EVENT_QUALY = 2
EVENT_PRACTICE = 3
EVENT_TTRIAL = 4

EVENT_OFFICIAL = 6
EVENT_UNOFFICIAL = 7

# INCIDENT FLAGS
# these are used in the laps data
FLAG_PITTED = 2
FLAG_OFF_TRACK = 4
FLAG_BLACK_FLAG = 8
FLAG_CAR_RESET = 16
FLAG_CONTACT = 32
FLAG_CAR_CONTACT = 64
FLAG_LOST_CONTROL = 128
FLAG_DISCONTINUITY = 256
FLAG_INTERPOLATED_CROSSING = 512
FLAG_CLOCK_SMASH = 1024
FLAG_TOW = 2048

INC_FLAGS = {
    0: "clean",
    2: "pitted",
    4: "off track",
    8: "black flag",
    16: "car reset",
    32: "contact",
    64: "car contact",
    128: "lost control",
    256: "discontinuity",
    512: "interpolated crossing",
    1024: "clock smash",
    2048: "tow"
}

# URLS
URL_IRACING_LOGIN = 'https://members.iracing.com/membersite/login.jsp'
URL_IRACING_LOGIN2 = 'https://members.iracing.com/membersite/Login'
URL_IRACING_HOME = 'https://members.iracing.com/membersite/member/Home.do'
URL_CURRENT_SERIES = 'https://members.iracing.com/membersite/member/Series.do'
URL_STATS_CHART = 'https://members.iracing.com/memberstats/member/GetChartData?custId=%s&catId=%s&chartType=1'
URL_DRIVER_COUNTS = 'https://members.iracing.com/membersite/member/GetDriverCounts'
URL_CAREER_STATS = 'https://members.iracing.com/memberstats/member/GetCareerStats?custid=%s'
URL_YEARLY_STATS = 'https://members.iracing.com/memberstats/member/GetYearlyStats?custid=%s'
URL_CARS_DRIVEN = 'https://members.iracing.com/memberstats/member/GetCarsDriven?custid=%s'
URL_PERSONAL_BEST = 'https://members.iracing.com/memberstats/member/GetPersonalBests?carid=%s&custid=%s'
URL_DRIVER_STATUS = 'https://members.iracing.com/membersite/member/GetDriverStatus?%s'
URL_DRIVER_STATS = 'https://members.iracing.com/memberstats/member/GetDriverStats'
URL_LASTRACE_STATS = 'https://members.iracing.com/memberstats/member/GetLastRacesStats?custid=%s'
URL_RESULTS_ARCHIVE = 'https://members.iracing.com/memberstats/member/GetResults'
URL_SEASON_STANDINGS = 'https://members.iracing.com/memberstats/member/GetSeasonStandings'
URL_SEASON_STANDINGS2 = 'https://members.iracing.com/membersite/member/statsseries.jsp'
URL_HOSTED_RESULTS = 'https://members.iracing.com/memberstats/member/GetPrivateSessionResults'
URL_SELECT_SERIES = 'https://members.iracing.com/membersite/member/SelectSeries.do?&season=%s&view=undefined&nocache=%s'
URL_SESSION_TIMES = 'https://members.iracing.com/membersite/member/GetSessionTimes'  # T-m-d
URL_SERIES_RACERESULTS = 'https://members.iracing.com/memberstats/member/GetSeriesRaceResults'

URL_GET_EVENTRESULTS = 'https://members.iracing.com/membersite/member/GetEventResultsAsCSV?subsessionid=%s&simsesnum=%s&includeSummary=1'  # simsesnum 0 race, -1 qualy or practice, -2 practice

URL_GET_LAPS_SINGLE = 'https://members.iracing.com/membersite/member/GetLaps?&subsessionid=%s&groupid=%s&simsessnum=%s'
URL_GET_LAPS_ALL = 'https://members.iracing.com/membersite/member/GetLapChart?&subsessionid=%s&carclassid=-1'

URL_GET_PASTSERIES = 'https://members.iracing.com/membersite/member/PreviousSeasons.do'

URL_GET_WORLDRECORD = 'https://members.iracing.com/memberstats/member/GetWorldRecords?seasonyear=%s&seasonquarter=%s' \
                      '&carid=%s&trackid=%s&custid=%s&format=json&upperbound=1 '

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.52 '
                  'Safari/537.17 '
    , 'Referer': 'https://members.iracing.com/membersite/login.jsp', 'Connection': 'keep-alive',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3', 'Cache-Control': 'max-age=0', 'Host': 'members.iracing.com',
    'Accept-Encoding': 'gzip,deflate,sdch', 'Origin': 'members.iracing.com', 'Accept-Language': 'en-US,en;q=0.8'}

# LOCATIONS
LOC_ALL = 'null'
LOC_AFGHANISTAN = 'AF'
LOC_ALAND_ISLANDS = 'AX'
LOC_ALBANIA = 'AL'
LOC_ALGERIA = 'DZ'
LOC_AMERICAN_SAMOA = 'AS'
LOC_ANDORRA = 'AD'
LOC_ANGOLA = 'AO'
LOC_ANGUILLA = 'AI'
LOC_ANTARCTICA = 'AQ'
LOC_ANTIGUA_AND_BARBUDA = 'AG'
LOC_ARGENTINA = 'AR'
LOC_ARMENIA = 'AM'
LOC_ARUBA = 'AW'
LOC_AUSTRALIA = 'AU'
LOC_AUSTRIA = 'AT'
LOC_AZERBAIJAN = 'AZ'
LOC_BAHAMAS = 'BS'
LOC_BAHRAIN = 'BH'
LOC_BANGLADESH = 'BD'
LOC_BARBADOS = 'BB'
LOC_BELARUS = 'BY'
LOC_BELGIUM = 'BE'
LOC_BELIZE = 'BZ'
LOC_BENIN = 'BJ'
LOC_BERMUDA = 'BM'
LOC_BHUTAN = 'BT'
LOC_BOLIVIA_PLURINATIONAL_STATE_OF = 'BO'
LOC_BOSNIA_AND_HERZEGOVINA = 'BA'
LOC_BOTSWANA = 'BW'
LOC_BOUVET_ISLAND = 'BV'
LOC_BRAZIL = 'BR'
LOC_BRITISH_INDIAN_OCEAN_TERRITORY = 'IO'
LOC_BRUNEI_DARUSSALAM = 'BN'
LOC_BULGARIA = 'BG'
LOC_BURKINA_FASO = 'BF'
LOC_BURUNDI = 'BI'
LOC_CAMBODIA = 'KH'
LOC_CAMEROON = 'CM'
LOC_CANADA = 'CA'
LOC_CAPE_VERDE = 'CV'
LOC_CAYMAN_ISLANDS = 'KY'
LOC_CENTRAL_AFRICAN_REPUBLIC = 'CF'
LOC_CHAD = 'TD'
LOC_CHILE = 'CL'
LOC_CHINA = 'CN'
LOC_CHRISTMAS_ISLAND = 'CX'
LOC_COCOS_KEELING_ISLANDS = 'CC'
LOC_COLOMBIA = 'CO'
LOC_COMOROS = 'KM'
LOC_CONGO = 'CG'
LOC_CONGO_THE_DEMOCRATIC_REPUBLIC_OF_THE = 'CD'
LOC_COOK_ISLANDS = 'CK'
LOC_COSTA_RICA = 'CR'
LOC_COTE_DIVOIRE = 'CI'
LOC_CROATIA = 'HR'
LOC_CUBA = 'CU'
LOC_CYPRUS = 'CY'
LOC_CZECH_REPUBLIC = 'CZ'
LOC_DENMARK = 'DK'
LOC_DJIBOUTI = 'DJ'
LOC_DOMINICA = 'DM'
LOC_DOMINICAN_REPUBLIC = 'DO'
LOC_ECUADOR = 'EC'
LOC_EGYPT = 'EG'
LOC_EL_SALVADOR = 'SV'
LOC_EQUATORIAL_GUINEA = 'GQ'
LOC_ERITREA = 'ER'
LOC_ESTONIA = 'EE'
LOC_ETHIOPIA = 'ET'
LOC_FALKLAND_ISLANDS_MALVINAS = 'FK'
LOC_FAROE_ISLANDS = 'FO'
LOC_FIJI = 'FJ'
LOC_FINLAND = 'FI'
LOC_FRANCE = 'FR'
LOC_FRENCH_GUIANA = 'GF'
LOC_FRENCH_POLYNESIA = 'PF'
LOC_FRENCH_SOUTHERN_TERRITORIES = 'TF'
LOC_GABON = 'GA'
LOC_GAMBIA = 'GM'
LOC_GEORGIA = 'GE'
LOC_GERMANY = 'DE'
LOC_GHANA = 'GH'
LOC_GIBRALTAR = 'GI'
LOC_GREECE = 'GR'
LOC_GREENLAND = 'GL'
LOC_GRENADA = 'GD'
LOC_GUADELOUPE = 'GP'
LOC_GUAM = 'GU'
LOC_GUATEMALA = 'GT'
LOC_GUERNSEY = 'GG'
LOC_GUINEA = 'GN'
LOC_GUINEA_BISSAU = 'GW'
LOC_GUYANA = 'GY'
LOC_HAITI = 'HT'
LOC_HEARD_ISLAND_AND_MCDONALD_ISLANDS = 'HM'
LOC_HOLY_SEE_VATICAN_CITY_STATE = 'VA'
LOC_HONDURAS = 'HN'
LOC_HONG_KONG = 'HK'
LOC_HUNGARY = 'HU'
LOC_ICELAND = 'IS'
LOC_INDIA = 'IN'
LOC_INDONESIA = 'ID'
LOC_IRAN_ISLAMIC_REPUBLIC_OF = 'IR'
LOC_IRAQ = 'IQ'
LOC_IRELAND = 'IE'
LOC_ISLE_OF_MAN = 'IM'
LOC_ISRAEL = 'IL'
LOC_ITALY = 'IT'
LOC_JAMAICA = 'JM'
LOC_JAPAN = 'JP'
LOC_JERSEY = 'JE'
LOC_JORDAN = 'JO'
LOC_KAZAKHSTAN = 'KZ'
LOC_KENYA = 'KE'
LOC_KIRIBATI = 'KI'
LOC_KOREA_DEMOCRATIC_PEOPLES_REPUBLIC_OF = 'KP'
LOC_KOREA_REPUBLIC_OF = 'KR'
LOC_KUWAIT = 'KW'
LOC_KYRGYZSTAN = 'KG'
LOC_LAO_PEOPLES_DEMOCRATIC_REPUBLIC = 'LA'
LOC_LATVIA = 'LV'
LOC_LEBANON = 'LB'
LOC_LESOTHO = 'LS'
LOC_LIBERIA = 'LR'
LOC_LIBYAN_ARAB_JAMAHIRIYA = 'LY'
LOC_LIECHTENSTEIN = 'LI'
LOC_LITHUANIA = 'LT'
LOC_LUXEMBOURG = 'LU'
LOC_MACAO = 'MO'
LOC_MACEDONIA_THE_FORMER_YUGOSLAV_REPUBLIC_OF = 'MK'
LOC_MADAGASCAR = 'MG'
LOC_MALAWI = 'MW'
LOC_MALAYSIA = 'MY'
LOC_MALDIVES = 'MV'
LOC_MALI = 'ML'
LOC_MALTA = 'MT'
LOC_MARSHALL_ISLANDS = 'MH'
LOC_MARTINIQUE = 'MQ'
LOC_MAURITANIA = 'MR'
LOC_MAURITIUS = 'MU'
LOC_MAYOTTE = 'YT'
LOC_MEXICO = 'MX'
LOC_MICRONESIA_FEDERATED_STATES_OF = 'FM'
LOC_MOLDOVA_REPUBLIC_OF = 'MD'
LOC_MONACO = 'MC'
LOC_MONGOLIA = 'MN'
LOC_MONTENEGRO = 'ME'
LOC_MONTSERRAT = 'MS'
LOC_MOROCCO = 'MA'
LOC_MOZAMBIQUE = 'MZ'
LOC_MYANMAR = 'MM'
LOC_NAMIBIA = 'NA'
LOC_NAURU = 'NR'
LOC_NEPAL = 'NP'
LOC_NETHERLANDS = 'NL'
LOC_NETHERLANDS_ANTILLES = 'AN'
LOC_NEW_CALEDONIA = 'NC'
LOC_NEW_ZEALAND = 'NZ'
LOC_NICARAGUA = 'NI'
LOC_NIGER = 'NE'
LOC_NIGERIA = 'NG'
LOC_NIUE = 'NU'
LOC_NORFOLK_ISLAND = 'NF'
LOC_NORTHERN_MARIANA_ISLANDS = 'MP'
LOC_NORWAY = 'NO'
LOC_OMAN = 'OM'
LOC_PAKISTAN = 'PK'
LOC_PALAU = 'PW'
LOC_PALESTINIAN_TERRITORY_OCCUPIED = 'PS'
LOC_PANAMA = 'PA'
LOC_PAPUA_NEW_GUINEA = 'PG'
LOC_PARAGUAY = 'PY'
LOC_PERU = 'PE'
LOC_PHILIPPINES = 'PH'
LOC_PITCAIRN = 'PN'
LOC_POLAND = 'PL'
LOC_PORTUGAL = 'PT'
LOC_PUERTO_RICO = 'PR'
LOC_QATAR = 'QA'
LOC_REUNION = 'RE'
LOC_ROMANIA = 'RO'
LOC_RUSSIAN_FEDERATION = 'RU'
LOC_RWANDA = 'RW'
LOC_SAINT_BARTHELEMY = 'BL'
LOC_SAINT_HELENA_ASCENSION_AND_TRISTAN_DA_CUNHA = 'SH'
LOC_SAINT_KITTS_AND_NEVIS = 'KN'
LOC_SAINT_LUCIA = 'LC'
LOC_SAINT_MARTIN_FRENCH_PART = 'MF'
LOC_SAINT_PIERRE_AND_MIQUELON = 'PM'
LOC_SAINT_VINCENT_AND_THE_GRENADINES = 'VC'
LOC_SAMOA = 'WS'
LOC_SAN_MARINO = 'SM'
LOC_SAO_TOME_AND_PRINCIPE = 'ST'
LOC_SAUDI_ARABIA = 'SA'
LOC_SENEGAL = 'SN'
LOC_SERBIA = 'RS'
LOC_SEYCHELLES = 'SC'
LOC_SIERRA_LEONE = 'SL'
LOC_SINGAPORE = 'SG'
LOC_SLOVAKIA = 'SK'
LOC_SLOVENIA = 'SI'
LOC_SOLOMON_ISLANDS = 'SB'
LOC_SOMALIA = 'SO'
LOC_SOUTH_AFRICA = 'ZA'
LOC_SOUTH_GEORGIA_AND_THE_SOUTH_SANDWICH_ISLANDS = 'GS'
LOC_SPAIN = 'ES'
LOC_SRI_LANKA = 'LK'
LOC_SUDAN = 'SD'
LOC_SURINAME = 'SR'
LOC_SVALBARD_AND_JAN_MAYEN = 'SJ'
LOC_SWAZILAND = 'SZ'
LOC_SWEDEN = 'SE'
LOC_SWITZERLAND = 'CH'
LOC_SYRIAN_ARAB_REPUBLIC = 'SY'
LOC_TAIWAN_PROVINCE_OF_CHINA = 'TW'
LOC_TAJIKISTAN = 'TJ'
LOC_TANZANIA_UNITED_REPUBLIC_OF = 'TZ'
LOC_THAILAND = 'TH'
LOC_TIMOR_LESTE = 'TL'
LOC_TOGO = 'TG'
LOC_TOKELAU = 'TK'
LOC_TONGA = 'TO'
LOC_TRINIDAD_AND_TOBAGO = 'TT'
LOC_TUNISIA = 'TN'
LOC_TURKEY = 'TR'
LOC_TURKMENISTAN = 'TM'
LOC_TURKS_AND_CAICOS_ISLANDS = 'TC'
LOC_TUVALU = 'TV'
LOC_UGANDA = 'UG'
LOC_UKRAINE = 'UA'
LOC_UNITED_ARAB_EMIRATES = 'AE'
LOC_UNITED_KINGDOM = 'GB'
LOC_UNITED_STATES = 'US'
LOC_UNITED_STATES_MINOR_OUTLYING_ISLANDS = 'UM'
LOC_URUGUAY = 'UY'
LOC_UZBEKISTAN = 'UZ'
LOC_VANUATU = 'VU'
LOC_VENEZUELA_BOLIVARIAN_REPUBLIC_OF = 'VE'
LOC_VIET_NAM = 'VN'
LOC_VIRGIN_ISLANDS_BRITISH = 'VG'
LOC_VIRGIN_ISLANDS_US = 'VI'
LOC_WALLIS_AND_FUTUNA = 'WF'
LOC_WESTERN_SAHARA = 'EH'
LOC_YEMEN = 'YE'
LOC_ZAMBIA = 'ZM'
LOC_ZIMBABWE = 'ZW'


class iRWebStats:

    """ Use this class to connect to iRacing website and request some stats
        from drivers, races and series. It needs to be logged in the
        iRacing membersite so valid login crendentials (user, password)
        are required. Most  data is returned in JSON format and
        converted to python dicts. """

    def __init__(self, verbose=True):
        self.last_cookie = ''
        self.logged = False
        self.custid = 0
        self.verbose = verbose
        self.TRACKS, self.CARS, self.DIVISION, self.CARCLASS, self.CLUB = {},\
            {}, {}, {}, {}

    def __save_cookie(self):
        """ Saves the current cookie to disk from a successful login to avoid
            future login procedures and save time. A cookie usually last
            at least a couple of hours """

        pprint("Saving cookie for future use", self.verbose)
        o = open('cookie.tmp', 'w')
        o.write(self.last_cookie)
        o.write('\n' + str(self.custid))
        o.close()

    def __load_cookie(self):
        """ Loads a previously saved cookie """
        try:
            o = open('cookie.tmp', 'r')
            self.last_cookie, self.custid = o.read().split('\n')
            o.close()
            return True
        except:
            return False

    def login(self, username='', password='', get_info=False):
        """ Log in to iRacing members site. If there is a valid cookie saved
            then it tries to use it to avoid a new login request. Returns
            True is the login was succesful and stores the customer id
            (custid) of the current login in self.custid. """

        if self.logged:
            return True
        data = {"username": username, "password": password, 'utcoffset': 300,
                'todaysdate': ''}
        try:
            pprint("Loggin in...", self.verbose)
            # Check if there's a previous cookie
            if (self.__load_cookie() and self.__check_cookie()):
                #  If previous cookie is valid
                pprint("Previous cookie valid", self.verbose)
                self.logged = True
                if get_info:
                  # Load iracing info
                  self.__get_irservice_info(self.__req(URL_IRACING_HOME,
                                                       cookie=self.last_cookie))
                # TODO Should we cache this?
                return self.logged
            self.custid = ''
            r = self.__req(URL_IRACING_LOGIN, grab_cookie=True)
            r = self.__req(URL_IRACING_LOGIN2, data,
                           cookie=self.last_cookie, grab_cookie=True)

            if 'irsso_members' in self.last_cookie:
                ind = r.index('js_custid')
                custid = int(r[ind + 11: r.index(';', ind)])
                self.custid = custid
                pprint(("CUSTID", self.custid), self.verbose)
                self.logged = True
                self.__get_irservice_info(r)
                self.__save_cookie()
                pprint("Log in succesful", self.verbose)
            else:
                pprint("Invalid Login (user: %s). Please check your\
                        credentials" % (username), self.verbose)
                self.logged = False

        except Exception as e:
            pprint(("Error on Login Request", e), self.verbose)
            self.logged = False
        return self.logged

    def logout(self):
        self.logged = False  # TODO proper logout

    def __check_cookie(self):
        """ Checks the cookie by testing a request response"""

        r = parse(self.__req(URL_DRIVER_COUNTS, cookie=self.last_cookie))
        if isinstance(r, dict):
            return True
        return False

    def __req(self, url, data=None, cookie=None, grab_cookie=False,
              useget=False):
        """ Creates and sends the HTTP requests to iRacing site """

        # Sleep/wait to avoid flooding the service with requests
        time.sleep(WAIT_TIME)  # 0.3 seconds
        h = HEADERS.copy()
        if cookie is not None:  # Send the cookie
            h['Cookie'] = cookie
        elif len(self.last_cookie):
            h['Cookie'] = self.last_cookie

        if (data is None) or useget:
            resp = requests.get(url, headers=h, params=data)
        else:
            h['Content-Type'] = 'application/x-www-form-urlencoded;\
                    charset=UTF-8'
            resp = requests.post(url, data=data, headers=h)
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

        pprint("Getting iRacing Service info (cars, tracks, etc.)",
               self.verbose)
        items = {"TRACKS":  "TrackListing", "CARS": "CarListing",
                 "CARCLASS":  "CarClassListing", "CLUBS": "ClubListing",
                 "SEASON": "SeasonListing", "DIVISION": "DivisionListing",
                 "YEARANDQUARTER": "YearAndQuarterListing"}
        for i in items:
            str2find = "var " + items[i] + " = extractJSON('"
            try:
                ind1 = resp.index(str2find)
                json_o = resp[ind1 + len(str2find): resp.index("');", ind1)]\
                    .replace('+', ' ')
                o = json.loads(json_o)
                if i not in ("SEASON", "YEARANDQUARTER"):
                    o = {ele['id']: ele for ele in o}
                setattr(self, i, o)  # i.e self.TRACKS = o

            except Exception as e:
                pprint("Error ocurred. Couldn't get {}".format(i), self.verbose)

    def _load_irservice_var(self, varname, resp, appear=1):
        str2find = "var " + varname + " = extractJSON('"
        ind1 = -1
        for _ in range(appear):
            ind1 = resp.index(str2find, ind1+1)
        json_o = resp[ind1 + len(str2find): resp.index("');", ind1)]\
            .replace('+', ' ')
        o = json.loads(json_o)
        if varname not in ("SeasonListing", "YEARANDQUARTER"):
            o = {ele['id']: ele for ele in o}
        return o

    @logged_in
    def iratingchart(self, custid=None, category=IRATING_ROAD_CHART):
        """ Gets the irating data of a driver using its custom id (custid)
            that generates the chart located in the driver's profile. """

        r = self.__req(URL_STATS_CHART % (custid, category),
                       cookie=self.last_cookie)
        return parse(r)

    @logged_in
    def driver_counts(self):
        """ Gets list of connected myracers and notifications. """
        r = self.__req(URL_DRIVER_COUNTS, cookie=self.last_cookie)
        return parse(r)

    @logged_in
    def career_stats(self, custid=None):
        """ Gets career stats (top5, top 10, etc.) of driver (custid)."""
        r = self.__req(URL_CAREER_STATS % (custid),
                       cookie=self.last_cookie)
        return parse(r)

    @logged_in
    def yearly_stats(self, custid=None):
        """ Gets yearly stats (top5, top 10, etc.) of driver (custid)."""
        r = self.__req(URL_YEARLY_STATS % (custid),
                       cookie=self.last_cookie)
        # tofile(r)
        return parse(r)

    @logged_in
    def cars_driven(self, custid=None):
        """ Gets list of cars driven by driver (custid)."""
        r = self.__req(URL_CARS_DRIVEN % (custid),
                       cookie=self.last_cookie)
        # tofile(r)
        return parse(r)

    @logged_in
    def personal_best(self, custid=None, carid=0):
        """ Personal best times of driver (custid) using car
            (carid. check self.CARS) set in official events."""
        r = self.__req(URL_PERSONAL_BEST % (carid, custid),
                       cookie=self.last_cookie)
        return parse(r)

    @logged_in
    def driverdata(self, drivername):
        """ Personal data of driver  using its name in the request
            (i.e drivername="Victor Beltran"). """

        r = self.__req(URL_DRIVER_STATUS % (encode({
            'searchTerms': drivername})), cookie=self.last_cookie)
        # tofile(r)
        return parse(r)

    @logged_in
    def lastrace_stats(self, custid=None):
        """ Gets stats of last races (10 max?) of driver (custid)."""
        r = self.__req(URL_LASTRACE_STATS % (custid),
                       cookie=self.last_cookie)
        return parse(r)

    @logged_in
    def driver_search(self, race_type=RACE_TYPE_ROAD, location=LOC_ALL,
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
            r = self.__req(URL_DRIVER_STATS, data=data,
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
            pprint(("Error fetching driver search data. Error:", e),
                   self.verbose)

        return drivers, total_results

    def test(self, a, b=2, c=3):
        return a, b, c

    @logged_in
    def results_archive(self, custid=None, race_type=RACE_TYPE_ROAD,
                        event_types=ALL, official=ALL,
                        license_level=ALL, car=ALL, track=ALL,
                        series=ALL, season=(2016, 3, ALL),
                        date_range=ALL, page=1, sort=SORT_TIME,
                        order= ORDER_DESC):
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
            tc = lambda s:\
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
        r = self.__req(URL_RESULTS_ARCHIVE, data=data,
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
    def all_seasons(self):
        """ Get All season data available at Series Stats page
        """
        pprint("Getting iRacing Seasons with Stats")
        resp = self.__req(URL_SEASON_STANDINGS2)
        return self._load_irservice_var("SeasonListing", resp)

    @logged_in
    def season_standings(self, season, carclass, club=ALL, raceweek=ALL,
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
        r = self.__req(URL_SEASON_STANDINGS, data=data)
        res = parse(r)
        total_results = res['d'][list(res['m'].keys())[list(res['m'].values()).index('rowcount')]]
        results = res['d']['r']
        header = res['m']
        results = format_results(results, header)

        return results, total_results

    @logged_in
    def hosted_results(self, session_host=None, session_name=None,
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
            tc = lambda s:\
                time.mktime(datetime.datetime.strptime(s, "%Y-%m-%d").
                            timetuple()) * 1000
            data['starttime_lowerbound'] = tc(date_range[0])
            # multiplied by 1000
            data['starttime_upperbound'] = tc(date_range[1])

        r = self.__req(URL_HOSTED_RESULTS, data=data)
        # tofile(r)
        res = parse(r)
        total_results = res['rowcount']
        results = res['rows']  # doesn't need format_results
        return results, total_results

    @logged_in
    def session_times(self, series_season, start, end):
        """ Gets Current and future sessions (qualy, practice, race)
            of series_season """
        r = self.__req(URL_SESSION_TIMES, data={'start': start, 'end': end,
                       'season': series_season}, useget=True)
        return parse(r)

    @logged_in
    def current_series_images(self):
        """ Gets Current series images
        """

        resp = self.__req(URL_CURRENT_SERIES, useget=True)

        series_images = {}
        seriesobjs = re.findall(r'seriesobj=([^;]*);', resp)
        for seriesobj in seriesobjs:
            seasonid = re.findall(r'seasonID:([0-9]*),', seriesobj)[0]
            image = re.findall(r'col_color_img:".+members/member_images/series/([^"]*)"', seriesobj)[0]
            series_images[seasonid] = image

        return series_images

    @logged_in
    def season_race_sessions(self, season, raceweek):
        """ Gets races sessions for season in specified raceweek """

        r = self.__req(URL_SERIES_RACERESULTS, data={'seasonid': season,
                       'raceweek': raceweek})  # TODO no bounds?
        res = parse(r)
        try:
            header = res['m']
            results = res['d']
            results = format_results(results, header)
            return results
        except TypeError:
            print(res)
            return None

    @logged_in
    def event_results(self, subsession, sessnum=0):
        """ Gets the event results (table of positions, times, etc.). The
            event is identified by a subsession id. """

        r = self.__req(URL_GET_EVENTRESULTS % (subsession, sessnum)).encode('utf8').decode('utf-8')
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
    def event_results2(self, subsession, custid):
        """ Get the event results from the web page rather than CSV.
        Required to get ttRating for time trials """

        r = self.__req(URL_GET_EVENTRESULTS2 % (subsession, custid))

        resp = re.sub('\t+',' ',r)
        resp = re.sub('\r\r\n+',' ',resp)
        resp = re.sub('\s+',' ',resp)

        str2find = "var resultOBJ ="
        ind1 = resp.index(str2find)
        ind2 = resp.index("};", ind1) + 1
        resp = resp[ind1 + len(str2find): ind2].replace('+', ' ')

        ttitems = ("custid", "isOfficial", "carID", "avglaptime", "fastestlaptime", "fastestlaptimems", "fastestlapnum", "bestnlapstime", "bestnlapsnum", "lapscomplete", "incidents", "newttRating", "oldttRating", "sr_new", "sr_old", "reasonOutName")
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

    def subsession_results(self, subsession):
        """ Get the results for a time trial event from the web page.
        """

        r = self.__req(URL_GET_SUBSESSRESULTS % (subsession), useget=True)

        out = parse(r)['rows']

        return out

    def event_laps_single(self, subsession, custid, sessnum=0):
        """ Get the lap times for an event from the web page.
        """

        r = self.__req(URL_GET_LAPS_SINGLE % (subsession, custid, sessnum))

        out = parse(r)

        return out

    def event_laps_all(self, subsession):
        """ Get the lap times for an event from the web page.
        """

        r = self.__req(URL_GET_LAPS_ALL % subsession)

        out = parse(r)

        return out

    def best_lap(self, subsessionid, custid):
        """ Get the best lap time for a driver from an event.
        """

        laptime = self.event_laps_single(subsessionid, custid)['drivers'][0]['bestlaptime']

        return laptime

    def world_record(self, seasonyear, seasonquarter, carid, trackid, custid):
        """ Get the world record lap time for certain car in a season.
        """

        r = self.__req(URL_GET_WORLDRECORD % (seasonyear, seasonquarter, carid, trackid, custid))
        res = parse(r)

        header = res['m']
        try:
            results = res['d']['r'][1]
            newr = dict()
            for k, v  in results.items():
                newr[header[k]] = v

            if newr['race'].find("%3A") > -1:
                t = datetime.datetime.strptime(newr['race'], "%M%%3A%S.%f")
                record = (t.minute * 60) + t.second + (t.microsecond / 1000000)
            else:
                record = float(newr['race'])
        except:
            record = None

        return record

if __name__ == '__main__':
    irw = iRWebStats()
    user, passw = ('username', 'password')
    irw.login(user, passw)
    print("Cars Driven", irw.cars_driven())  # example usage
